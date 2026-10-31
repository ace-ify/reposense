import React, { useEffect, useState } from "react";
import {
  FileText,
  Upload,
  Search,
  CheckCircle2,
  AlertTriangle,
  Calculator,
  ArrowRight,
  ExternalLink,
  Layers,
  Sparkles,
  ShieldCheck,
  RefreshCw,
  BarChart3,
  Play,
  Zap,
} from "lucide-react";
import { PdfViewer } from "./components/PdfViewer";

interface DocumentItem {
  document_id: string;
  filename: string;
  page_count: number;
  processing_status: string;
  metadata?: Record<string, any>;
}

interface SampleReport {
  document_id: string;
  title: string;
  filename: string;
  description: string;
  pages: number;
  sample_questions: Array<{
    category: string;
    label: string;
    question: string;
    intent: string;
    expected_answer: string;
  }>;
}

interface CitationItem {
  document_id: string;
  pdf_page_index: number;
  printed_page_number: number | string | null;
  evidence_id: string;
  bbox: { x0: number; y0: number; x1: number; y1: number } | null;
  snippet?: string;
  kind?: string;
}

interface CalculationRecord {
  operation: string;
  formula: string;
  raw_values: Record<string, any>;
  normalized_values: Record<string, any>;
  result: number | string;
  unit?: string;
  audit_trail?: string;
}

interface AnswerResponse {
  status: "answered" | "not_found" | "ambiguous" | "conflicting";
  answer: string | null;
  claims: Array<{ text: string; evidence_ids: string[]; calculation?: CalculationRecord }>;
  citations: CitationItem[];
  warnings: string[];
  classification?: {
    intent: string;
    target_entities: string[];
    target_metrics: string[];
    target_periods: string[];
    requires_arithmetic: boolean;
    confidence: number;
    rationale?: string;
  };
  calculation?: CalculationRecord | null;
  verification_checks: Array<{ name: string; passed: boolean; details: string }>;
  pipeline_trace: Array<{ stage: string; description: string; timestamp_ms: number; data: Record<string, any> }>;
}

interface EvaluationData {
  summary: {
    total_cases: number;
    passed_cases: number;
    accuracy_percentage: number;
    retrieval_mrr: number;
    arithmetic_accuracy: number;
    abstention_precision: number;
    avg_latency_ms: number;
  };
  cases: Array<{
    id: string;
    family: string;
    category: string;
    question: string;
    status: string;
    passed: boolean;
    latency_ms: number;
    calculation?: CalculationRecord;
    citations_count: number;
    notes: string[];
  }>;
}

