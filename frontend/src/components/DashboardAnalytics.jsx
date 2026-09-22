import { useState, useMemo } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from "recharts";
import {
  TrendingUp, TrendingDown, Users, UserCheck, Activity, DollarSign,
  Download, Calendar, ArrowUpRight, CheckCircle2, Clock, AlertCircle,
  FileText, Sparkles, Filter, RefreshCw
} from "lucide-react";
import "./DashboardAnalytics.css";

// Theme emerald palette (Strictly avoiding blue)
const BRAND_GREEN = "#10b981";
const ACCENT_MINT = "#34d399";
const DARK_EMERALD = "#059669";
const PALE_EMERALD = "#6ee7b7";
const CHART_COLORS = [BRAND_GREEN, ACCENT_MINT, DARK_EMERALD, PALE_EMERALD];

// Mock datasets for different date ranges
const MOCK_TIME_DATA = {
  "7d": [
    { date: "Mon", visits: 14200, users: 4800, revenue: 9800, engagement: 64 },
    { date: "Tue", visits: 16800, users: 5600, revenue: 11400, engagement: 66 },
    { date: "Wed", visits: 19100, users: 6400, revenue: 13200, engagement: 70 },
    { date: "Thu", visits: 18400, users: 6100, revenue: 12600, engagement: 69 },
    { date: "Fri", visits: 22600, users: 7800, revenue: 16800, engagement: 73 },
    { date: "Sat", visits: 17900, users: 5900, revenue: 11200, engagement: 67 },
    { date: "Sun", visits: 19450, users: 6290, revenue: 13250, engagement: 71 },
  ],
  "30d": [
    { date: "Week 1", visits: 98400, users: 31200, revenue: 64200, engagement: 65 },
    { date: "Week 2", visits: 112500, users: 36800, revenue: 78900, engagement: 68 },
    { date: "Week 3", visits: 134200, users: 44100, revenue: 92400, engagement: 72 },
    { date: "Week 4", visits: 142100, users: 46300, revenue: 107300, engagement: 74 },
  ],
  "this_month": [
    { date: "Day 1-5", visits: 72000, users: 23500, revenue: 48000, engagement: 66 },
    { date: "Day 6-10", visits: 84000, users: 27900, revenue: 56500, engagement: 68 },
    { date: "Day 11-15", visits: 96000, users: 31200, revenue: 64800, engagement: 71 },
    { date: "Day 16-20", visits: 104000, users: 34500, revenue: 72100, engagement: 73 },
    { date: "Day 21-25", visits: 118000, users: 39100, revenue: 84200, engagement: 75 },
  ],
};

const KPI_STATS_BY_RANGE = {
  "7d": [
    {
      id: "visits",
      label: "Total Visits",
      value: "128,450",
      change: "+14.2%",
      isPositive: true,
      icon: Users,
    },
    {
      id: "users",
      label: "Active Users",
      value: "42,890",
      change: "+8.6%",
      isPositive: true,
      icon: UserCheck,
    },
    {
      id: "engagement",
      label: "Engagement Rate",
      value: "68.4%",
      change: "+3.1%",
      isPositive: true,
      icon: Activity,
    },
    {
      id: "revenue",
      label: "Revenue / Conversions",
      value: "$84,250",
      change: "+18.9%",
      isPositive: true,
      icon: DollarSign,
    },
  ],
  "30d": [
    {
      id: "visits",
      label: "Total Visits",
      value: "487,200",
      change: "+21.4%",
      isPositive: true,
      icon: Users,
    },
    {
      id: "users",
      label: "Active Users",
      value: "158,400",
      change: "+12.8%",
      isPositive: true,
      icon: UserCheck,
    },
    {
      id: "engagement",
      label: "Engagement Rate",
      value: "70.8%",
      change: "+5.4%",
      isPositive: true,
      icon: Activity,
    },
    {
      id: "revenue",
      label: "Revenue / Conversions",
      value: "$342,800",
      change: "+24.5%",
      isPositive: true,
      icon: DollarSign,
    },
  ],
  "this_month": [
    {
      id: "visits",
      label: "Total Visits",
      value: "474,000",
      change: "+19.1%",
      isPositive: true,
      icon: Users,
    },
    {
      id: "users",
      label: "Active Users",
      value: "156,200",
      change: "+11.4%",
      isPositive: true,
      icon: UserCheck,
    },
    {
      id: "engagement",
      label: "Engagement Rate",
      value: "71.2%",
      change: "+4.2%",
      isPositive: true,
      icon: Activity,
    },
    {
      id: "revenue",
      label: "Revenue / Conversions",
      value: "$325,600",
      change: "+22.7%",
      isPositive: true,
      icon: DollarSign,
    },
  ],
};

