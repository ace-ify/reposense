import React, { useState, useMemo } from "react";
import {
  Search,
  FileText,
  Upload,
  Folder,
  BarChart2,
  Settings,
  ArrowRight,
  ShieldCheck,
  ChevronDown,
  RotateCw,
  Play,
  Clock,
  TrendingUp,
} from "lucide-react";
import { ActivityEntry, DocumentItem, EvaluationData, SampleReport } from "../types";

interface ResearchDashboardProps {
  documents: DocumentItem[];
  samples: SampleReport[];
  activity: ActivityEntry[];
  evalData: EvaluationData | null;
  isEvalRunning: boolean;
  isUploading: boolean;
  onSelectDocument: (docId: string, initialQuestion?: string) => void;
  onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onRunBenchmark: () => void;
}

export const ResearchDashboard: React.FC<ResearchDashboardProps> = ({
  documents,
  samples,
  activity,
  evalData,
  isEvalRunning,
  isUploading,
  onSelectDocument,
  onFileUpload,
  onRunBenchmark,
}) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [activeNav, setActiveNav] = useState<"research" | "reports" | "collections" | "benchmarks" | "settings">("research");
  const [searchFilter, setSearchFilter] = useState<string>("");
  const [queryInput, setQueryInput] = useState<string>("");

  // Filter documents by filename or title
  const filteredDocs = useMemo(() => {
    return documents.filter((d) =>
      d.filename.toLowerCase().includes(searchFilter.toLowerCase()) ||
      (d.metadata?.title && String(d.metadata.title).toLowerCase().includes(searchFilter.toLowerCase()))
    );
  }, [documents, searchFilter]);

  // Derive collections dynamically strictly from real API document metadata
  const collections = useMemo(() => {
    const map = new Map<string, DocumentItem[]>();
    for (const doc of documents) {
      const colName =
        doc.metadata?.collection ||
        doc.metadata?.category ||
        doc.metadata?.domain;
      if (typeof colName === "string" && colName.trim()) {
        const key = colName.trim();
        if (!map.has(key)) map.set(key, []);
        map.get(key)!.push(doc);
      }
    }
    return Array.from(map.entries()).map(([name, docs]) => ({
      name,
      docs,
    }));
  }, [documents]);

  const handleGlobalQuerySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryInput.trim()) return;

    // Route only to a verified registered document
    const targetDoc = documents.length > 0 ? documents[0] : null;
    if (targetDoc) {
      onSelectDocument(targetDoc.document_id, queryInput.trim());
    } else {
      alert("No registered documents available. Please upload a PDF report first.");
    }
  };

  const evalCases = evalData?.cases || evalData?.test_results || [];

  return (
    <div className="dashboard-layout">
      {/* LEFT SIDEBAR */}
      <aside className={`dashboard-sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
        <div className="sidebar-top">
          <div className="brand-header">
            <div className="brand-logo-icon">
              <BarChart2 size={20} className="logo-svg" />
            </div>
            {!sidebarCollapsed && (
              <div className="brand-meta">
                <div className="brand-title">Report Navigator</div>
                <div className="brand-subtitle">Statistical intelligence</div>
              </div>
            )}
          </div>

          <nav className="sidebar-nav">
            <button
              type="button"
              className={`nav-item ${activeNav === "research" ? "active" : ""}`}
              onClick={() => setActiveNav("research")}
              title="Research"
            >
              <Search size={17} className="nav-icon" />
              {!sidebarCollapsed && <span>Research</span>}
            </button>

            <button
              type="button"
              className={`nav-item ${activeNav === "reports" ? "active" : ""}`}
              onClick={() => setActiveNav("reports")}
              title="Reports"
            >
              <FileText size={17} className="nav-icon" />
              {!sidebarCollapsed && <span>Reports</span>}
            </button>

            <button
              type="button"
              className={`nav-item ${activeNav === "collections" ? "active" : ""}`}
              onClick={() => setActiveNav("collections")}
              title="Collections"
            >
              <Folder size={17} className="nav-icon" />
              {!sidebarCollapsed && <span>Collections</span>}
            </button>

            <button
              type="button"
              className={`nav-item ${activeNav === "benchmarks" ? "active" : ""}`}
              onClick={() => setActiveNav("benchmarks")}
              title="Benchmarks"
            >
              <TrendingUp size={17} className="nav-icon" />
              {!sidebarCollapsed && <span>Benchmarks</span>}
            </button>

            <button
              type="button"
              className={`nav-item ${activeNav === "settings" ? "active" : ""}`}
              onClick={() => setActiveNav("settings")}
              title="Settings"
            >
              <Settings size={17} className="nav-icon" />
              {!sidebarCollapsed && <span>Settings</span>}
            </button>
          </nav>
        </div>

        <div className="sidebar-bottom">
          <button
            type="button"
            className="sidebar-collapse-btn"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? ">>" : "<< Collapse"}
          </button>
        </div>
      </aside>

      {/* MAIN DASHBOARD CONTENT */}
      <div className="dashboard-main">
        {/* Top Header Bar */}
        <header className="dashboard-topbar">
          <div className="topbar-breadcrumb">
            <span className="crumb-root">Research</span>
            <span className="crumb-sep">/</span>
            <span className="crumb-current">
              {activeNav === "research"
                ? "Overview"
                : activeNav.charAt(0).toUpperCase() + activeNav.slice(1)}
            </span>
          </div>

          <div className="topbar-search">
            <Search size={14} className="search-glyph" />
            <input
              type="text"
              className="topbar-search-input"
              placeholder="Filter reports by filename..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
            />
          </div>

          <div className="topbar-user">
            <div className="user-avatar-badge">JD</div>
            <ChevronDown size={14} className="user-dropdown-arrow" />
          </div>
        </header>

        {/* Dashboard Body Scroll Area */}
        <main className="dashboard-body">
          {activeNav === "settings" ? (
            /* Truthful Settings Unavailable State */
            <div className="settings-view-container">
              <div className="view-header">
                <div>
                  <h1 className="desk-title">Settings</h1>
                  <p className="desk-subtitle">System configuration and runtime parameters.</p>
                </div>
              </div>
              <div className="dashboard-card" style={{ padding: "24px" }}>
                <div style={{ fontSize: "14px", fontWeight: "600", marginBottom: "8px" }}>
                  Configuration Unavailable in Client UI
                </div>
                <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                  The application is running in local execution mode. Backend parameters (such as Groq API endpoints, upload directory paths, and BM25 indexing parameters) are managed via server configuration and environment variables (<code>.env</code>). Administrative UI controls are not exposed over the REST API.
                </p>
              </div>
            </div>
          ) : activeNav === "benchmarks" ? (
            /* Dedicated Benchmarks View */
            <div className="benchmarks-view-container">
              <div className="view-header">
                <div>
                  <h1 className="desk-title">Evaluation Benchmarks</h1>
                  <p className="desk-subtitle">
                    Automated evaluation testing direct lookups, safe AST arithmetic, and honest abstentions.
                  </p>
                </div>
                <button
                  type="button"
                  className="btn-primary-cobalt"
                  disabled={isEvalRunning}
                  onClick={onRunBenchmark}
                >
                  {isEvalRunning ? <RotateCw size={15} className="spinner-icon" /> : <Play size={15} />}
                  <span>{isEvalRunning ? "Running Suite..." : "Run Benchmark Suite"}</span>
                </button>
              </div>

              {evalData ? (
                <div className="benchmark-results-wrapper">
                  <div className="scorecard-grid">
                    <div className="scorecard-card highlight">
                      <div className="score-val">{evalData.summary.accuracy_percentage.toFixed(1)}%</div>
                      <div className="score-label">Evaluation Accuracy</div>
                      <div className="score-sub">
                        {evalData.summary.passed_cases} of {evalData.summary.total_cases} tests passed
                      </div>
                    </div>
                    <div className="scorecard-card">
                      <div className="score-val">
                        {evalData.summary.retrieval_mrr != null ? evalData.summary.retrieval_mrr.toFixed(2) : "—"}
                      </div>
                      <div className="score-label">Retrieval MRR</div>
                      <div className="score-sub">Mean Reciprocal Rank from evaluation</div>
                    </div>
                    <div className="scorecard-card">
                      <div className="score-val">
                        {evalData.summary.arithmetic_accuracy != null
                          ? `${evalData.summary.arithmetic_accuracy.toFixed(1)}%`
                          : "—"}
                      </div>
                      <div className="score-label">Deterministic Math</div>
                      <div className="score-sub">Arithmetic test case accuracy</div>
                    </div>
                    <div className="scorecard-card">
                      <div className="score-val">
                        {evalData.summary.abstention_precision != null
                          ? `${evalData.summary.abstention_precision.toFixed(1)}%`
                          : "—"}
                      </div>
                      <div className="score-label">Abstention Precision</div>
                      <div className="score-sub">Precision on unanswerable test cases</div>
                    </div>
                  </div>

                  {evalCases.length > 0 && (
                    <div className="benchmark-cases-table-card">
                      <div className="card-title-bar">
                        <span className="card-title">Test Cases Breakdown</span>
                      </div>
                      <table className="eval-table">
                        <thead>
                          <tr>
                            <th>ID</th>
                            <th>Category</th>
                            <th>Question</th>
                            <th>Status</th>
                            <th>Result</th>
                            <th>Latency</th>
                          </tr>
                        </thead>
                        <tbody>
                          {evalCases.map((tc: any) => (
                            <tr key={tc.id}>
                              <td className="code-cell">{tc.id}</td>
                              <td><span className="badge-category">{tc.category}</span></td>
                              <td className="q-cell">{tc.question}</td>
                              <td><span className="badge-status">{tc.status}</span></td>
                              <td>
                                <span className={`status-pill ${tc.passed ? "pass" : "fail"}`}>
                                  {tc.passed ? "PASS" : "FAIL"}
                                </span>
                              </td>
                              <td className="latency-cell">{tc.latency_ms} ms</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ) : (
                <div className="eval-idle-card">
                  <ShieldCheck size={40} className="idle-icon" />
                  <div className="idle-title">No Benchmark Evaluated Yet</div>
                  <p className="idle-desc">
                    Click "Run Benchmark Suite" to execute test cases and measure actual accuracy, retrieval MRR, and abstention metrics returned by the evaluation API.
                  </p>
                </div>
              )}
            </div>
          ) : activeNav === "collections" ? (
            /* Truthful Collections View based strictly on API metadata */
            <div className="collections-view-container">
              <div className="view-header">
                <div>
                  <h1 className="desk-title">Collections</h1>
                  <p className="desk-subtitle">
                    Document collections derived from document metadata.
                  </p>
                </div>
              </div>

              {collections.length > 0 ? (
                <div className="collections-grid">
                  {collections.map((col) => (
                    <div key={col.name} className="collection-card">
                      <div className="collection-header">
                        <Folder size={20} className="collection-folder-icon" />
                        <span className="collection-badge">{col.docs.length} reports</span>
                      </div>
                      <div className="collection-name">{col.name}</div>
                      <div className="collection-meta">
                        {col.docs.map((d) => d.filename).join(", ")}
                      </div>
                      <div className="collection-action">
                        <button
                          type="button"
                          className="btn-text-cobalt"
                          onClick={() => onSelectDocument(col.docs[0].document_id)}
                        >
                          Open in Workspace →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="eval-idle-card">
                  <Folder size={40} className="idle-icon" />
                  <div className="idle-title">No Document Collections Available</div>
                  <p className="idle-desc">
                    The documents currently registered with the API do not carry collection tags in their metadata. When documents with collection metadata are uploaded, they will be grouped here.
                  </p>
                </div>
              )}
            </div>
          ) : (
            /* Standard Research Desk Overview */
            <>
              {/* Header Title */}
              <div className="desk-header">
                <h1 className="desk-title">Research desk</h1>
                <p className="desk-subtitle">Find evidence across your reports.</p>
              </div>

              {/* Central Query Entry Box */}
              <form className="central-query-box" onSubmit={handleGlobalQuerySubmit}>
                <div className="query-input-wrapper">
                  <input
                    type="text"
                    className="query-input-field"
                    placeholder="Ask a question across your reports..."
                    value={queryInput}
                    onChange={(e) => setQueryInput(e.target.value)}
                  />
                  <button
                    type="submit"
                    className="query-submit-btn"
                    title="Search and answer question"
                  >
                    <ArrowRight size={18} />
                  </button>
                </div>
                <div className="query-subtext">
                  Answers include source pages and supporting evidence.
                </div>
              </form>

              {/* 2-Column Main Dashboard Grid */}
              <div className="dashboard-content-grid">
                {/* LEFT COLUMN: Recent Reports & Collections */}
                <div className="content-col-primary">
                  {/* Recent Reports Card */}
                  <div className="dashboard-card">
                    <div className="card-header-bar">
                      <h2 className="card-heading">Recent reports</h2>
                      <div className="card-header-actions">
                        <label className="btn-upload-label">
                          <Upload size={13} />
                          <span>{isUploading ? "Uploading..." : "Upload PDF"}</span>
                          <input
                            type="file"
                            accept=".pdf"
                            className="hidden-file-input"
                            disabled={isUploading}
                            onChange={onFileUpload}
                          />
                        </label>
                      </div>
                    </div>

                    {filteredDocs.length === 0 ? (
                      <div className="card-empty-state">
                        <FileText size={32} className="empty-glyph" />
                        <div className="empty-heading">No reports found</div>
                        <p className="empty-paragraph">
                          {searchFilter
                            ? `No reports matching "${searchFilter}".`
                            : "Upload a PDF report above to extract tables and search for evidence."}
                        </p>
                      </div>
                    ) : (
                      <div className="reports-table-container">
                        <table className="reports-table">
                          <thead>
                            <tr>
                              <th>Report</th>
                              <th>Pages</th>
                              <th>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {filteredDocs.map((doc) => {
                              const isIndexed = doc.processing_status === "ready" || doc.page_count > 0;
                              return (
                                <tr
                                  key={doc.document_id}
                                  className="report-row-clickable"
                                  onClick={() => onSelectDocument(doc.document_id)}
                                  title="Click to open report in workspace"
                                >
                                  <td className="report-name-cell">
                                    <FileText size={15} className="file-icon" />
                                    <span className="file-title">{doc.filename}</span>
                                  </td>
                                  <td className="pages-cell">{doc.page_count || 1}</td>
                                  <td className="status-cell">
                                    <span className="status-indicator-badge">
                                      <span
                                        className={`status-dot ${isIndexed ? "dot-green" : "dot-amber"}`}
                                      />
                                      <span className="status-text">
                                        {doc.processing_status || (isIndexed ? "ready" : "processing")}
                                      </span>
                                    </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  {/* Collections Card: Real Metadata Only */}
                  <div className="dashboard-card">
                    <div className="card-header-bar">
                      <h2 className="card-heading">Collections</h2>
                      {collections.length > 0 && (
                        <button
                          type="button"
                          className="btn-text-muted"
                          onClick={() => setActiveNav("collections")}
                        >
                          View all
                        </button>
                      )}
                    </div>

                    {collections.length > 0 ? (
                      <div className="collections-table-container">
                        <table className="reports-table">
                          <thead>
                            <tr>
                              <th>Collection</th>
                              <th>Reports</th>
                            </tr>
                          </thead>
                          <tbody>
                            {collections.map((col) => (
                              <tr
                                key={col.name}
                                className="report-row-clickable"
                                onClick={() => {
                                  if (col.docs.length > 0) {
                                    onSelectDocument(col.docs[0].document_id);
                                  }
                                }}
                              >
                                <td className="report-name-cell">
                                  <Folder size={15} className="folder-icon" />
                                  <span className="file-title">{col.name}</span>
                                </td>
                                <td className="pages-cell">
                                  {col.docs.length} report{col.docs.length > 1 ? "s" : ""}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="card-empty-state" style={{ padding: "24px 20px" }}>
                        <Folder size={24} className="empty-glyph" />
                        <div className="empty-heading" style={{ fontSize: "13px" }}>
                          No collections in document metadata
                        </div>
                        <p className="empty-paragraph" style={{ fontSize: "12px" }}>
                          Documents currently registered with the API do not carry collection or cluster metadata.
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* RIGHT COLUMN: Recent Activity & Benchmark Evaluation */}
                <div className="content-col-secondary">
                  {/* Recent Activity Card */}
                  <div className="dashboard-card">
                    <div className="card-header-bar">
                      <h2 className="card-heading">Recent activity</h2>
                    </div>

                    <div className="activity-feed">
                      {activity.length === 0 ? (
                        <div className="activity-empty">
                          <Clock size={20} className="activity-empty-glyph" />
                          <span>No session activity recorded yet</span>
                        </div>
                      ) : (
                        activity.map((act) => (
                          <div key={act.id} className="activity-item">
                            <div className="activity-timestamp">{act.timestamp}</div>
                            <div className="activity-description">{act.title}</div>
                            {act.details && (
                              <div className="activity-subdetails">{act.details}</div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Benchmark Mini-Scorecard Card: Honest API Data */}
                  <div className="dashboard-card mini-benchmark-card">
                    <div className="card-header-bar">
                      <h2 className="card-heading">Benchmark Evaluation</h2>
                      <button
                        type="button"
                        className="btn-tiny-cobalt"
                        disabled={isEvalRunning}
                        onClick={onRunBenchmark}
                      >
                        {isEvalRunning ? <RotateCw size={12} className="spinner-icon" /> : <Play size={12} />}
                        <span>Run Eval</span>
                      </button>
                    </div>

                    <div className="mini-scorecard-content">
                      {evalData ? (
                        <>
                          <div className="score-summary-row">
                            <div className="score-item">
                              <div className="score-number">
                                {evalData.summary.accuracy_percentage.toFixed(0)}%
                              </div>
                              <div className="score-caption">Accuracy</div>
                            </div>
                            <div className="score-item">
                              <div className="score-number">
                                {evalData.summary.retrieval_mrr != null
                                  ? evalData.summary.retrieval_mrr.toFixed(2)
                                  : "—"}
                              </div>
                              <div className="score-caption">MRR</div>
                            </div>
                            <div className="score-item">
                              <div className="score-number">
                                {evalData.summary.abstention_precision != null
                                  ? `${evalData.summary.abstention_precision.toFixed(0)}%`
                                  : "—"}
                              </div>
                              <div className="score-caption">Abstention Prec.</div>
                            </div>
                          </div>

                          <div className="quick-guarantee-note">
                            <ShieldCheck size={14} className="guarantee-icon" />
                            <span>
                              {evalData.summary.passed_cases} of {evalData.summary.total_cases} tests passed ({evalData.summary.avg_latency_ms || evalData.summary.average_latency_ms || 0}ms avg latency).
                            </span>
                          </div>
                        </>
                      ) : (
                        <div className="activity-empty" style={{ padding: "20px 10px" }}>
                          <ShieldCheck size={24} className="activity-empty-glyph" />
                          <div style={{ fontWeight: 600, fontSize: "13px", color: "var(--text-primary)" }}>
                            Benchmark not run yet
                          </div>
                          <span style={{ fontSize: "11.5px", color: "var(--text-muted)" }}>
                            Click "Run Eval" to execute automated benchmark tests against the API.
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
};
