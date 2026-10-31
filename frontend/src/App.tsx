import React, { useEffect, useState } from "react";
import { ResearchDashboard } from "./components/ResearchDashboard";
import { ReportWorkspace } from "./components/ReportWorkspace";
import {
  ActivityEntry,
  AnswerResponse,
  CitationItem,
  DocumentEvidenceData,
  DocumentItem,
  EvaluationData,
  HighlightBox,
  SampleReport,
  TableItem,
} from "./types";

export const App: React.FC = () => {
  // Navigation View Mode: "dashboard" vs "workspace"
  const [currentView, setCurrentView] = useState<"dashboard" | "workspace">("dashboard");

  // Document & Evidence State
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [samples, setSamples] = useState<SampleReport[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [evidenceData, setEvidenceData] = useState<DocumentEvidenceData | null>(null);
  const [suggestions, setSuggestions] = useState<Array<{ label: string; question: string; category?: string; intent?: string }>>([]);

  // QA & Evidence Highlighting State
  const [answerData, setAnswerData] = useState<AnswerResponse | null>(null);
  const [targetPageIndex, setTargetPageIndex] = useState<number>(0);
  const [activeHighlight, setActiveHighlight] = useState<HighlightBox | null>(null);
  const [isLoadingQuestion, setIsLoadingQuestion] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);

  // Benchmarks & Activity Feed
  const [evalData, setEvalData] = useState<EvaluationData | null>(null);
  const [isEvalRunning, setIsEvalRunning] = useState<boolean>(false);
  const [activity, setActivity] = useState<ActivityEntry[]>([
    {
      id: "act_init",
      timestamp: "Today, Session start",
      title: "Report Navigator initialized",
      details: "Evidence verification engine ready for government statistics reports.",
      type: "index",
    },
  ]);

  const addActivity = (title: string, details?: string, type: "index" | "query" | "upload" | "benchmark" = "query") => {
    const now = new Date();
    const timeStr = `Today, ${now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
    setActivity((prev) => [
      {
        id: `act_${Date.now()}`,
        timestamp: timeStr,
        title,
        details,
        type,
      },
      ...prev.slice(0, 19),
    ]);
  };

  // 1. Initial Data Fetching (Documents, Samples, Evaluation Scorecard)
  useEffect(() => {
    // Load pre-seeded sample benchmarks
    fetch("/api/v1/samples")
      .then((res) => res.json())
      .then((sampleData: SampleReport[]) => {
        setSamples(sampleData);
      })
      .catch((err) => console.warn("Failed to fetch sample benchmarks:", err));

    // Load registered documents
    fetch("/api/v1/documents")
      .then((res) => res.json())
      .then((docs: DocumentItem[]) => {
        if (Array.isArray(docs) && docs.length > 0) {
          setDocuments(docs);
          setSelectedDocId(docs[0].document_id);
          addActivity(
            `Loaded ${docs.length} indexed reports`,
            `Active: ${docs[0].filename} (${docs[0].page_count} pages)`,
            "index"
          );
        }
      })
      .catch((err) => console.error("Error loading documents:", err));

    // Load initial benchmark evaluation metrics
    fetch("/api/v1/evaluation")
      .then((res) => res.json())
      .then((data: EvaluationData) => setEvalData(data))
      .catch((err) => console.warn("Error loading evaluation metrics:", err));
  }, []);

  // 2. Fetch Evidence and Suggestions when selected document changes
  useEffect(() => {
    if (!selectedDocId) return;

    fetch(`/api/v1/documents/${selectedDocId}/evidence`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch evidence");
        return res.json();
      })
      .then((data: DocumentEvidenceData) => {
        setEvidenceData(data);
      })
      .catch((err) => console.warn("Error fetching evidence:", err));

    fetch(`/api/v1/documents/${selectedDocId}/suggestions`)
      .then((res) => res.json())
      .then((suggs) => {
        if (Array.isArray(suggs) && suggs.length > 0) {
          setSuggestions(suggs);
        } else {
          setSuggestions([]);
        }
      })
      .catch(() => setSuggestions([]));
  }, [selectedDocId]);

  // Handle PDF file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/v1/documents", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
      const newDoc: DocumentItem = await res.json();
      setDocuments((prev) => [newDoc, ...prev]);
      setSelectedDocId(newDoc.document_id);
      addActivity(`Indexed ${newDoc.filename}`, `${newDoc.page_count} pages processed with table boundaries`, "upload");
      // Seamlessly navigate into workspace for the newly uploaded document
      setCurrentView("workspace");
    } catch (err) {
      alert("Failed to upload and parse PDF document.");
    } finally {
      setIsUploading(false);
    }
  };

  // Handle Asking a Question (from either Dashboard or Workspace)
  const handleAskQuestion = async (queryText: string, docIdToUse?: string) => {
    const docId = docIdToUse || selectedDocId;
    if (!queryText.trim() || !docId) return;

    setIsLoadingQuestion(true);
    setAnswerData(null);
    setActiveHighlight(null);

    try {
      const res = await fetch("/api/v1/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: queryText,
          document_ids: [docId],
        }),
      });

      if (!res.ok) throw new Error("Question processing failed");
      const data: AnswerResponse = await res.json();
      setAnswerData(data);

      addActivity(
        `Answered: "${queryText.slice(0, 45)}..."`,
        `Outcome: ${data.status.toUpperCase()} · ${data.citations.length} citations`,
        "query"
      );

      // Auto-navigate to top cited evidence
      if (data.citations && data.citations.length > 0) {
        const topCitation = data.citations[0];
        if (topCitation.bbox) {
          const bbox = topCitation.bbox;
          setTargetPageIndex(topCitation.pdf_page_index);
          setActiveHighlight({
            bbox: bbox,
            id: topCitation.evidence_id,
            label: `Evidence · p.${topCitation.printed_page_number || topCitation.pdf_page_index + 1}`,
            pageIndex: topCitation.pdf_page_index,
          });
        }
      }
    } catch (err) {
      alert("Error processing question. Please check backend connection.");
    } finally {
      setIsLoadingQuestion(false);
    }
  };

  // User selects a document from the Research Dashboard
  const handleSelectDocument = (docId: string, initialQuestion?: string) => {
    setSelectedDocId(docId);
    setCurrentView("workspace");

    if (initialQuestion) {
      handleAskQuestion(initialQuestion, docId);
    }
  };

  // User clicks a citation
  const handleSelectCitation = (citation: CitationItem) => {
    setTargetPageIndex(citation.pdf_page_index);
    if (citation.bbox) {
      setActiveHighlight({
        bbox: citation.bbox,
        id: citation.evidence_id,
        label: `Cited Evidence · Page ${citation.printed_page_number || citation.pdf_page_index + 1}`,
        pageIndex: citation.pdf_page_index,
      });
    }
  };

  // User highlights a structured table from TableExplorer
  const handleHighlightTable = (table: TableItem, label?: string) => {
    setTargetPageIndex(table.pdf_page_index);
    if (table.bbox) {
      setActiveHighlight({
        bbox: table.bbox,
        id: table.table_id,
        label: label || `Table on Page ${table.printed_page_number || table.pdf_page_index + 1}`,
        pageIndex: table.pdf_page_index,
      });
    }
  };

  // Run live evaluation benchmark suite
  const handleRunBenchmark = async () => {
    setIsEvalRunning(true);
    try {
      const res = await fetch("/api/v1/evaluation/run", { method: "POST" });
      const data: EvaluationData = await res.json();
      setEvalData(data);
      addActivity(
        "Executed Benchmark Suite",
        `Accuracy: ${data.summary.accuracy_percentage.toFixed(1)}% (${data.summary.passed_cases}/${data.summary.total_cases})`,
        "benchmark"
      );
    } catch (e) {
      alert("Failed to execute benchmark evaluation suite.");
    } finally {
      setIsEvalRunning(false);
    }
  };

  const selectedDocument = documents.find((d) => d.document_id === selectedDocId) || documents[0] || null;

  return (
    <div className="report-navigator-app">
      {currentView === "dashboard" ? (
        <ResearchDashboard
          documents={documents}
          samples={samples}
          activity={activity}
          evalData={evalData}
          isEvalRunning={isEvalRunning}
          isUploading={isUploading}
          onSelectDocument={handleSelectDocument}
          onFileUpload={handleFileUpload}
          onRunBenchmark={handleRunBenchmark}
        />
      ) : (
        <ReportWorkspace
          document={selectedDocument}
          evidenceData={evidenceData}
          suggestions={suggestions}
          answerData={answerData}
          targetPageIndex={targetPageIndex}
          activeHighlight={activeHighlight}
          isLoadingQuestion={isLoadingQuestion}
          onBackToDashboard={() => setCurrentView("dashboard")}
          onAskQuestion={(q) => handleAskQuestion(q)}
          onJumpToPage={(p) => setTargetPageIndex(p)}
          onSelectCitation={handleSelectCitation}
          onHighlightTable={handleHighlightTable}
        />
      )}
    </div>
  );
};

export default App;
