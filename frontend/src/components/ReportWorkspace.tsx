import React, { useState, useMemo, useEffect } from "react";
import {
  ArrowLeft,
  Share2,
  FileEdit,
  Download,
  MoreHorizontal,
  ChevronRight,
  BarChart2,
  FileText,
  Search,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  Calculator,
  Layers,
  Sparkles,
  Info,
  Check,
  X,
  FileSpreadsheet,
  CornerDownRight,
  Loader2,
  Save,
  Trash2,
} from "lucide-react";
import {
  AnswerResponse,
  CitationItem,
  DocumentEvidenceData,
  DocumentItem,
  HighlightBox,
  TableItem,
} from "../types";
import { PdfViewer } from "./PdfViewer";
import { TableExplorer } from "./TableExplorer";

interface ReportWorkspaceProps {
  document: DocumentItem | null;
  evidenceData: DocumentEvidenceData | null;
  isLoadingEvidence?: boolean;
  evidenceError?: string | null;
  suggestions: Array<{ label: string; question: string; category?: string; intent?: string }>;
  answerData: AnswerResponse | null;
  targetPageIndex: number;
  activeHighlight: HighlightBox | null;
  isLoadingQuestion: boolean;
  onBackToDashboard: () => void;
  onAskQuestion: (query: string) => void;
  onJumpToPage: (pageIndex: number) => void;
  onSelectCitation: (citation: CitationItem) => void;
  onHighlightTable: (table: TableItem, label?: string) => void;
}

