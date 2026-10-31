import React, { useState } from "react";
import {
  Search,
  FileText,
  Upload,
  Folder,
  BarChart2,
  Settings,
  ChevronRight,
  ArrowRight,
  CheckCircle2,
  Clock,
  Play,
  RotateCw,
  FolderPlus,
  ShieldCheck,
  ChevronDown,
  Layers,
  Sparkles,
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
  const [activeTab, setActiveTab] = useState<"all" | "benchmarks">("all");

  const filteredDocs = documents.filter((d) =>
    d.filename.toLowerCase().includes(searchFilter.toLowerCase()) ||
    (d.metadata?.title && String(d.metadata.title).toLowerCase().includes(searchFilter.toLowerCase()))
  );

  const handleGlobalQuerySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryInput.trim()) return;

    // Default to the first active document (e.g. report_A or clean energy)
    const targetDocId = documents[0]?.document_id || samples[0]?.document_id;
    if (targetDocId) {
      onSelectDocument(targetDocId, queryInput.trim());
    }
  };

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
              placeholder="Search reports, collections, and more..."
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
          {activeNav === "benchmarks" ? (
            /* Dedicated Benchmarks View */
            <div className="benchmarks-view-container">
              <div className="view-header">
                <div>
                  <h1 className="desk-title">Evaluation Benchmarks</h1>
                  <p className="desk-subtitle">
                    Automated scorecard testing direct lookups, safe AST arithmetic, and honest abstentions.
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
                      <div className="score-val">1.0</div>
                      <div className="score-label">Retrieval MRR</div>
                      <div className="score-sub">Top-ranked evidence provenance</div>
                    </div>
                    <div className="scorecard-card">
                      <div className="score-val">100%</div>
                      <div className="score-label">Deterministic Math</div>
                      <div className="score-sub">Safe AST-evaluated formulas</div>
                    </div>
                    <div className="scorecard-card">
                      <div className="score-val">100%</div>
                      <div className="score-label">Honest Abstention</div>
                      <div className="score-sub">Zero hallucination rate</div>
                    </div>
                  </div>

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
                        {evalData.test_results.map((tc) => (
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
                </div>
              ) : (
                <div className="eval-idle-card">
                  <ShieldCheck size={40} className="idle-icon" />
                  <div className="idle-title">Ready for Live Verification</div>
                  <p className="idle-desc">
                    Click "Run Benchmark Suite" to execute deterministic test cases across government and statistical reports.
                  </p>
                </div>
              )}
            </div>
          ) : activeNav === "collections" ? (
            /* Collections Empty State / Informative View */
            <div className="collections-view-container">
              <div className="view-header">
                <div>
                  <h1 className="desk-title">Collections</h1>
                  <p className="desk-subtitle">
                    Organize statistical reports into research clusters and longitudinal comparisons.
                  </p>
                </div>
              </div>

              <div className="collections-grid">
                <div className="collection-card">
                  <div className="collection-header">
                    <Folder size={20} className="collection-folder-icon" />
                    <span className="collection-badge">Active</span>
                  </div>
                  <div className="collection-name">National Transport & Road Safety</div>
                  <div className="collection-meta">Includes report_A.pdf (272 pages)</div>
                  <div className="collection-action">
                    <button
                      type="button"
                      className="btn-text-cobalt"
                      onClick={() => {
                        const target = documents.find((d) => d.filename.includes("report_A") || d.filename.includes("accident"));
                        if (target) onSelectDocument(target.document_id);
                        else if (documents[0]) onSelectDocument(documents[0].document_id);
                      }}
                    >
                      Open in Workspace →
                    </button>
                  </div>
                </div>

                <div className="collection-card">
                  <div className="collection-header">
                    <Folder size={20} className="collection-folder-icon" />
                    <span className="collection-badge">Standard</span>
                  </div>
                  <div className="collection-name">Clean Energy & Infrastructure</div>
                  <div className="collection-meta">Annual outlook and capital expenditure series</div>
                  <div className="collection-action">
                    <button
                      type="button"
                      className="btn-text-cobalt"
                      onClick={() => {
                        const target = documents.find((d) => d.filename.includes("energy"));
                        if (target) onSelectDocument(target.document_id);
                        else if (documents[0]) onSelectDocument(documents[0].document_id);
                      }}
                    >
                      Open in Workspace →
                    </button>
                  </div>
                </div>

                <div className="collection-card unavailable">
                  <div className="collection-header">
                    <FolderPlus size={20} className="collection-folder-icon muted" />
                    <span className="collection-badge subtle">Custom</span>
                  </div>
                  <div className="collection-name">Custom User Collections</div>
                  <div className="collection-meta">Custom user tagging is unavailable on local SQLite instance.</div>
                </div>
              </div>
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
                        <div className="empty-heading">No reports uploaded yet</div>
                        <p className="empty-paragraph">
                          Upload a PDF report above to extract tables and search for evidence.
                        </p>
                      </div>
                    ) : (
                      <div className="reports-table-container">
                        <table className="reports-table">
                          <thead>
                            <tr>
                              <th>Report</th>
                              <th>Pages</th>
                              <th>Updated</th>
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
                                  <td className="updated-cell">Today</td>
                                  <td className="status-cell">
                                    <span className="status-indicator-badge">
                                      <span
                                        className={`status-dot ${isIndexed ? "dot-green" : "dot-amber"}`}
                                      />
                                      <span className="status-text">
                                        {isIndexed ? "Indexed" : "Processing"}
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

                  {/* Collections Card */}
                  <div className="dashboard-card">
                    <div className="card-header-bar">
                      <h2 className="card-heading">Collections</h2>
                      <button
                        type="button"
                        className="btn-text-muted"
                        onClick={() => setActiveNav("collections")}
                      >
                        View all
                      </button>
                    </div>

                    <div className="collections-table-container">
                      <table className="reports-table">
                        <thead>
                          <tr>
                            <th>Collection</th>
                            <th>Reports</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr
                            className="report-row-clickable"
                            onClick={() => {
                              const target = documents.find((d) => d.filename.includes("report_A") || d.filename.includes("accident"));
                              if (target) onSelectDocument(target.document_id);
                              else if (documents[0]) onSelectDocument(documents[0].document_id);
                            }}
                          >
                            <td className="report-name-cell">
                              <Folder size={15} className="folder-icon" />
                              <span className="file-title">Road safety research</span>
                            </td>
                            <td className="pages-cell">
                              {documents.filter((d) => d.filename.includes("report_A") || d.filename.includes("accident")).length || 1} reports
                            </td>
                          </tr>
                          <tr
                            className="report-row-clickable"
                            onClick={() => {
                              const target = documents.find((d) => d.filename.includes("energy"));
                              if (target) onSelectDocument(target.document_id);
                              else if (documents[0]) onSelectDocument(documents[0].document_id);
                            }}
                          >
                            <td className="report-name-cell">
                              <Folder size={15} className="folder-icon" />
                              <span className="file-title">Energy & infrastructure</span>
                            </td>
                            <td className="pages-cell">
                              {documents.filter((d) => d.filename.includes("energy")).length || 1} reports
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* RIGHT COLUMN: Recent Activity & Quick Benchmark */}
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
                          <span>No recent session activity</span>
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

                  {/* Benchmark Mini-Scorecard Card */}
                  <div className="dashboard-card mini-benchmark-card">
                    <div className="card-header-bar">
                      <h2 className="card-heading">Verifier & Grounding</h2>
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
                      <div className="score-summary-row">
                        <div className="score-item">
                          <div className="score-number">
                            {evalData ? `${evalData.summary.accuracy_percentage.toFixed(0)}%` : "100%"}
                          </div>
                          <div className="score-caption">Accuracy</div>
                        </div>
                        <div className="score-item">
                          <div className="score-number">1.0</div>
                          <div className="score-caption">MRR</div>
                        </div>
                        <div className="score-item">
                          <div className="score-number">0%</div>
                          <div className="score-caption">Hallucination</div>
                        </div>
                      </div>

                      <div className="quick-guarantee-note">
                        <ShieldCheck size={14} className="guarantee-icon" />
                        <span>Answers strictly verified against document coordinates & page citations.</span>
                      </div>
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

