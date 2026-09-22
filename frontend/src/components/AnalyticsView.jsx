import { useState, useEffect } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, BarChart, Bar, LineChart, Line
} from "recharts";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  RefreshCw,
  Camera,
  CheckCircle,
  AlertTriangle,
  DollarSign,
  Package,
  CheckSquare,
  Users,
  Headset,
  Sparkles,
  Zap,
} from "lucide-react";
import "./AnalyticsView.css";

const API = "http://localhost:8000/analytics";

const EMOTION_COLORS = {
  angry: "#ff3a5c",
  frustrated: "#f59e0b",
  neutral: "#64748b",
  happy: "#10b981",
  grateful: "#34d399",
  curious: "#8b5cf6",
  uninterested: "#6b7280",
};

const ACTION_COLORS = { ESCALATE: "#ef4444", NORMAL: "#6b7280", UPSELL: "#10b981" };

export default function AnalyticsView() {
  const [activeTab, setActiveTab] = useState("executive"); // 'executive' | 'snapshots' | 'support_ai'
  const [execData, setExecData] = useState(null);
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState(null);

  // Conversational intelligence state (maintained for full depth)
  const [convOverview, setConvOverview] = useState(null);
  const [sentimentTrendData, setSentimentTrendData] = useState([]);
  const [emotionData, setEmotionData] = useState([]);
  const [actionData, setActionData] = useState([]);
  const [hourlyData, setHourlyData] = useState([]);
  const [topIssues, setTopIssues] = useState([]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      // 1. BMS Multi-tenant executive endpoints
      const [execRes, snapRes] = await Promise.all([
        fetch(`${API}/executive-dashboard`).then((r) => (r.ok ? r.json() : null)),
        fetch(`${API}/snapshots?days=14`).then((r) => (r.ok ? r.json() : [])),
      ]);
      setExecData(execRes);
      setSnapshots(Array.isArray(snapRes) ? snapRes : []);

      // 2. Conversational support intelligence endpoints
      const [ovRes, stRes, emRes, acRes, hrRes, tiRes] = await Promise.all([
        fetch(`${API}/overview`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch(`${API}/sentiment-trend`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
        fetch(`${API}/emotion-breakdown`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
        fetch(`${API}/action-distribution`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
        fetch(`${API}/hourly-activity`).then((r) => (r.ok ? r.json() : [])).catch(() => []),
        fetch(`${API}/top-issues`, { method: "POST" }).then((r) => (r.ok ? r.json() : [])).catch(() => []),
      ]);

      setConvOverview(ovRes);
      setSentimentTrendData(Array.isArray(stRes) ? stRes : []);
      setEmotionData(Array.isArray(emRes) ? emRes : []);
      setActionData(Array.isArray(acRes) ? acRes : []);
      setHourlyData(Array.isArray(hrRes) ? hrRes : []);
      setTopIssues(Array.isArray(tiRes) ? tiRes : []);
    } catch (err) {
      console.error("Analytics fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleCaptureSnapshot = async () => {
    try {
      const res = await fetch(`${API}/snapshots/generate`, { method: "POST" });
      if (res.ok) {
        showToast("Daily snapshot captured successfully!");
        fetchAnalytics();
      }
    } catch (e) {
      showToast("Error capturing snapshot.");
    }
  };

  const healthScore = execData?.health_score ?? 70;
  const healthTrend = execData?.health_trend ?? "stable";

  return (
    <div className="analytics-container">
      {/* ── Header ── */}
      <div className="analytics-header-bms">
        <div className="analytics-title-group">
          <h1>
            <BarChart3 size={24} color="#10b981" />
            Executive BMS Analytics & Intelligence
          </h1>
          <p>
            Unified multi-module intelligence: CRM pipeline velocity, support sentiment, billing receivables, inventory asset valuations, and team collaboration.
          </p>
        </div>

        <div className="analytics-top-actions">
          <button
            className="btn-secondary"
            onClick={handleCaptureSnapshot}
            title="Record today's snapshot in database"
          >
            <Camera size={14} color="#10b981" />
            Capture Snapshot
          </button>
          <button className="btn-secondary" onClick={fetchAnalytics} title="Refresh data">
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Sub Tabs ── */}
      <div className="analytics-subtabs">
        <button
          className={`analytics-subtab-btn ${activeTab === "executive" ? "active" : ""}`}
          onClick={() => setActiveTab("executive")}
        >
          <Activity size={15} />
          Executive BMS Overview
        </button>
        <button
          className={`analytics-subtab-btn ${activeTab === "snapshots" ? "active" : ""}`}
          onClick={() => setActiveTab("snapshots")}
        >
          <TrendingUp size={15} />
          Historical Snapshots & Trends ({snapshots.length})
        </button>
        <button
          className={`analytics-subtab-btn ${activeTab === "support_ai" ? "active" : ""}`}
          onClick={() => setActiveTab("support_ai")}
        >
          <Sparkles size={15} />
          Support & Conversational AI
        </button>
      </div>

      {/* ════════ TAB 1: EXECUTIVE BMS OVERVIEW ════════ */}
      {activeTab === "executive" && (
        <>
          {/* Top Hero: Health Score + AI Insights */}
          <div className="executive-hero-grid">
            <div className="health-score-card">
              <div className="health-score-title">Business Health Score</div>
              <div className="health-score-circle">
                <span className="health-score-num">{healthScore}</span>
                <span className="health-score-sub">/ 100</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                {healthTrend === "improving" ? (
                  <TrendingUp size={16} color="#10b981" />
                ) : healthTrend === "declining" ? (
                  <TrendingDown size={16} color="#ef4444" />
                ) : (
                  <Minus size={16} color="#f59e0b" />
                )}
                <span style={{ fontSize: 12, fontWeight: 700, color: "#ffffff", textTransform: "uppercase" }}>
                  Status: {healthTrend}
                </span>
              </div>
            </div>

            <div className="insights-card">
              <div className="insights-card-title">
                <Zap size={16} color="#10b981" />
                Executive Automated Insights
              </div>
              <div className="insights-list">
                {(execData?.insights || [
                  "All BMS services connected and tracking active multi-tenant telemetry.",
                  "Receivables and inventory stocks operating within normal parameters.",
                ]).map((ins, i) => (
                  <div key={i} className="insight-item">
                    <CheckCircle size={15} color="#10b981" style={{ flexShrink: 0, marginTop: 2 }} />
                    <span>{ins}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Cross-Module KPI Cards */}
          <div className="bms-kpi-grid">
            <div className="bms-kpi-card">
              <div className="bms-kpi-top">
                <span className="bms-kpi-label">Lifetime Revenue</span>
                <span className="bms-kpi-module-tag">Billing</span>
              </div>
              <span className="bms-kpi-value emerald">
                ${(execData?.summary?.total_revenue ?? 0).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
              <span style={{ fontSize: 11, color: "#64748b" }}>
                {execData?.modules?.billing?.paid_invoices ?? 0} paid invoice(s)
              </span>
            </div>

            <div className="bms-kpi-card">
              <div className="bms-kpi-top">
                <span className="bms-kpi-label">Pipeline Deal Value</span>
                <span className="bms-kpi-module-tag">CRM</span>
              </div>
              <span className="bms-kpi-value">
                ${(execData?.summary?.pipeline_value ?? 0).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
              <span style={{ fontSize: 11, color: "#64748b" }}>
                {execData?.modules?.crm?.total_leads ?? 0} active lead(s)
              </span>
            </div>

            <div className="bms-kpi-card">
              <div className="bms-kpi-top">
                <span className="bms-kpi-label">Open Support Tickets</span>
                <span className="bms-kpi-module-tag">Support</span>
              </div>
              <span className="bms-kpi-value" style={{ color: (execData?.summary?.open_tickets ?? 0) > 3 ? "#ef4444" : "#ffffff" }}>
                {execData?.summary?.open_tickets ?? 0}
              </span>
              <span style={{ fontSize: 11, color: "#64748b" }}>
                Avg Sentiment: {execData?.modules?.support?.average_sentiment ?? 0.5}
              </span>
            </div>

            <div className="bms-kpi-card">
              <div className="bms-kpi-top">
                <span className="bms-kpi-label">Inventory Valuation</span>
                <span className="bms-kpi-module-tag">Inventory</span>
              </div>
              <span className="bms-kpi-value">
                ${(execData?.summary?.inventory_valuation ?? 0).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
              <span style={{ fontSize: 11, color: "#64748b" }}>
                {execData?.summary?.active_products ?? 0} product catalog items
              </span>
            </div>

            <div className="bms-kpi-card">
              <div className="bms-kpi-top">
                <span className="bms-kpi-label">Task Completion Rate</span>
                <span className="bms-kpi-module-tag">Tasks</span>
              </div>
              <span className="bms-kpi-value emerald">
                {execData?.summary?.task_completion_rate ?? 0}%
              </span>
              <span style={{ fontSize: 11, color: "#64748b" }}>
                {execData?.modules?.tasks?.total ?? 0} internal task(s)
              </span>
            </div>
          </div>

          {/* Module Health Matrix Grid */}
          <div className="modules-matrix-grid">
            {/* CRM Module Card */}
            <div className="module-matrix-card">
              <div className="module-matrix-header">
                <span className="module-matrix-title">
                  <Users size={16} color="#10b981" /> CRM Pipeline
                </span>
                <span className="status-pill status-fulfilled">Active</span>
              </div>
              <div className="module-matrix-stats">
                <div className="matrix-stat-item">
                  <span className="matrix-stat-lbl">Customers</span>
                  <span className="matrix-stat-val">{execData?.modules?.crm?.total_customers ?? 0}</span>
                </div>
                <div className="matrix-stat-item">
                  <span className="matrix-stat-lbl">Won Deals</span>
                  <span className="matrix-stat-val">${(execData?.modules?.crm?.won_deals_value ?? 0).toLocaleString()}</span>
                </div>
              </div>
            </div>

            {/* Support Module Card */}
            <div className="module-matrix-card">
              <div className="module-matrix-header">
                <span className="module-matrix-title">
                  <Headset size={16} color="#10b981" /> Support & Caspian
                </span>
                <span className="status-pill status-fulfilled">Monitoring</span>
              </div>
              <div className="module-matrix-stats">
                <div className="matrix-stat-item">
                  <span className="matrix-stat-lbl">Resolved</span>
                  <span className="matrix-stat-val">{execData?.modules?.support?.resolved ?? 0}</span>
                </div>
                <div className="matrix-stat-item">
                  <span className="matrix-stat-lbl">Escalations</span>
                  <span className="matrix-stat-val" style={{ color: (execData?.modules?.support?.escalated ?? 0) > 0 ? "#ef4444" : "#ffffff" }}>
                    {execData?.modules?.support?.escalated ?? 0}
                  </span>
                </div>
              </div>
            </div>

            {/* Billing Module Card */}
            <div className="module-matrix-card">
              <div className="module-matrix-header">
                <span className="module-matrix-title">
                  <DollarSign size={16} color="#10b981" /> Billing & Invoices
                </span>
                <span className="status-pill status-fulfilled">Automated</span>
              </div>
              <div className="module-matrix-stats">
                <div className="matrix-stat-item">
                  <span className="matrix-stat-lbl">Paid Invoices</span>
                  <span className="matrix-stat-val">{execData?.modules?.billing?.paid_invoices ?? 0}</span>
                </div>
                <div className="matrix-stat-item">
                  <span className="matrix-stat-lbl">Overdue Receivables</span>
                  <span className="matrix-stat-val" style={{ color: (execData?.modules?.billing?.overdue_invoices ?? 0) > 0 ? "#ef4444" : "#ffffff" }}>
                    ${(execData?.modules?.billing?.overdue_amount ?? 0).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Inventory Module Card */}
            <div className="module-matrix-card">
              <div className="module-matrix-header">
                <span className="module-matrix-title">
                  <Package size={16} color="#10b981" /> Inventory & Fulfillment
                </span>
                <span className="status-pill status-fulfilled">Synced</span>
              </div>
              <div className="module-matrix-stats">
                <div className="matrix-stat-item">
                  <span className="matrix-stat-lbl">Low Stock Alerts</span>
                  <span className="matrix-stat-val" style={{ color: (execData?.modules?.inventory?.low_stock_items ?? 0) > 0 ? "#f59e0b" : "#ffffff" }}>
                    {execData?.modules?.inventory?.low_stock_items ?? 0}
                  </span>
                </div>
                <div className="matrix-stat-item">
                  <span className="matrix-stat-lbl">Fulfilled Orders</span>
                  <span className="matrix-stat-val">{execData?.modules?.inventory?.fulfilled_orders ?? 0}</span>
                </div>
              </div>
            </div>

            {/* Tasks Module Card */}
            <div className="module-matrix-card">
              <div className="module-matrix-header">
                <span className="module-matrix-title">
                  <CheckSquare size={16} color="#10b981" /> Team Collaboration
                </span>
                <span className="status-pill status-fulfilled">Kanban Active</span>
              </div>
              <div className="module-matrix-stats">
                <div className="matrix-stat-item">
                  <span className="matrix-stat-lbl">In Progress</span>
                  <span className="matrix-stat-val">{execData?.modules?.tasks?.in_progress ?? 0}</span>
                </div>
                <div className="matrix-stat-item">
                  <span className="matrix-stat-lbl">Overdue Deadlines</span>
                  <span className="matrix-stat-val" style={{ color: (execData?.modules?.tasks?.overdue ?? 0) > 0 ? "#ef4444" : "#ffffff" }}>
                    {execData?.modules?.tasks?.overdue ?? 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* ════════ TAB 2: HISTORICAL SNAPSHOTS & TRENDS ════════ */}
      {activeTab === "snapshots" && (
        <>
          <div className="chart-card-bms">
            <div className="chart-card-header">
              <span className="chart-card-title">
                <TrendingUp size={16} color="#10b981" /> Revenue Trajectory (Daily Snapshots)
              </span>
              <span style={{ fontSize: 12, color: "#94a3b8" }}>14-Day Timeline</span>
            </div>
            <div style={{ height: 280, width: "100%" }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={snapshots}>
                  <defs>
                    <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip contentStyle={{ background: "#131b26", borderColor: "#1e293b", color: "#fff" }} />
                  <Area type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" name="Revenue ($)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="chart-card-bms">
            <div className="chart-card-header">
              <span className="chart-card-title">
                <Activity size={16} color="#10b981" /> Operational Velocity (Tickets vs Task Completion)
              </span>
            </div>
            <div style={{ height: 280, width: "100%" }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={snapshots}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip contentStyle={{ background: "#131b26", borderColor: "#1e293b", color: "#fff" }} />
                  <Bar dataKey="open_tickets" fill="#f59e0b" name="Open Tickets" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="task_completion_rate" fill="#10b981" name="Task Rate (%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Snapshots Table */}
          <div className="inventory-table-card">
            <table className="inventory-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Monthly Revenue</th>
                  <th>Open Tickets</th>
                  <th>New Leads</th>
                  <th>Pending Orders</th>
                  <th>Task Completion</th>
                </tr>
              </thead>
              <tbody>
                {snapshots.map((s) => (
                  <tr key={s.id}>
                    <td style={{ fontFamily: "monospace", fontWeight: 700, color: "#10b981" }}>
                      {s.date}
                    </td>
                    <td style={{ fontWeight: 700, color: "#ffffff" }}>
                      ${(s.revenue ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td>{s.open_tickets}</td>
                    <td>{s.new_leads}</td>
                    <td>{s.pending_orders}</td>
                    <td>
                      <span className="status-pill status-fulfilled">
                        {s.task_completion_rate}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* ════════ TAB 3: SUPPORT & CONVERSATIONAL AI ════════ */}
      {activeTab === "support_ai" && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
            {/* Sentiment Timeline */}
            <div className="chart-card-bms" style={{ marginBottom: 0 }}>
              <div className="chart-card-header">
                <span className="chart-card-title">Sentiment Timeline</span>
              </div>
              <div style={{ height: 260, width: "100%" }}>
                {sentimentTrendData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={sentimentTrendData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="index" stroke="#64748b" fontSize={11} />
                      <YAxis domain={[0, 1]} stroke="#64748b" fontSize={11} />
                      <Tooltip contentStyle={{ background: "#131b26", borderColor: "#1e293b", color: "#fff" }} />
                      <Area type="monotone" dataKey="score" stroke="#10b981" fill="rgba(16, 185, 129, 0.2)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ textAlign: "center", color: "#64748b", paddingTop: 100 }}>
                    No conversational interactions recorded yet.
                  </div>
                )}
              </div>
            </div>

            {/* Emotion Breakdown */}
            <div className="chart-card-bms" style={{ marginBottom: 0 }}>
              <div className="chart-card-header">
                <span className="chart-card-title">Emotion Distribution</span>
              </div>
              <div style={{ height: 260, width: "100%" }}>
                {emotionData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={emotionData}
                        dataKey="count"
                        nameKey="emotion"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        innerRadius={45}
                      >
                        {emotionData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={EMOTION_COLORS[entry.emotion] || "#64748b"} />
                        ))}
                      </Pie>
                      <Legend />
                      <Tooltip contentStyle={{ background: "#131b26", borderColor: "#1e293b", color: "#fff" }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ textAlign: "center", color: "#64748b", paddingTop: 100 }}>
                    No emotion distribution data yet.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Top Issues AI Card */}
          {topIssues.length > 0 && (
            <div className="chart-card-bms">
              <div className="chart-card-header">
                <span className="chart-card-title">
                  <Sparkles size={16} color="#10b981" /> AI Theme Extraction: Top Support Issues
                </span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
                {topIssues.map((issue, idx) => (
                  <div key={idx} className="matrix-stat-item">
                    <span className="matrix-stat-lbl">Recurring Theme #{idx + 1}</span>
                    <span className="matrix-stat-val" style={{ fontSize: 14 }}>
                      {issue.issue}
                    </span>
                    <span style={{ fontSize: 11, color: "#10b981", marginTop: 4 }}>
                      {issue.count} ticket(s)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Toast Notification */}
      {toastMessage && (
        <div
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            background: "#10b981",
            color: "#ffffff",
            padding: "12px 20px",
            borderRadius: 8,
            fontWeight: 600,
            fontSize: 13,
            boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
            zIndex: 9999,
          }}
        >
          {toastMessage}
        </div>
      )}
    </div>
  );
}