export const ReportWorkspace: React.FC<ReportWorkspaceProps> = ({
  document,
  evidenceData,
  isLoadingEvidence = false,
  evidenceError = null,
  suggestions,
  answerData,
  targetPageIndex,
  activeHighlight,
  isLoadingQuestion,
  onBackToDashboard,
  onAskQuestion,
  onJumpToPage,
  onSelectCitation,
  onHighlightTable,
}) => {
  const [leftNavTab, setLeftNavTab] = useState<"outline" | "pages">("outline");
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState<boolean>(false);
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState<boolean>(false);
  const [inspectorTab, setInspectorTab] = useState<"evidence" | "method" | "checks" | "tables">("evidence");
  const [inputQuestion, setInputQuestion] = useState<string>("");
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  // Real local storage note editor
  const [isNoteModalOpen, setIsNoteModalOpen] = useState<boolean>(false);
  const [noteContent, setNoteContent] = useState<string>("");

  useEffect(() => {
    if (document) {
      const savedNote = localStorage.getItem(`report_notes_${document.document_id}`) || "";
      setNoteContent(savedNote);
    } else {
      setNoteContent("");
    }
  }, [document?.document_id]);

  const handleSaveNote = () => {
    if (!document) return;
    localStorage.setItem(`report_notes_${document.document_id}`, noteContent);
    setIsNoteModalOpen(false);
    showFeedback("Note saved to browser storage.");
  };

  const handleDeleteNote = () => {
    if (!document) return;
    localStorage.removeItem(`report_notes_${document.document_id}`);
    setNoteContent("");
    setIsNoteModalOpen(false);
    showFeedback("Note removed from browser storage.");
  };

  const showFeedback = (msg: string) => {
    setActionFeedback(msg);
    setTimeout(() => setActionFeedback(null), 3500);
  };

  const handleQuestionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuestion.trim()) return;
    onAskQuestion(inputQuestion.trim());
  };

  const handleShare = () => {
    if (!document) return;
    const shareUrl = `${window.location.origin}${window.location.pathname}?doc=${encodeURIComponent(document.document_id)}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(shareUrl).then(() => {
        showFeedback(`Link copied: reopens ${document.filename}`);
      }).catch(() => {
        showFeedback(`Share URL: ${shareUrl}`);
      });
    } else {
      showFeedback(`Share URL: ${shareUrl}`);
    }
  };

  // Build outline items dynamically from live evidence data
  const outlineItems = useMemo(() => {
    if (!evidenceData) return [];

    const items: Array<{
      id: string;
      title: string;
      pageIndex: number;
      kind: "heading" | "table";
      level?: number;
    }> = [];

    // Add headings
    evidenceData.evidence
      .filter((ev) => ev.kind === "heading")
      .forEach((h, idx) => {
        items.push({
          id: h.evidence_id || `head_${idx}`,
          title: h.text.slice(0, 70),
          pageIndex: h.pdf_page_index,
          kind: "heading",
          level: 1,
        });
      });

    // Add structured tables
    evidenceData.tables.forEach((tbl, idx) => {
      items.push({
        id: tbl.table_id || `tbl_${idx}`,
        title: tbl.title ? tbl.title.slice(0, 60) : `Table on Page ${tbl.printed_page_number || tbl.pdf_page_index + 1}`,
        pageIndex: tbl.pdf_page_index,
        kind: "table",
        level: 2,
      });
    });

    return items.sort((a, b) => a.pageIndex - b.pageIndex);
  }, [evidenceData]);

  const pdfUrl = document ? `/api/v1/documents/${document.document_id}/pdf` : null;
  const isIndexed = document?.processing_status === "ready" || (document?.page_count || 0) > 0;

  // Extract structured key-values from answerData for Evidence tab
  const evidenceFacets = useMemo(() => {
    if (!answerData) return null;

    const classification = answerData.classification;
    const topCitation = answerData.citations[0];

    const entity = classification?.target_entities?.join(", ") || (answerData.answer ? "Target Entity" : "—");
    const metric = classification?.target_metrics?.join(", ") || classification?.intent || "Standard Metric";
    const value = answerData.answer || (answerData.status === "not_found" ? "NOT_FOUND" : "—");
    const period = classification?.target_periods?.join(", ") || "Report Period";
    const unit = answerData.calculation?.unit || "standard units";

    return {
      entity,
      metric,
      value,
      period,
      unit,
      source: document?.metadata?.source || document?.filename || "Official Statistical Report",
      snippet: topCitation?.snippet || (answerData.claims[0]?.text ?? ""),
    };
  }, [answerData, document]);

  // Derived Grounding Status strictly from answer status, citations, and verification checks
  const groundingStatus = useMemo(() => {
    if (!answerData) return null;

    if (answerData.status === "not_found") {
      return {
        label: "Not found in report (honest refusal)",
        className: "abstention",
        dotColor: "dot-amber",
      };
    }
    if (answerData.status === "ambiguous") {
      return {
        label: "Ambiguous query result",
        className: "abstention",
        dotColor: "dot-amber",
      };
    }
    if (answerData.status === "conflicting") {
      return {
        label: "Conflicting evidence in report",
        className: "abstention",
        dotColor: "dot-amber",
      };
    }

    const checks = answerData.verification_checks || [];
    if (checks.length > 0) {
      const passedCount = checks.filter((c) => c.passed).length;
      const totalCount = checks.length;
      if (passedCount === totalCount) {
        return {
          label: `Grounding verified (${passedCount}/${totalCount} checks passed)`,
          className: "high",
          dotColor: "dot-green",
        };
      } else {
        const failedCount = totalCount - passedCount;
        return {
          label: `Verification flagged (${failedCount} check${failedCount > 1 ? "s" : ""} failed)`,
          className: "flagged",
          dotColor: "dot-amber",
        };
      }
    }

    // Neutral wording when no verification checks returned by API
    if (answerData.citations && answerData.citations.length > 0) {
      return {
        label: `Evidence cited (${answerData.citations.length} source${answerData.citations.length > 1 ? "s" : ""})`,
        className: "neutral",
        dotColor: "dot-green",
      };
    }

    return {
      label: "Unreferenced response",
      className: "unreferenced",
      dotColor: "dot-amber",
    };
  }, [answerData]);

  return (
    <div className="workspace-shell">
      {/* FLOATING ACTION TOAST */}
      {actionFeedback && (
        <div className="floating-action-toast">
          <Info size={14} />
          <span>{actionFeedback}</span>
        </div>
      )}

      {/* REAL NOTE MODAL */}
      {isNoteModalOpen && (
        <div className="note-modal-backdrop" onClick={() => setIsNoteModalOpen(false)}>
          <div className="note-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="note-modal-header">
              <div className="note-modal-title">
                <FileEdit size={16} />
                <span>Research Notes · {document?.filename}</span>
              </div>
              <button
                type="button"
                className="btn-panel-toggle"
                onClick={() => setIsNoteModalOpen(false)}
              >
                ✕
              </button>
            </div>
            <div className="note-modal-body">
              <textarea
                className="note-textarea"
                placeholder="Write observations, notes, or findings about this report (persisted in browser storage)..."
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                rows={8}
              />
              <div className="note-storage-hint">
                Notes are persisted in local browser storage for document ID: <code>{document?.document_id}</code>.
              </div>
            </div>
            <div className="note-modal-actions">
              {noteContent && (
                <button type="button" className="btn-note-delete" onClick={handleDeleteNote}>
                  <Trash2 size={13} />
                  <span>Clear Note</span>
                </button>
              )}
              <div style={{ display: "flex", gap: "8px", marginLeft: "auto" }}>
                <button
                  type="button"
                  className="btn-text-action"
                  onClick={() => setIsNoteModalOpen(false)}
                >
                  Cancel
                </button>
                <button type="button" className="btn-primary-cobalt" onClick={handleSaveNote}>
                  <Save size={13} />
                  <span>Save Note</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TOP WORKSPACE NAVIGATION BAR */}
      <header className="workspace-topbar">
        {/* Left: Back button + Document Info */}
        <div className="workspace-title-group">
          <button
            type="button"
            className="btn-back-dashboard"
            onClick={onBackToDashboard}
            title="Return to Research Desk"
          >
            <ArrowLeft size={16} />
          </button>

          <div className="doc-headline-block">
            <div className="doc-title-row">
              <span className="doc-title-text">
                {document?.metadata?.title || document?.filename || "Statistical Report"}
              </span>
              <span className="doc-status-pill">
                <span className={`status-dot ${isIndexed ? "dot-green" : "dot-amber"}`} />
                <span className="status-label">
                  {document?.processing_status || (isIndexed ? "ready" : "processing")}
                </span>
              </span>
            </div>
            <div className="doc-meta-row">
              {document ? `${document.page_count} pages · Status: ${document.processing_status}` : ""}
            </div>
          </div>
        </div>

        {/* Right: Workspace Action Buttons */}
        <div className="workspace-actions-group">
          <button
            type="button"
            className="workspace-action-btn"
            onClick={handleShare}
            title="Copy link to reopen this report"
          >
            <Share2 size={14} />
            <span>Share</span>
          </button>

          <button
            type="button"
            className="workspace-action-btn"
            onClick={() => setIsNoteModalOpen(true)}
            title="Open research notes (persisted in local browser storage)"
          >
            <FileEdit size={14} />
            <span>{noteContent ? "View note" : "Add note"}</span>
          </button>

          {document && (
            <a
              href={`/api/v1/documents/${document.document_id}/pdf`}
              download={document.filename}
              className="workspace-action-btn"
              title="Download original PDF"
            >
              <Download size={14} />
              <span>Download</span>
            </a>
          )}
        </div>
      </header>

      {/* THREE-PANEL WORKSPACE BODY */}
      <div className="workspace-panels-container">
        {/* LEFT PANEL: Collapsible Outline & Page Navigation */}
        <div className={`workspace-left-panel ${leftPanelCollapsed ? "collapsed" : ""}`}>
          <div className="panel-header-row">
            <div className="panel-tabs">
              <button
                type="button"
                className={`panel-tab-btn ${leftNavTab === "outline" ? "active" : ""}`}
                onClick={() => setLeftNavTab("outline")}
              >
                Outline
              </button>
              <button
                type="button"
                className={`panel-tab-btn ${leftNavTab === "pages" ? "active" : ""}`}
                onClick={() => setLeftNavTab("pages")}
              >
                Pages
              </button>
            </div>
            <button
              type="button"
              className="btn-panel-toggle"
              onClick={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
              title={leftPanelCollapsed ? "Expand panel" : "Collapse panel"}
            >
              {leftPanelCollapsed ? ">>" : "<<"}
            </button>
          </div>

          <div className="panel-scroll-content">
            {isLoadingEvidence ? (
              <div className="outline-empty-state">
                <Loader2 size={20} className="spinner-icon" />
                <span style={{ marginTop: "8px", fontSize: "12px" }}>Loading outline...</span>
              </div>
            ) : evidenceError ? (
              <div className="outline-empty-state">
                <span style={{ color: "var(--color-rose)", fontSize: "12px" }}>{evidenceError}</span>
              </div>
            ) : leftNavTab === "outline" ? (
              <div className="outline-tree">
                {outlineItems.length === 0 ? (
                  <div className="outline-empty-state">
                    <Layers size={24} className="empty-glyph" />
                    <span>No headings or tables found in evidence</span>
                  </div>
                ) : (
                  outlineItems.map((item) => {
                    const isCurrentPage = targetPageIndex === item.pageIndex;
                    return (
                      <div
                        key={item.id}
                        className={`outline-item-row ${isCurrentPage ? "active-page-item" : ""}`}
                        onClick={() => onJumpToPage(item.pageIndex)}
                        title={`Jump to Page ${item.pageIndex + 1}`}
                      >
                        <div className="outline-item-content">
                          {isCurrentPage && <span className="active-dot">•</span>}
                          {item.kind === "table" ? (
                            <FileSpreadsheet size={13} className="outline-kind-icon table" />
                          ) : (
                            <ChevronRight size={13} className="outline-kind-icon" />
                          )}
                          <span className="outline-item-title">{item.title}</span>
                        </div>
                        <span className="outline-page-badge">p.{item.pageIndex + 1}</span>
                      </div>
                    );
                  })
                )}
              </div>
            ) : (
              <div className="pages-thumbnail-grid">
                {Array.from({ length: document?.page_count || 1 }, (_, i) => i).map((pIdx) => {
                  const isCurrent = targetPageIndex === pIdx;
                  return (
                    <div
                      key={pIdx}
                      className={`page-thumb-card ${isCurrent ? "current-thumb" : ""}`}
                      onClick={() => onJumpToPage(pIdx)}
                    >
                      <div className="thumb-preview-box">
                        <FileText size={20} className="thumb-icon" />
                      </div>
                      <span className="thumb-label">{pIdx + 1}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* CENTER PANEL: Dominant PDF Viewer */}
        <div className="workspace-center-panel">
          <PdfViewer
            pdfUrl={pdfUrl}
            targetPageIndex={targetPageIndex}
            activeHighlight={activeHighlight}
            onPageChange={onJumpToPage}
            documentTitle={document?.filename}
          />
        </div>

        {/* RIGHT PANEL: Answer & Evidence Inspector */}
        <div className={`workspace-right-panel ${rightPanelCollapsed ? "collapsed" : ""}`}>
          <div className="panel-header-row right-header">
            <span className="panel-header-title">EVIDENCE & REASONING</span>
            <button
              type="button"
              className="btn-panel-toggle"
              onClick={() => setRightPanelCollapsed(!rightPanelCollapsed)}
              title={rightPanelCollapsed ? "Expand inspector" : "Collapse inspector"}
            >
              {rightPanelCollapsed ? "<<" : ">>"}
            </button>
          </div>

          <div className="panel-scroll-content">
            {/* Query Form right inside workspace */}
            <form className="workspace-query-box" onSubmit={handleQuestionSubmit}>
              <div className="query-field-wrap">
                <input
                  type="text"
                  className="workspace-query-input"
                  placeholder="Ask a question about this report..."
                  value={inputQuestion}
                  onChange={(e) => setInputQuestion(e.target.value)}
                />
                <button
                  type="submit"
                  className="workspace-query-submit"
                  disabled={isLoadingQuestion}
                  title="Ask question"
                >
                  <ArrowRight size={16} />
                </button>
              </div>
            </form>

            {/* Suggestions / Sample Questions */}
            {suggestions.length > 0 && (
              <div className="quick-suggestions-block">
                <div className="suggestions-header">
                  <Sparkles size={12} className="sparkle-icon" />
                  <span>SUGGESTED INQUIRIES</span>
                </div>
                <div className="suggestions-list">
                  {suggestions.slice(0, 3).map((s, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="suggestion-pill"
                      onClick={() => {
                        setInputQuestion(s.question);
                        onAskQuestion(s.question);
                      }}
                    >
                      <CornerDownRight size={11} className="pill-arrow" />
                      <span className="pill-text">{s.label || s.question}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Dominant Answer Section */}
            {isLoadingQuestion ? (
              <div className="inspector-loading-card">
                <div className="spinner" />
                <span className="loading-label">Searching report & verifying evidence...</span>
              </div>
            ) : answerData ? (
              <div className="dominant-answer-card">
                <div className="answer-section-tag">ANSWER</div>

                {/* Dominant Large Headline */}
                <div className="answer-hero-value">
                  {answerData.answer ? (
                    answerData.answer
                  ) : answerData.status === "not_found" ? (
                    <span className="status-refusal">NOT_FOUND</span>
                  ) : (
                    "—"
                  )}
                </div>

                {/* Subtitle / Meaning */}
                <div className="answer-narrative-explanation">
                  {answerData.claims[0]?.text ||
                    (answerData.status === "not_found"
                      ? "The requested statistic was not found in the verified text or tables of this report."
                      : "Direct extraction from report evidence.")}
                </div>

                {/* Truthful Grounding Match Badge */}
                {groundingStatus && (
                  <div className="evidence-match-badge-row">
                    <span className={`match-pill ${groundingStatus.className}`}>
                      <span className={`pill-dot ${groundingStatus.dotColor}`} />
                      <span>{groundingStatus.label}</span>
                    </span>
                  </div>
                )}

                {/* Citations List */}
                {answerData.citations.length > 0 && (
                  <div className="citations-list-group">
                    <div className="citations-group-title">CITATIONS</div>
                    {answerData.citations.map((c, i) => (
                      <div
                        key={i}
                        className="citation-card-clickable"
                        onClick={() => onSelectCitation(c)}
                        title="Click to jump to page and highlight evidence"
                      >
                        <div className="citation-card-left">
                          <FileText size={15} className="citation-icon" />
                          <div className="citation-text-block">
                            <span className="citation-page-text">
                              Page {c.printed_page_number || c.pdf_page_index + 1}
                            </span>
                            <span className="citation-kind-sub">
                              {c.kind ? c.kind.toUpperCase() : "EVIDENCE"}
                            </span>
                          </div>
                        </div>
                        <ChevronRight size={15} className="citation-arrow" />
                      </div>
                    ))}
                  </div>
                )}

                {/* 4 Inspector Tabs */}
                <div className="inspector-tabs-bar">
                  <button
                    type="button"
                    className={`inspector-tab-btn ${inspectorTab === "evidence" ? "active" : ""}`}
                    onClick={() => setInspectorTab("evidence")}
                  >
                    Evidence
                  </button>
                  <button
                    type="button"
                    className={`inspector-tab-btn ${inspectorTab === "method" ? "active" : ""}`}
                    onClick={() => setInspectorTab("method")}
                  >
                    Method
                  </button>
                  <button
                    type="button"
                    className={`inspector-tab-btn ${inspectorTab === "checks" ? "active" : ""}`}
                    onClick={() => setInspectorTab("checks")}
                  >
                    Checks
                  </button>
                  <button
                    type="button"
                    className={`inspector-tab-btn ${inspectorTab === "tables" ? "active" : ""}`}
                    onClick={() => setInspectorTab("tables")}
                  >
                    Tables {evidenceData?.tables?.length ? `(${evidenceData.tables.length})` : ""}
                  </button>
                </div>

                {/* Tab 1: Evidence Structured Facets */}
                {inspectorTab === "evidence" && evidenceFacets && (
                  <div className="tab-pane-evidence">
                    <div className="facets-key-val-grid">
                      <div className="facet-row">
                        <span className="facet-label">Entity</span>
                        <span className="facet-val bold">{evidenceFacets.entity}</span>
                      </div>
                      <div className="facet-row">
                        <span className="facet-label">Metric</span>
                        <span className="facet-val">{evidenceFacets.metric}</span>
                      </div>
                      <div className="facet-row">
                        <span className="facet-label">Value</span>
                        <span className="facet-val bold highlight">{evidenceFacets.value}</span>
                      </div>
                      <div className="facet-row">
                        <span className="facet-label">Period</span>
                        <span className="facet-val">{evidenceFacets.period}</span>
                      </div>
                      <div className="facet-row">
                        <span className="facet-label">Unit</span>
                        <span className="facet-val">{evidenceFacets.unit}</span>
                      </div>
                      <div className="facet-row">
                        <span className="facet-label">Source</span>
                        <span className="facet-val source-val">{evidenceFacets.source}</span>
                      </div>
                    </div>

                    {evidenceFacets.snippet && (
                      <div className="evidence-snippet-box">
                        <div className="snippet-header">VERIFIED EXCERPT</div>
                        <div className="snippet-body">"{evidenceFacets.snippet}"</div>
                      </div>
                    )}

                    {answerData.citations[0] && (
                      <button
                        type="button"
                        className="btn-open-in-document"
                        onClick={() => onSelectCitation(answerData.citations[0])}
                      >
                        <ExternalLink size={13} />
                        <span>
                          Open on Page {answerData.citations[0].printed_page_number || answerData.citations[0].pdf_page_index + 1}
                        </span>
                      </button>
                    )}
                  </div>
                )}

                {/* Tab 2: Method / Deterministic Arithmetic */}
                {inspectorTab === "method" && (
                  <div className="tab-pane-method">
                    {answerData.calculation ? (
                      <div className="arithmetic-audit-block">
                        <div className="audit-header">
                          <Calculator size={15} />
                          <span>DETERMINISTIC ARITHMETIC (ADR-003)</span>
                        </div>
                        <div className="math-row">
                          <span className="math-lbl">Operation:</span>
                          <span className="math-val bold">{answerData.calculation.operation}</span>
                        </div>
                        <div className="math-row">
                          <span className="math-lbl">Formula:</span>
                          <code className="math-code">{answerData.calculation.formula}</code>
                        </div>
                        <div className="math-row">
                          <span className="math-lbl">Evaluated Result:</span>
                          <span className="math-val result-highlight">
                            {answerData.calculation.result} {answerData.calculation.unit || ""}
                          </span>
                        </div>
                        {answerData.calculation.audit_trail && (
                          <div className="audit-trail-note">
                            {answerData.calculation.audit_trail}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="direct-lookup-method">
                        <div className="method-title">Direct Hybrid Retrieval</div>
                        <p className="method-desc">
                          Retrieved via lexical BM25 ranking and semantic vector representations with Reciprocal Rank Fusion (RRF).
                        </p>
                      </div>
                    )}

                    {answerData.classification?.rationale && (
                      <div className="rationale-note">
                        <strong>Classification Rationale:</strong> {answerData.classification.rationale}
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 3: Checks / Grounding Ledger */}
                {inspectorTab === "checks" && (
                  <div className="tab-pane-checks">
                    <div className="checks-title-bar">GROUNDING VERIFICATION LEDGER</div>
                    <div className="checks-list">
                      {answerData.verification_checks.length > 0 ? (
                        answerData.verification_checks.map((chk, idx) => (
                          <div key={idx} className={`check-card ${chk.passed ? "passed" : "failed"}`}>
                            <div className="check-left">
                              {chk.passed ? (
                                <Check size={14} className="check-icon pass" />
                              ) : (
                                <X size={14} className="check-icon fail" />
                              )}
                              <span className="check-name">{chk.name}</span>
                            </div>
                            <span className="check-details">{chk.details}</span>
                          </div>
                        ))
                      ) : (
                        <div className="checks-empty">
                          No automated verification checks returned by API for this query.
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Tab 4: Structured Table Explorer */}
                {inspectorTab === "tables" && (
                  <div className="tab-pane-tables">
                    <TableExplorer
                      tables={evidenceData?.tables || []}
                      onHighlightTable={onHighlightTable}
                    />
                  </div>
                )}
              </div>
            ) : (
              /* Empty State when no question has been asked yet in this report */
              <div className="inspector-empty-state">
                <Search size={32} className="empty-glyph" />
                <div className="empty-title">Ready for Questions</div>
                <p className="empty-subtitle">
                  Ask a question above or choose a suggested inquiry to inspect evidence citations on this report.
                </p>

                {evidenceData && evidenceData.tables.length > 0 && (
                  <button
                    type="button"
                    className="btn-inspect-tables"
                    onClick={() => setInspectorTab("tables")}
                  >
                    <FileSpreadsheet size={14} />
                    <span>Explore {evidenceData.tables.length} Structured Tables</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
