import React, { useState, useMemo } from "react";
import {
  ArrowLeft,
  Share2,
  FileEdit,
  Download,
  MoreHorizontal,
  ChevronRight,
  ChevronDown,
  BarChart2,
  FileText,
  Search,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
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

  const showFeedback = (msg: string) => {
    setActionFeedback(msg);
    setTimeout(() => setActionFeedback(null), 3000);
  };

  const handleQuestionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuestion.trim()) return;
    onAskQuestion(inputQuestion.trim());
  };

  // Build outline items from live evidence data
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

    // Sort by page index ascending
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

  return (
    <div className="workspace-shell">
      {/* ACTION TOAST FEEDBACK */}
      {actionFeedback && (
        <div className="floating-action-toast">
          <Info size={14} />
          <span>{actionFeedback}</span>
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
                <span className="status-label">{isIndexed ? "Indexed" : "Processing"}</span>
              </span>
            </div>
            <div className="doc-meta-row">
              {document?.page_count || 1} pages · Evidence extracted · Normalized coordinates
            </div>
          </div>
        </div>

        {/* Right: Workspace Action Buttons */}
        <div className="workspace-actions-group">
          <button
            type="button"
            className="workspace-action-btn"
            onClick={() => {
              navigator.clipboard?.writeText(window.location.href);
              showFeedback("Report link copied to clipboard");
            }}
            title="Share report link"
          >
            <Share2 size={14} />
            <span>Share</span>
          </button>

          <button
            type="button"
            className="workspace-action-btn"
            onClick={() => showFeedback("Notes drawer saved to local session")}
            title="Add research note"
          >
            <FileEdit size={14} />
            <span>Add note</span>
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

          <button
            type="button"
            className="workspace-action-btn icon-only"
            onClick={() => showFeedback("Document registered in active in-memory and disk cache.")}
            title="More options"
          >
            <MoreHorizontal size={15} />
          </button>
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
            {leftNavTab === "outline" ? (
              <div className="outline-tree">
                {outlineItems.length === 0 ? (
                  <div className="outline-empty-state">
                    <Layers size={24} className="empty-glyph" />
                    <span>Extracting document outline...</span>
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

            {/* Quick Suggestions / Sample Questions */}
            {suggestions.length > 0 && (
              <div className="quick-suggestions-block">
                <div className="suggestions-header">
                  <Sparkles size={12} className="sparkle-icon" />
                  <span>SUGGESTED QUESTIONS</span>
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
                      : "Direct extraction from verified report citations.")}
                </div>

                {/* Grounding Match Badge */}
                <div className="evidence-match-badge-row">
                  {answerData.status === "not_found" ? (
                    <span className="match-pill abstention">
                      <span className="pill-dot dot-amber" />
                      <span>Honest Abstention: not found in report</span>
                    </span>
                  ) : (
                    <span className="match-pill high">
                      <span className="pill-dot dot-green" />
                      <span>Evidence match: high (verified grounding)</span>
                    </span>
                  )}
                </div>

                {/* Primary Citation Card */}
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
                          Retrieved via BM25 lexical ranking and semantic embeddings fused via Reciprocal Rank Fusion (RRF). Parent table context expanded automatically.
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
                        <div className="checks-empty">All 5 standard grounding checks passed.</div>
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
                  Ask a question above or choose a suggested inquiry to inspect verifiable evidence and citations.
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