const CATEGORY_DISTRIBUTION = [
  { name: "Direct / Web App", value: 42, color: BRAND_GREEN },
  { name: "CRM / Pipeline", value: 28, color: ACCENT_MINT },
  { name: "Support AI", value: 18, color: DARK_EMERALD },
  { name: "Integrations & API", value: 12, color: PALE_EMERALD },
];

const INITIAL_ACTIVITIES = [
  {
    id: "EVT-9042",
    event: "Enterprise Deal Won",
    target: "Acme Global Tech",
    channel: "CRM Module",
    status: "Completed",
    timestamp: "12 mins ago",
    value: "+$18,500.00",
    statusType: "success",
  },
  {
    id: "EVT-9041",
    event: "Invoice Paid in Full",
    target: "Marcus Vance",
    channel: "Billing",
    status: "Verified",
    timestamp: "28 mins ago",
    value: "+$6,600.00",
    statusType: "success",
  },
  {
    id: "EVT-9040",
    event: "Sales Order Fulfilled",
    target: "ORD-2026-0014",
    channel: "Inventory",
    status: "Shipped",
    timestamp: "1 hour ago",
    value: "5 Units",
    statusType: "info",
  },
  {
    id: "EVT-9039",
    event: "Ticket Auto-Resolved",
    target: "Ticket #1042 (Caspian)",
    channel: "Support",
    status: "Resolved",
    timestamp: "2 hours ago",
    value: "CSAT 98%",
    statusType: "success",
  },
  {
    id: "EVT-9038",
    event: "Daily Snapshot Synced",
    target: "Analytics Engine",
    channel: "System",
    status: "Optimized",
    timestamp: "4 hours ago",
    value: "Score 91/100",
    statusType: "success",
  },
  {
    id: "EVT-9037",
    event: "Stock Reorder Triggered",
    target: "Edge Router X1",
    channel: "Inventory",
    status: "Pending",
    timestamp: "5 hours ago",
    value: "Restock: 25",
    statusType: "warning",
  },
];

// Custom Recharts Dark Tooltip
function CustomTooltip({ active, payload, label, activeMetric }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="dash-chart-tooltip">
        <div className="dash-tooltip-label">{label}</div>
        <div className="dash-tooltip-item">
          <span className="dash-tooltip-dot" />
          <span className="dash-tooltip-metric">
            {activeMetric === "revenue" ? "Revenue" : activeMetric === "users" ? "Active Users" : "Visits"}:
          </span>
          <span className="dash-tooltip-value">
            {activeMetric === "revenue"
              ? `$${data.revenue?.toLocaleString()}`
              : activeMetric === "users"
              ? data.users?.toLocaleString()
              : data.visits?.toLocaleString()}
          </span>
        </div>
        <div className="dash-tooltip-sub">
          Engagement: <strong>{data.engagement}%</strong>
        </div>
      </div>
    );
  }
  return null;
}