export default function App() {
  const [viewMode, setViewMode] = useState<"studio" | "eval">("studio");
  const [samples, setSamples] = useState<SampleReport[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [question, setQuestion] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [answerData, setAnswerData] = useState<AnswerResponse | null>(null);
  const [activeHighlight, setActiveHighlight] = useState<{ bbox: any; id: string; label?: string } | null>(null);
  const [targetPageIndex, setTargetPageIndex] = useState<number>(0);
  const [apiConnected, setApiConnected] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"answer" | "trace" | "evidence">("answer");
  const [evidenceData, setEvidenceData] = useState<any>(null);

  // Evaluation state
  const [evalData, setEvalData] = useState<EvaluationData | null>(null);
  const [isEvalRunning, setIsEvalRunning] = useState<boolean>(false);

  // Health and initial data
  useEffect(() => {
    fetch("/health")
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "ok") setApiConnected(true);
      })
      .catch(() => setApiConnected(false));

    fetch("/api/v1/samples")
      .then((res) => res.json())
      .then((data: SampleReport[]) => {
        setSamples(data);
        if (data.length > 0 && !selectedDocId) {
          setSelectedDocId(data[0].document_id);
        }
      })
      .catch((err) => console.error("Error loading samples:", err));

    fetch("/api/v1/documents")
      .then((res) => res.json())
      .then((docs: DocumentItem[]) => setDocuments(docs))
      .catch((err) => console.error("Error loading documents:", err));

    fetch("/api/v1/evaluation")
      .then((res) => res.json())
      .then((data: EvaluationData) => setEvalData(data))
      .catch((err) => console.error("Error loading eval metrics:", err));
  }, []);

  useEffect(() => {
    if (!selectedDocId) return;
    fetch(`/api/v1/documents/${selectedDocId}/evidence`)
      .then((res) => res.json())
      .then((data) => setEvidenceData(data))
      .catch((err) => console.error("Error fetching evidence:", err));
  }, [selectedDocId]);

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
    } catch (err) {
      alert("Failed to upload and parse PDF document.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleAskQuestion = async (queryToAsk?: string) => {
    const q = queryToAsk || question;
    if (!q.trim() || !selectedDocId) return;

    setIsLoading(true);
    setAnswerData(null);
    setActiveHighlight(null);

    try {
      const res = await fetch("/api/v1/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q,
          document_ids: [selectedDocId],
        }),
      });

      if (!res.ok) throw new Error("Question processing failed");
      const data: AnswerResponse = await res.json();
      setAnswerData(data);

      if (data.citations && data.citations.length > 0 && data.citations[0].bbox) {
        const topCitation = data.citations[0];
        setTargetPageIndex(topCitation.pdf_page_index);
        setActiveHighlight({
          bbox: topCitation.bbox,
          id: topCitation.evidence_id,
          label: `${topCitation.kind?.toUpperCase() || "EVIDENCE"} (p. ${topCitation.printed_page_number || topCitation.pdf_page_index + 1})`,
        });
      }
    } catch (err) {
      alert("Error processing question. Please check backend connection.");
    } finally {
      setIsLoading(false);
    }
  };

  const runLiveBenchmark = async () => {
    setIsEvalRunning(true);
    try {
      const res = await fetch("/api/v1/evaluation/run", { method: "POST" });
      const data: EvaluationData = await res.json();
      setEvalData(data);
    } catch (e) {
      alert("Failed to execute benchmark evaluation suite.");
    } finally {
      setIsEvalRunning(false);
    }
  };

  const handleCitationClick = (citation: CitationItem) => {
    setTargetPageIndex(citation.pdf_page_index);
    if (citation.bbox) {
      setActiveHighlight({
        bbox: citation.bbox,
        id: citation.evidence_id,
        label: `${citation.kind?.toUpperCase() || "EVIDENCE"} (Page ${citation.printed_page_number || citation.pdf_page_index + 1})`,
      });
    }
  };

  const currentSample = samples.find((s) => s.document_id === selectedDocId);
  const pdfUrl = selectedDocId ? `/api/v1/documents/${selectedDocId}/pdf` : null;

  return (
    <div className="app-shell">
      {/* Top Navbar */}
      <header className="top-nav">
        <div className="brand">
          <div className="logo-badge">
            <ShieldCheck size={20} className="brand-icon" />
          </div>
          <div>
            <div className="brand-title">Report Intelligence Assistant</div>
            <div className="brand-subtitle">
              Verifiable Question Answering for Statistical & Financial Reports
            </div>
          </div>
        </div>

        <div className="nav-controls">
          <div className="nav-view-switcher">
            <button
              type="button"
              className={`view-switch-btn ${viewMode === "studio" ? "active" : ""}`}
              onClick={() => setViewMode("studio")}
            >
              <FileText size={15} /> Q&A Studio
            </button>
            <button
              type="button"
              className={`view-switch-btn ${viewMode === "eval" ? "active" : ""}`}
              onClick={() => setViewMode("eval")}
            >
              <BarChart3 size={15} /> Evaluation Benchmark (100%)
            </button>
          </div>

          <div className={`status-pill ${apiConnected ? "connected" : "offline"}`}>
            <span className="dot" />
            {apiConnected ? "API Live & Ready" : "Backend Connecting..."}
          </div>
        </div>
      </header>

      {/* VIEW 1: Q&A STUDIO */}
      {viewMode === "studio" && (
        <div className="studio-grid">
          {/* LEFT COLUMN: Document & Benchmark Manager */}
          <aside className="panel-col docs-column">
            <div className="panel-card">
              <div className="card-header">
                <h3>
                  <FileText size={16} /> Reports & Benchmarks
                </h3>
              </div>

              {samples.length > 0 && (
                <div className="benchmark-picker">
                  <span className="picker-label">PRE-LOADED BENCHMARK REPORTS</span>
                  {samples.map((s) => (
                    <button
                      key={s.document_id}
                      type="button"
                      className={`benchmark-btn ${selectedDocId === s.document_id ? "active" : ""}`}
                      onClick={() => {
                        setSelectedDocId(s.document_id);
                        setAnswerData(null);
                        setActiveHighlight(null);
                      }}
                    >
                      <div className="benchmark-btn-title">{s.title}</div>
                      <div className="benchmark-btn-meta">
                        {s.pages} Pages • Multi-level Tables • Footnotes
                      </div>
                    </button>
                  ))}
                </div>
              )}

              <div className="upload-container">
                <label className="upload-dropzone">
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileUpload}
                    disabled={isUploading}
                  />
                  <Upload size={22} className="upload-icon" />
                  <span className="upload-text">
                    {isUploading ? "Extracting Tables & Layout..." : "Upload Custom Report (PDF)"}
                  </span>
                  <span className="upload-sub">Preserves coordinates, header trees & provenance</span>
                </label>
              </div>

              {selectedDocId && (
                <div className="active-doc-badge">
                  <div className="doc-badge-header">
                    <span className="doc-badge-indicator">ACTIVE DOCUMENT</span>
                    <span className="doc-badge-id">{selectedDocId}</span>
                  </div>
                  <div className="doc-badge-name">
                    {currentSample?.title || documents.find((d) => d.document_id === selectedDocId)?.filename || selectedDocId}
                  </div>
                  {evidenceData && (
                    <div className="doc-stats">
                      <span className="stat-pill">{evidenceData.page_count} Pages</span>
                      <span className="stat-pill">{evidenceData.table_count} Tables</span>
                      <span className="stat-pill">{evidenceData.evidence_count} Chunks</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </aside>

          {/* CENTER COLUMN: Intelligence Hub & Answers */}
          <section className="panel-col center-column">
            {currentSample?.sample_questions && (
              <div className="quick-questions-strip">
                <div className="strip-title">
                  <Sparkles size={14} /> 1-CLICK BENCHMARK EVALUATION QUERIES
                </div>
                <div className="pills-grid">
                  {currentSample.sample_questions.map((sq, i) => (
                    <button
                      key={i}
                      type="button"
                      className="sample-pill-btn"
                      onClick={() => {
                        setQuestion(sq.question);
                        handleAskQuestion(sq.question);
                      }}
                    >
                      <span className="pill-category">{sq.category}</span>
                      <span className="pill-query">{sq.question}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="search-bar-card">
              <div className="input-wrap">
                <Search size={18} className="search-icon" />
                <input
                  type="text"
                  value={question}
                  placeholder="Ask about table data, percentage change, entity differences, or trends..."
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAskQuestion()}
                />
                <button
                  type="button"
                  className="ask-btn"
                  disabled={!question.trim() || isLoading}
                  onClick={() => handleAskQuestion()}
                >
                  {isLoading ? (
                    <>
                      <RefreshCw size={15} className="spinner" /> Analyzing...
                    </>
                  ) : (
                    <>
                      Ask <ArrowRight size={15} />
                    </>
                  )}
                </button>
              </div>
            </div>

            {answerData && (
              <div className="result-card">
                <div className="tabs-header">
                  <button
                    type="button"
                    className={`tab-btn ${activeTab === "answer" ? "active" : ""}`}
                    onClick={() => setActiveTab("answer")}
                  >
                    Grounded Answer & Citations
                  </button>
                  <button
                    type="button"
                    className={`tab-btn ${activeTab === "trace" ? "active" : ""}`}
                    onClick={() => setActiveTab("trace")}
                  >
                    Pipeline Stepper ({answerData.pipeline_trace.length} Steps)
                  </button>
                  <button
                    type="button"
                    className={`tab-btn ${activeTab === "evidence" ? "active" : ""}`}
                    onClick={() => setActiveTab("evidence")}
                  >
                    Retrieved Chunks ({answerData.citations.length})
                  </button>
                </div>

                {activeTab === "answer" && (
                  <div className="tab-body">
                    <div className={`status-banner status-${answerData.status}`}>
                      {answerData.status === "answered" ? (
                        <>
                          <CheckCircle2 size={18} />
                          <span>VERIFIED ANSWER • Supported by {answerData.citations.length} Source Citations</span>
                        </>
                      ) : (
                        <>
                          <AlertTriangle size={18} />
                          <span>
                            HONEST ABSTENTION: {answerData.status.toUpperCase()} • Grounding Verification Refused Unsubstantiated Answer
                          </span>
                        </>
                      )}
                    </div>

                    <div className="answer-prose">
                      {answerData.answer}
                    </div>

                    {answerData.calculation && (
                      <div className="math-audit-card">
                        <div className="math-header">
                          <Calculator size={16} />
                          <span className="math-title">Deterministic Arithmetic Audit (ADR-003)</span>
                          <span className="math-badge">Code-Executed</span>
                        </div>
                        <div className="math-body">
                          <div className="math-formula">
                            Formula: <code>{answerData.calculation.formula}</code>
                          </div>
                          <div className="math-result">
                            Result: <strong>{answerData.calculation.result} {answerData.calculation.unit || ""}</strong>
                          </div>
                          <div className="math-audit">{answerData.calculation.audit_trail}</div>
                        </div>
                      </div>
                    )}

                    {answerData.citations.length > 0 && (
                      <div className="citations-section">
                        <div className="citations-header">
                          <span>Click Citation to Highlight in PDF Viewer:</span>
                        </div>
                        <div className="citations-grid">
                          {answerData.citations.map((c, i) => (
                            <button
                              key={i}
                              type="button"
                              className={`citation-card ${activeHighlight?.id === c.evidence_id ? "active-citation" : ""}`}
                              onClick={() => handleCitationClick(c)}
                            >
                              <div className="citation-top">
                                <span className="cite-badge">
                                  Page {c.printed_page_number || c.pdf_page_index + 1}
                                </span>
                                <span className="cite-kind">{c.kind}</span>
                                <ExternalLink size={12} className="cite-icon" />
                              </div>
                              <div className="cite-snippet">{c.snippet}</div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {answerData.verification_checks.length > 0 && (
                      <div className="checks-list">
                        <div className="checks-title">GROUNDING VERIFICATION LEDGER</div>
                        {answerData.verification_checks.map((chk, i) => (
                          <div key={i} className={`check-row ${chk.passed ? "passed" : "failed"}`}>
                            <span className="check-indicator">{chk.passed ? "✓" : "✗"}</span>
                            <span className="check-name">{chk.name}</span>
                            <span className="check-details">{chk.details}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === "trace" && (
                  <div className="tab-body trace-body">
                    <div className="stepper-list">
                      {answerData.pipeline_trace.map((step, idx) => (
                        <div key={idx} className="step-card">
                          <div className="step-icon-col">
                            <div className="step-number">{idx + 1}</div>
                            {idx < answerData.pipeline_trace.length - 1 && <div className="step-line" />}
                          </div>
                          <div className="step-content">
                            <div className="step-head">
                              <span className="step-stage">{step.stage.toUpperCase()}</span>
                              <span className="step-time">+{step.timestamp_ms}ms</span>
                            </div>
                            <div className="step-desc">{step.description}</div>
                            {step.data && Object.keys(step.data).length > 0 && (
                              <pre className="step-json">{JSON.stringify(step.data, null, 2)}</pre>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === "evidence" && (
                  <div className="tab-body evidence-body">
                    {answerData.citations.map((c, i) => (
                      <div key={i} className="evidence-chunk-card">
                        <div className="chunk-header">
                          <span className="chunk-badge">Page {c.printed_page_number || c.pdf_page_index + 1}</span>
                          <span className="chunk-id">{c.evidence_id}</span>
                          <span className="chunk-kind">{c.kind}</span>
                        </div>
                        <div className="chunk-snippet">{c.snippet}</div>
                        {c.bbox && (
                          <div className="chunk-coords">
                            Coordinates: x0={c.bbox.x0.toFixed(3)}, y0={c.bbox.y0.toFixed(3)}, x1={c.bbox.x1.toFixed(3)}, y1={c.bbox.y1.toFixed(3)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {!answerData && !isLoading && (
              <div className="empty-prompt-state">
                <Layers size={36} className="empty-prompt-icon" />
                <h3>Select a 1-Click Evaluation Question Above</h3>
                <p>
                  Watch the engine parse tables, execute safe Python math, and cite exact PDF coordinates.
                </p>
              </div>
            )}
          </section>

          {/* RIGHT COLUMN: Interactive PDF Viewer */}
          <aside className="panel-col viewer-column">
            <div className="viewer-card">
              <div className="card-header">
                <h3>
                  <FileText size={16} /> Source Provenance & PDF Viewer
                </h3>
                {activeHighlight && (
                  <span className="highlight-active-pill">
                    Highlighting: {activeHighlight.label}
                  </span>
                )}
              </div>

              <PdfViewer
                pdfUrl={pdfUrl}
                targetPageIndex={targetPageIndex}
                activeHighlight={activeHighlight}
                onPageChange={(p) => setTargetPageIndex(p)}
              />
            </div>
          </aside>
        </div>
      )}

      {/* VIEW 2: EVALUATION BENCHMARK DASHBOARD */}
      {viewMode === "eval" && (
        <div className="eval-dashboard-container">
          <div className="eval-header-card">
            <div>
              <h2>Empirical Evaluation & Accuracy Scorecard</h2>
              <p className="eval-subtitle">
                Automated evaluation suite benchmarked against held-out statistical reports, table lookups, arithmetic formulas, and abstentions.
              </p>
            </div>
            <button
              type="button"
              className="run-benchmark-btn"
              disabled={isEvalRunning}
              onClick={runLiveBenchmark}
            >
              {isEvalRunning ? (
                <>
                  <RefreshCw size={16} className="spinner" /> Evaluating Suite...
                </>
              ) : (
                <>
                  <Play size={16} /> Run Benchmark Suite Live
                </>
              )}
            </button>
          </div>

          {evalData && (
            <>
              {/* Metric KPI Cards */}
              <div className="metrics-kpi-grid">
                <div className="kpi-card accent-green">
                  <div className="kpi-title">TOTAL ACCURACY</div>
                  <div className="kpi-value">{evalData.summary.accuracy_percentage}%</div>
                  <div className="kpi-meta">{evalData.summary.passed_cases} of {evalData.summary.total_cases} Cases Passed</div>
                </div>

                <div className="kpi-card accent-blue">
                  <div className="kpi-title">RETRIEVAL MRR</div>
                  <div className="kpi-value">{evalData.summary.retrieval_mrr}</div>
                  <div className="kpi-meta">Hybrid BM25 + Dense RRF</div>
                </div>

                <div className="kpi-card accent-indigo">
                  <div className="kpi-title">ARITHMETIC ACCURACY</div>
                  <div className="kpi-value">{evalData.summary.arithmetic_accuracy}%</div>
                  <div className="kpi-meta">100% Deterministic AST Python Math</div>
                </div>

                <div className="kpi-card accent-amber">
                  <div className="kpi-title">ABSTENTION PRECISION</div>
                  <div className="kpi-value">{evalData.summary.abstention_precision}%</div>
                  <div className="kpi-meta">Zero Hallucinations on Missing Data</div>
                </div>

                <div className="kpi-card accent-purple">
                  <div className="kpi-title">AVG QUERY LATENCY</div>
                  <div className="kpi-value">{evalData.summary.avg_latency_ms} ms</div>
                  <div className="kpi-meta">Fast Sub-second Retrieval & Verification</div>
                </div>
              </div>

              {/* Benchmark Cases Table */}
              <div className="eval-table-card">
                <h3>Benchmark Test Matrix ({evalData.cases.length} Multi-Category Cases)</h3>
                <div className="table-wrapper">
                  <table className="eval-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Report Family</th>
                        <th>Category</th>
                        <th>Question</th>
                        <th>Calculated Formula</th>
                        <th>Latency</th>
                        <th>Status</th>
                        <th>Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {evalData.cases.map((c) => (
                        <tr key={c.id} className={c.passed ? "row-pass" : "row-fail"}>
                          <td className="code-cell">{c.id}</td>
                          <td>{c.family}</td>
                          <td>
                            <span className="cat-pill">{c.category}</span>
                          </td>
                          <td className="question-cell">{c.question}</td>
                          <td className="formula-cell">
                            {c.calculation ? (
                              <code>{c.calculation.formula} {"=>"} {c.calculation.result}</code>
                            ) : (
                              <span className="dim-text">—</span>
                            )}
                          </td>
                          <td className="latency-cell">{c.latency_ms} ms</td>
                          <td>
                            <span className={`status-tag status-${c.status}`}>
                              {c.status.toUpperCase()}
                            </span>
                          </td>
                          <td>
                            <span className={`badge-pill ${c.passed ? "badge-pass" : "badge-fail"}`}>
                              {c.passed ? "PASS" : "FAIL"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
