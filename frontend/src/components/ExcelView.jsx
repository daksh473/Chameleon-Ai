import { useState, useEffect, useCallback, useRef } from "react";
import {
  Upload, Download, FileSpreadsheet, RefreshCw, X, Check,
  AlertCircle, Clock, Trash2, Eye, Copy, ChevronDown, Link
} from "lucide-react";
import "./ExcelView.css";

const API = "http://localhost:8000";

export default function ExcelView() {
  const [activeTab, setActiveTab] = useState("upload");
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [mapping, setMapping] = useState({});
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [exportDropdown, setExportDropdown] = useState(false);
  const [templateDropdown, setTemplateDropdown] = useState(false);
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncUrl, setSyncUrl] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [previewModal, setPreviewModal] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const fetchInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, histRes, syncRes] = await Promise.all([
        fetch(`${API}/excel/stats`).then(r => r.ok ? r.json() : null),
        fetch(`${API}/excel/history`).then(r => r.ok ? r.json() : []),
        fetch(`${API}/excel/sync/status`).then(r => r.ok ? r.json() : null)
      ]);
      setStats(statsRes);
      setHistory(histRes || []);
      setSyncStatus(syncRes);
    } catch (e) {
      console.error(e);
      setError("Failed to load Excel integration data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  // ── Upload ──
  const handleFile = async (file) => {
    if (!file) return;
    setUploading(true);
    setUploadResult(null);
    setImportResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API}/excel/upload`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setUploadResult(data);
      setMapping(data.mapping || {});
    } catch (e) {
      setImportResult({ error: true, message: e.message });
    }
    setUploading(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer?.files?.[0];
    handleFile(file);
  };

  const onDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = () => setDragging(false);

  // ── Import ──
  const handleImport = async (type) => {
    if (!uploadResult?.file_id) return;
    setImporting(true);
    setImportResult(null);
    try {
      const res = await fetch(`${API}/excel/import/${type}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: uploadResult.file_id, column_mapping: mapping })
      });
      const data = await res.json();
      setImportResult({ success: true, ...data });
      fetchInitialData();
    } catch (e) {
      setImportResult({ error: true, message: e.message });
    }
    setImporting(false);
  };

  const handleAutoImport = async () => {
    if (!uploadResult) return;
    setImporting(true);
    setImportResult(null);
    const formData = new FormData();
    // Re-upload for auto import
    try {
      const res = await fetch(`${API}/excel/import/${uploadResult.detected_type}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: uploadResult.file_id, column_mapping: mapping })
      });
      const data = await res.json();
      setImportResult({ success: true, ...data });
      fetchInitialData();
    } catch (e) {
      setImportResult({ error: true, message: e.message });
    }
    setImporting(false);
  };

  // ── Export ──
  const handleExport = (type) => {
    setExportDropdown(false);
    window.open(`${API}/excel/export/${type}`, "_blank");
  };

  const handleTemplate = (type) => {
    setTemplateDropdown(false);
    window.open(`${API}/excel/template/${type}`, "_blank");
  };

  // ── Preview ──
  const openPreview = async (type, title) => {
    setPreviewModal({ type, title });
    setLoadingPreview(true);
    try {
      const res = await fetch(`${API}/excel/export/preview/${type}`);
      const data = await res.json();
      setPreviewData(data);
    } catch (e) {
      setPreviewData(null);
    }
    setLoadingPreview(false);
  };

  const copyCSV = () => {
    if (!previewData?.rows?.length) return;
    const headers = previewData.columns.join(",");
    const rows = previewData.rows.map(r => previewData.columns.map(c => r[c] ?? "").join(",")).join("\n");
    navigator.clipboard.writeText(headers + "\n" + rows);
  };

  // ── Undo ──
  const handleUndo = async (importId) => {
    try {
      await fetch(`${API}/excel/undo/${importId}`, { method: "POST" });
      fetchInitialData();
    } catch (e) { console.error(e); }
  };

  // ── Sync ──
  const handleSync = async () => {
    if (!syncUrl.trim()) return;
    setSyncing(true);
    try {
      const res = await fetch(`${API}/excel/sync/crm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ google_sheet_url: syncUrl })
      });
      await res.json();
      fetchInitialData();
    } catch (e) { console.error(e); }
    setSyncing(false);
  };

  // ── Mapping field options ──
  const fieldOptions = {
    customers: ["name", "email", "phone", "company"],
    conversations: ["message", "sentiment", "emotion", "action"],
    tickets: ["customer_name", "issue", "priority", "status"],
    deals: ["title", "value", "stage", "probability", "expected_close"]
  };

  const exportCards = [
    { type: "customers", icon: "📊", title: "Customer Report", key: "customers" },
    { type: "conversations", icon: "💬", title: "Conversation Log", key: "conversations" },
    { type: "tickets", icon: "🎫", title: "Ticket Report", key: "tickets" },
    { type: "analytics", icon: "📈", title: "Analytics Report", key: null },
    { type: "full-report", icon: "📋", title: "Full Company Report", key: null }
  ];

  if (loading) return <div className="excel-view p-8 text-gray-400">Loading Excel Integration...</div>;
  if (error) return <div className="p-8 text-red-400">Error: {error}</div>;

  return (
    <div className="excel-view">
      {/* ── Header ── */}
      <div className="excel-view-header">
        <h2><FileSpreadsheet size={22} /> Excel Integration</h2>
        <div className="excel-header-actions">
          <button className="excel-btn excel-btn-primary" onClick={() => fileInputRef.current?.click()}>
            <Upload size={14} /> Upload Excel
          </button>
          <input ref={fileInputRef} type="file" accept=".xlsx,.xls,.csv" hidden onChange={e => handleFile(e.target.files?.[0])} />

          <div className="excel-dropdown-wrapper">
            <button className="excel-btn" onClick={() => { setExportDropdown(!exportDropdown); setTemplateDropdown(false); }}>
              <Download size={14} /> Export <ChevronDown size={12} />
            </button>
            {exportDropdown && (
              <div className="excel-dropdown">
                <button onClick={() => handleExport("customers")}>📊 Customers</button>
                <button onClick={() => handleExport("conversations")}>💬 Conversations</button>
                <button onClick={() => handleExport("tickets")}>🎫 Tickets</button>
                <button onClick={() => handleExport("analytics")}>📈 Analytics</button>
                <button onClick={() => handleExport("full-report")}>📋 Full Report</button>
              </div>
            )}
          </div>

          <div className="excel-dropdown-wrapper">
            <button className="excel-btn" onClick={() => { setTemplateDropdown(!templateDropdown); setExportDropdown(false); }}>
              <FileSpreadsheet size={14} /> Templates <ChevronDown size={12} />
            </button>
            {templateDropdown && (
              <div className="excel-dropdown">
                <button onClick={() => handleTemplate("customers")}>Customer Template</button>
                <button onClick={() => handleTemplate("tickets")}>Ticket Template</button>
                <button onClick={() => handleTemplate("conversations")}>Conversation Template</button>
                <button onClick={() => handleTemplate("deals")}>Deal Template</button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Tab Bar ── */}
      <div className="excel-tab-bar">
        <button className={`excel-tab ${activeTab === "upload" ? "active" : ""}`} onClick={() => setActiveTab("upload")}>
          <Upload size={14} /> Upload & Import
        </button>
        <button className={`excel-tab ${activeTab === "export" ? "active" : ""}`} onClick={() => setActiveTab("export")}>
          <Download size={14} /> Export
        </button>
        <button className={`excel-tab ${activeTab === "history" ? "active" : ""}`} onClick={() => setActiveTab("history")}>
          <Clock size={14} /> Import History
        </button>
        <button className={`excel-tab ${activeTab === "sync" ? "active" : ""}`} onClick={() => setActiveTab("sync")}>
          <RefreshCw size={14} /> Live Sync
        </button>
      </div>

      {/* ── Result Banner ── */}
      {importResult && (
        <div className={`excel-result-banner ${importResult.error ? "error" : "success"}`}>
          {importResult.error ? <AlertCircle size={18} /> : <Check size={18} />}
          <p>
            {importResult.error
              ? importResult.message
              : `Successfully imported ${importResult.imported || 0} rows. ${importResult.skipped ? `Skipped: ${importResult.skipped}.` : ""} ${importResult.errors ? `Errors: ${importResult.errors}.` : ""} ${importResult.analyzed ? `Analyzed: ${importResult.analyzed}.` : ""} ${importResult.tickets_created ? `Tickets created: ${importResult.tickets_created}.` : ""}`
            }
          </p>
          <button className="excel-modal-close" onClick={() => setImportResult(null)}><X size={14} /></button>
        </div>
      )}

      {/* ══════ UPLOAD TAB ══════ */}
      {activeTab === "upload" && (
        <>
          {/* Drop Zone */}
          {!uploadResult && (
            <div
              className={`excel-upload-zone ${dragging ? "dragging" : ""}`}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploading ? (
                <div className="excel-loading">
                  <div className="excel-spinner" />
                  <span>Parsing file…</span>
                </div>
              ) : (
                <>
                  <div className="upload-icon-wrapper">
                    <Upload size={28} color="#30A46C" />
                  </div>
                  <h3>Drag & drop your Excel file here or click to browse</h3>
                  <p>Import customers, conversations, tickets, or deals</p>
                  <div className="upload-formats">
                    <span className="format-badge">.XLSX</span>
                    <span className="format-badge">.XLS</span>
                    <span className="format-badge">.CSV</span>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Upload Result */}
          {uploadResult && (
            <div className="excel-upload-result">
              <div className="upload-result-header">
                <h3>
                  <FileSpreadsheet size={18} />
                  {uploadResult.filename}
                </h3>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <span className="detected-badge">
                    <Check size={12} /> {uploadResult.detected_type}
                  </span>
                  <button className="excel-modal-close" onClick={() => { setUploadResult(null); setMapping({}); }}>
                    <X size={16} />
                  </button>
                </div>
              </div>

              <div className="upload-stats">
                <div className="upload-stat">Total Rows: <strong>{uploadResult.total_rows}</strong></div>
                <div className="upload-stat">Columns: <strong>{uploadResult.columns?.length}</strong></div>
                <div className="upload-stat">Detected: <strong>{uploadResult.detected_type}</strong></div>
              </div>

              {/* Preview Table */}
              {uploadResult.preview?.length > 0 && (
                <div className="excel-table-wrapper">
                  <table className="excel-table">
                    <thead>
                      <tr>
                        {uploadResult.columns.map((col, i) => <th key={i}>{col}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {uploadResult.preview.map((row, ri) => (
                        <tr key={ri}>
                          {uploadResult.columns.map((col, ci) => (
                            <td key={ci}>{String(row[col] ?? "")}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Column Mapping */}
              {uploadResult.detected_type !== "unknown" && (
                <div className="excel-mapping-section">
                  <h4>Column Mapping</h4>
                  <div className="mapping-grid">
                    {uploadResult.columns.map((col, i) => (
                      <div className="mapping-item" key={i}>
                        <label>{col}</label>
                        <select
                          value={mapping[col] || ""}
                          onChange={e => setMapping(prev => ({ ...prev, [col]: e.target.value }))}
                        >
                          <option value="">— skip —</option>
                          {(fieldOptions[uploadResult.detected_type] || []).map(f => (
                            <option key={f} value={f}>{f}</option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                  <div className="mapping-actions">
                    <button
                      className="excel-btn excel-btn-primary"
                      onClick={() => handleImport(uploadResult.detected_type)}
                      disabled={importing}
                    >
                      {importing ? <>Importing…</> : <><Check size={14} /> Import Now</>}
                    </button>
                    <button
                      className="excel-btn"
                      onClick={handleAutoImport}
                      disabled={importing}
                    >
                      Import with AI Auto-mapping
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ══════ EXPORT TAB ══════ */}
      {activeTab === "export" && (
        <>
          <h3 className="excel-section-title"><Download size={16} /> Quick Export</h3>
          <div className="excel-export-grid">
            {exportCards.map(card => (
              <div
                key={card.type}
                className="export-card"
                onClick={() => openPreview(card.key || card.type, card.title)}
              >
                <div className="export-card-icon">{card.icon}</div>
                <h4>{card.title}</h4>
                <div className="export-card-meta">
                  {card.key && stats && (
                    <span className="row-count">{stats[card.key] || 0} rows</span>
                  )}
                  {!card.key && <span className="row-count">Multi-sheet report</span>}
                  <span>Downloads as .xlsx</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ══════ HISTORY TAB ══════ */}
      {activeTab === "history" && (
        <div className="excel-history-section">
          <h3><Clock size={16} /> Import History</h3>
          {history.length === 0 ? (
            <div className="history-empty">No imports yet. Upload an Excel file to get started.</div>
          ) : (
            history.map(item => (
              <div className="history-item" key={item.id}>
                <div className="history-item-info">
                  <div className="history-item-icon"><FileSpreadsheet size={16} /></div>
                  <div className="history-item-details">
                    <h4>{item.filename}</h4>
                    <p>{item.detected_type} • {item.imported} imported, {item.skipped} skipped • {new Date(item.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <div className="history-item-meta">
                  <span className={`history-badge ${item.status}`}>{item.status}</span>
                  {item.status === "completed" && (
                    <button className="excel-btn excel-btn-danger" onClick={() => handleUndo(item.id)}>
                      <Trash2 size={13} /> Undo
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* ══════ SYNC TAB ══════ */}
      {activeTab === "sync" && (
        <div className="excel-sync-panel">
          <div className="sync-header">
            <h3><RefreshCw size={16} /> Live Sync</h3>
            <div className="sync-status">
              <span className={`sync-dot ${syncStatus?.status === "connected" ? "connected" : ""}`} />
              <span style={{ color: syncStatus?.status === "connected" ? "#30A46C" : "#888" }}>
                {syncStatus?.status === "connected" ? "Connected" : "Disconnected"}
              </span>
            </div>
          </div>
          {syncStatus?.last_synced && (
            <div className="sync-info">
              <div className="sync-info-item">Last synced: <strong>{new Date(syncStatus.last_synced).toLocaleString()}</strong></div>
              <div className="sync-info-item">Type: <strong>{syncStatus.sync_type || "N/A"}</strong></div>
            </div>
          )}
          <div className="sync-input-row">
            <input
              className="sync-input"
              placeholder="Paste Google Sheets URL…"
              value={syncUrl}
              onChange={e => setSyncUrl(e.target.value)}
            />
            <button className="excel-btn excel-btn-primary" onClick={handleSync} disabled={syncing || !syncUrl.trim()}>
              {syncing ? <RefreshCw size={14} className="excel-spinner" /> : <Link size={14} />}
              {syncing ? "Syncing…" : "Connect"}
            </button>
          </div>
        </div>
      )}

      {/* ══════ PREVIEW MODAL ══════ */}
      {previewModal && (
        <div className="excel-modal-overlay" onClick={() => { setPreviewModal(null); setPreviewData(null); }}>
          <div className="excel-modal" onClick={e => e.stopPropagation()}>
            <div className="excel-modal-header">
              <h3><Eye size={16} /> {previewModal.title} Preview</h3>
              <div className="excel-modal-actions">
                <button className="excel-btn" onClick={copyCSV}><Copy size={13} /> Copy CSV</button>
                <button className="excel-btn excel-btn-primary" onClick={() => handleExport(previewModal.type)}>
                  <Download size={13} /> Download
                </button>
                <button className="excel-modal-close" onClick={() => { setPreviewModal(null); setPreviewData(null); }}>
                  <X size={16} />
                </button>
              </div>
            </div>
            <div className="excel-modal-body">
              {loadingPreview ? (
                <div className="excel-loading"><div className="excel-spinner" /><span>Loading preview…</span></div>
              ) : previewData?.rows?.length > 0 ? (
                <div className="excel-table-wrapper">
                  <table className="excel-table">
                    <thead>
                      <tr>{previewData.columns.map((col, i) => <th key={i}>{col}</th>)}</tr>
                    </thead>
                    <tbody>
                      {previewData.rows.map((row, ri) => (
                        <tr key={ri}>
                          {previewData.columns.map((col, ci) => (
                            <td key={ci}>{String(row[col] ?? "")}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="history-empty">No data available for preview.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