export default function DashboardAnalytics() {
  const [dateRange, setDateRange] = useState("7d");
  const [activeMetric, setActiveMetric] = useState("visits");
  const [searchFilter, setSearchFilter] = useState("");
  const [toast, setToast] = useState(null);

  const kpiStats = KPI_STATS_BY_RANGE[dateRange] || KPI_STATS_BY_RANGE["7d"];
  const chartData = MOCK_TIME_DATA[dateRange] || MOCK_TIME_DATA["7d"];

  const showNotification = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  const handleExport = () => {
    const csvRows = [
      ["Date", "Visits", "Active Users", "Revenue ($)", "Engagement (%)"],
      ...chartData.map((d) => [d.date, d.visits, d.users, d.revenue, `${d.engagement}%`]),
    ];
    const csvContent =
      "data:text/csv;charset=utf-8," + csvRows.map((e) => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `analytics-overview-${dateRange}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showNotification("Analytics Report exported successfully as CSV!");
  };

  // Filter activities
  const filteredActivities = useMemo(() => {
    if (!searchFilter.trim()) return INITIAL_ACTIVITIES;
    const q = searchFilter.toLowerCase();
    return INITIAL_ACTIVITIES.filter(
      (a) =>
        a.event.toLowerCase().includes(q) ||
        a.target.toLowerCase().includes(q) ||
        a.channel.toLowerCase().includes(q) ||
        a.status.toLowerCase().includes(q)
    );
  }, [searchFilter]);

  return (
    <div className="dashboard-analytics-root">
      {/* Toast Notification */}
      {toast && (
        <div className="dash-toast-banner animate-in fade-in slide-in-from-top-2">
          <CheckCircle2 size={16} color="#10b981" />
          <span>{toast}</span>
        </div>
      )}

      {/* ── HEADER ── */}
      <div className="dash-analytics-header">
        <div className="dash-header-title-block">
          <div className="dash-badge-live">
            <span className="dash-live-dot" />
            LIVE DASHBOARD
          </div>
          <h1 className="dash-analytics-title">Analytics Overview</h1>
          <p className="dash-analytics-subtitle">
            System performance metrics, customer engagement rates, and conversion dynamics.
          </p>
        </div>

        <div className="dash-header-controls">
          {/* Date range selector */}
          <div className="dash-select-container">
            <Calendar size={14} className="dash-select-icon" />
            <select
              className="dash-date-select"
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="this_month">This Month</option>
            </select>
          </div>

          {/* Export button */}
          <button className="dash-export-btn" onClick={handleExport} title="Export CSV summary">
            <Download size={15} />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* ── ROW OF 4 KPI STAT CARDS ── */}
      <div className="dash-kpi-grid">
        {kpiStats.map((kpi) => {
          const Icon = kpi.icon;
          const isCurrentActive = activeMetric === kpi.id;
          return (
            <div
              key={kpi.id}
              className={`dash-kpi-card ${isCurrentActive ? "active" : ""}`}
              onClick={() => {
                if (kpi.id === "revenue" || kpi.id === "visits" || kpi.id === "users") {
                  setActiveMetric(kpi.id);
                }
              }}
              title="Click to graph this metric"
            >
              <div className="dash-kpi-top">
                <span className="dash-kpi-label">{kpi.label}</span>
                <div className="dash-kpi-icon-box">
                  <Icon size={17} color="#10b981" />
                </div>
              </div>
              <div className="dash-kpi-mid">
                <span className="dash-kpi-value">{kpi.value}</span>
              </div>
              <div className="dash-kpi-bottom">
                <span className="dash-kpi-growth-badge">
                  <TrendingUp size={12} />
                  {kpi.change}
                </span>
                <span className="dash-kpi-comparison">vs previous period</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── CHARTS ROW: PRIMARY TREND CHART + SECONDARY BREAKDOWN ── */}
      <div className="dash-charts-grid">
        {/* Primary Trend Chart */}
        <div className="dash-chart-card primary-card">
          <div className="dash-chart-card-header">
            <div>
              <h2 className="dash-card-heading">Performance Trends</h2>
              <p className="dash-card-subheading">
                Historical trajectory across{" "}
                <span className="text-emerald-400 font-semibold capitalize">
                  {activeMetric === "revenue" ? "Revenue ($)" : activeMetric === "users" ? "Active Users" : "Total Visits"}
                </span>
              </p>
            </div>
            <div className="dash-metric-tabs">
              <button
                className={`dash-tab-btn ${activeMetric === "visits" ? "active" : ""}`}
                onClick={() => setActiveMetric("visits")}
              >
                Visits
              </button>
              <button
                className={`dash-tab-btn ${activeMetric === "users" ? "active" : ""}`}
                onClick={() => setActiveMetric("users")}
              >
                Users
              </button>
              <button
                className={`dash-tab-btn ${activeMetric === "revenue" ? "active" : ""}`}
                onClick={() => setActiveMetric("revenue")}
              >
                Revenue ($)
              </button>
            </div>
          </div>

          <div className="dash-primary-chart-wrapper">
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="emeraldGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={BRAND_GREEN} stopOpacity={0.35} />
                    <stop offset="95%" stopColor={BRAND_GREEN} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: "#1f2937" }}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(val) =>
                    activeMetric === "revenue"
                      ? `$${(val / 1000).toFixed(0)}k`
                      : val >= 1000
                      ? `${(val / 1000).toFixed(0)}k`
                      : val
                  }
                />
                <Tooltip
                  content={<CustomTooltip activeMetric={activeMetric} />}
                />
                <Area
                  type="monotone"
                  dataKey={activeMetric}
                  stroke={BRAND_GREEN}
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#emeraldGradient)"
                  dot={{ r: 3, fill: BRAND_GREEN, strokeWidth: 1 }}
                  activeDot={{ r: 6, fill: ACCENT_MINT }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Secondary View / Breakdown: Donut Chart & Category Progress */}
        <div className="dash-chart-card secondary-card">
          <div className="dash-chart-card-header">
            <div>
              <h2 className="dash-card-heading">Channel Distribution</h2>
              <p className="dash-card-subheading">Source attribution & volume</p>
            </div>
            <span className="dash-pill-tag">100% Total</span>
          </div>

          <div className="dash-donut-wrapper">
            <div className="dash-donut-canvas">
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie
                    data={CATEGORY_DISTRIBUTION}
                    innerRadius={48}
                    outerRadius={70}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {CATEGORY_DISTRIBUTION.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => [`${value}%`, "Share"]}
                    contentStyle={{
                      backgroundColor: "#111827",
                      borderColor: "#1f2937",
                      borderRadius: "8px",
                      color: "#f1f5f9",
                      fontSize: "12px",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="dash-donut-center-text">
                <span className="dash-donut-center-num">4</span>
                <span className="dash-donut-center-sub">Channels</span>
              </div>
            </div>

            {/* Progress Bar Breakdown list */}
            <div className="dash-progress-list">
              {CATEGORY_DISTRIBUTION.map((item) => (
                <div key={item.name} className="dash-progress-row">
                  <div className="dash-progress-info">
                    <span className="dash-progress-dot" style={{ backgroundColor: item.color }} />
                    <span className="dash-progress-name">{item.name}</span>
                    <span className="dash-progress-val">{item.value}%</span>
                  </div>
                  <div className="dash-progress-track">
                    <div
                      className="dash-progress-bar"
                      style={{ width: `${item.value}%`, backgroundColor: item.color }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── RECENT ACTIVITY DATA TABLE ── */}
      <div className="dash-table-card">
        <div className="dash-table-header">
          <div>
            <h2 className="dash-card-heading">Recent System Events & Transactions</h2>
            <p className="dash-card-subheading">Real-time audit log of customer and BMS events</p>
          </div>

          <div className="dash-table-filter-box">
            <Filter size={14} className="dash-filter-icon" />
            <input
              type="text"
              className="dash-table-search-input"
              placeholder="Filter events or users..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
            />
          </div>
        </div>

        <div className="dash-table-responsive-wrapper">
          <table className="dash-data-table">
            <thead>
              <tr>
                <th>Event / Action</th>
                <th>Target / User</th>
                <th>Channel / Module</th>
                <th>Status</th>
                <th>Timestamp</th>
                <th className="text-right">Value / Metric</th>
              </tr>
            </thead>
            <tbody>
              {filteredActivities.length > 0 ? (
                filteredActivities.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <div className="dash-event-cell">
                        <span className="dash-event-id">{row.id}</span>
                        <span className="dash-event-title">{row.event}</span>
                      </div>
                    </td>
                    <td>
                      <span className="dash-target-name">{row.target}</span>
                    </td>
                    <td>
                      <span className="dash-channel-badge">{row.channel}</span>
                    </td>
                    <td>
                      <span className={`dash-status-pill ${row.statusType}`}>
                        {row.status}
                      </span>
                    </td>
                    <td>
                      <span className="dash-time-stamp">
                        <Clock size={11} className="inline mr-1 opacity-70" />
                        {row.timestamp}
                      </span>
                    </td>
                    <td className="text-right">
                      <span className="dash-metric-highlight font-mono">
                        {row.value}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="dash-table-empty">
                    No matching activity events found for "{searchFilter}".
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
