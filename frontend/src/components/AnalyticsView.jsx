import { useState, useEffect, useCallback } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  BarChart, Bar
} from "recharts";
import { Download, TrendingUp, TrendingDown, Minus, Activity, RefreshCw } from "lucide-react";

const API = "http://localhost:8000/analytics";

const EMOTION_COLORS = {
  angry: "#ff3a5c",
  frustrated: "#f59e0b",
  neutral: "#64748b",
  happy: "#00e676",
  grateful: "#34d399",
  curious: "#8b5cf6",
  uninterested: "#6b7280"
};

const ACTION_COLORS = { ESCALATE: "#E5484D", NORMAL: "#6b7280", UPSELL: "#30A46C" };

function scoreColor(s) {
  if (s < 0.3) return "#E5484D";
  if (s >= 0.7) return "#30A46C";
  return "#F5A623";
}

function trendMeta(trend) {
  if (trend === "improving") return { icon: TrendingUp, color: "#30A46C", bg: "rgba(48,164,108,0.1)", border: "rgba(48,164,108,0.25)" };
  if (trend === "declining") return { icon: TrendingDown, color: "#E5484D", bg: "rgba(229,72,77,0.1)", border: "rgba(229,72,77,0.25)" };
  return { icon: Minus, color: "#F5A623", bg: "rgba(245,166,35,0.1)", border: "rgba(245,166,35,0.25)" };
}

/* ── Skeleton Block ── */
function Skeleton({ h = 120, className = "" }) {
  return (
    <div
      className={`rounded-xl animate-pulse ${className}`}
      style={{ height: h, background: "linear-gradient(90deg, #232323 25%, #2a2a2a 50%, #232323 75%)", backgroundSize: "400% 100%" }}
    />
  );
}

/* ── KPI Card ── */
function KpiCard({ label, value, suffix = "", color }) {
  return (
    <div className="kpi-card" style={{ "--kpi-accent": color }}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" style={{ color: color || "#fff" }}>
        {value}{suffix && <span className="kpi-suffix">{suffix}</span>}
      </div>
    </div>
  );
}

/* ── Circular Progress Ring ── */
function HealthRing({ score }) {
  const r = 70, c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  const color = score >= 70 ? "#30A46C" : score >= 40 ? "#F5A623" : "#E5484D";

  return (
    <svg width="180" height="180" viewBox="0 0 180 180" className="health-ring">
      <circle cx="90" cy="90" r={r} fill="none" stroke="#2a2a2a" strokeWidth="10" />
      <circle
        cx="90" cy="90" r={r} fill="none"
        stroke={color} strokeWidth="10" strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={offset}
        style={{ transition: "stroke-dashoffset 1.2s ease-out", transform: "rotate(-90deg)", transformOrigin: "90px 90px" }}
      />
      <text x="90" y="82" textAnchor="middle" fill={color} fontSize="36" fontWeight="700" fontFamily="monospace">{score}</text>
      <text x="90" y="108" textAnchor="middle" fill="#6b7280" fontSize="12" fontWeight="500">/ 100</text>
    </svg>
  );
}

/* ── Custom Recharts Tooltip ── */
function DarkTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "#1e1e1e", border: "1px solid #333", borderRadius: 8, padding: "8px 12px", fontSize: 12 }}>
      <div style={{ color: "#999", marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || "#fff" }}>{p.name}: <strong>{typeof p.value === "number" ? p.value.toFixed?.(2) ?? p.value : p.value}</strong></div>
      ))}
    </div>
  );
}

/* ══════════════════════════════════════════════
   MAIN ANALYTICS VIEW
   ══════════════════════════════════════════════ */
export default function AnalyticsView() {
  const [overview, setOverview] = useState(null);
  const [trend, setTrend] = useState(null);
  const [emotions, setEmotions] = useState(null);
  const [actions, setActions] = useState(null);
  const [hourly, setHourly] = useState(null);
  const [topIssues, setTopIssues] = useState(null);
  const [health, setHealth] = useState(null);
  const [voiceStats, setVoiceStats] = useState(null);
  const [languageStats, setLanguageStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchAll = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);

    try {
      const opts = { method: "POST" };
      const [ov, tr, em, ac, hr, ti, hs, vs, langStats] = await Promise.all([
        fetch(`${API}/overview`, opts).then(r => r.json()),
        fetch(`${API}/sentiment-trend`, opts).then(r => r.json()),
        fetch(`${API}/emotion-breakdown`, opts).then(r => r.json()),
        fetch(`${API}/action-distribution`, opts).then(r => r.json()),
        fetch(`${API}/hourly-activity`, opts).then(r => r.json()),
        fetch(`${API}/top-issues`, opts).then(r => r.json()),
        fetch(`${API}/customer-health-score`, opts).then(r => r.json()),
        fetch(`${API}/voice-stats`, opts).then(r => r.json()),
        fetch(`http://localhost:8000/languages/stats`, { method: "GET" }).then(r => r.json()),
      ]);

      setOverview(ov);
      setTrend(tr);
      setEmotions(em);
      setActions(ac);
      setHourly(hr);
      setTopIssues(ti);
      setHealth(hs);
      setVoiceStats(vs);
      setLanguageStats(langStats);
      setLastRefresh(new Date());
    } catch (err) {
      console.error("Analytics fetch error:", err);
      setError("Failed to load analytics data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Auto-refresh every 30s
  useEffect(() => {
    const id = setInterval(() => fetchAll(true), 30000);
    return () => clearInterval(id);
  }, [fetchAll]);

  // Export as JSON
  const exportJSON = () => {
    const blob = new Blob([JSON.stringify({ overview, trend, emotions, actions, hourly, topIssues, health }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `analytics_${new Date().toISOString().slice(0,10)}.json`;
    a.click(); URL.revokeObjectURL(url);
  };

  // Transform action data for BarChart
  const actionData = actions ? Object.entries(actions).map(([name, value]) => ({ name, value })) : [];

  if (loading) {
    return (
      <div className="analytics-view">
        <div className="av-header"><Skeleton h={32} className="w-48" /></div>
        <div className="av-kpi-grid">
          {[...Array(6)].map((_, i) => <Skeleton key={i} h={100} />)}
        </div>
        <div className="av-row-2">
          <Skeleton h={280} /><Skeleton h={280} />
        </div>
        <div className="av-row-2">
          <Skeleton h={280} /><Skeleton h={280} />
        </div>
        <Skeleton h={260} />
        <Skeleton h={220} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-view p-8 flex items-center justify-center text-red-400">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="analytics-view">

      {/* ── Header ── */}
      <div className="av-header">
        <div>
          <h2 className="av-title">
            <Activity size={22} /> Analytics Dashboard
          </h2>
          <p className="av-subtitle">
            Real-time performance insights &amp; AI-powered analysis
            {lastRefresh && <span className="av-refresh-ts"> · Updated {lastRefresh.toLocaleTimeString()}</span>}
            {refreshing && <RefreshCw size={12} className="av-spinner" />}
          </p>
        </div>
        <button className="av-export-btn" onClick={exportJSON}>
          <Download size={14} /> Export JSON
        </button>
      </div>

      {/* ── Row 1: KPI Cards ── */}
      <div className="av-kpi-grid">
        <KpiCard label="Total Conversations" value={overview?.total_conversations ?? 0} />
        <KpiCard label="Avg Sentiment Score" value={overview?.avg_sentiment_score?.toFixed(2) ?? "—"} color={scoreColor(overview?.avg_sentiment_score ?? 0.5)} />
        <KpiCard label="Escalation Rate" value={overview?.escalation_rate ?? 0} suffix="%" color="#E5484D" />
        <KpiCard label="Upsell Rate" value={overview?.upsell_rate ?? 0} suffix="%" color="#30A46C" />
        <KpiCard label="Resolution Rate" value={overview?.resolution_rate ?? 0} suffix="%" color="#3B82F6" />
        <KpiCard
          label="Customer Health"
          value={health?.score ?? "—"}
          suffix="/100"
          color={health?.score >= 70 ? "#30A46C" : health?.score >= 40 ? "#F5A623" : "#E5484D"}
        />
      </div>

      {/* ── Row 1.5: Voice Analytics KPIs ── */}
      <h3 className="av-chart-title" style={{ marginTop: '10px' }}>Voice Analytics</h3>
      <div className="av-kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: '24px' }}>
        <KpiCard label="Total Voice Conversations" value={voiceStats?.total_voice_conversations ?? 0} color="#8b5cf6" />
        <KpiCard label="Most Common Language" value={voiceStats?.most_common_language?.toUpperCase() ?? "N/A"} color="#3B82F6" />
        <KpiCard label="Avg Confidence Score" value={(voiceStats?.avg_confidence_score * 100)?.toFixed(1) ?? 0} suffix="%" color="#30A46C" />
      </div>

      {/* ── Row 1.6: Regional Language Breakdown ── */}
      <h3 className="av-chart-title" style={{ marginTop: '10px' }}>Regional Language Breakdown</h3>
      {languageStats && languageStats.length > 0 && (
        <div className="av-row-2 mb-6">
          <div className="av-chart-card flex-1">
            <h3 className="av-chart-title">Usage by Language</h3>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={languageStats || []} dataKey="count" nameKey="language_name" cx="50%" cy="50%" outerRadius={80} paddingAngle={5}>
                  {(Array.isArray(languageStats) ? languageStats : []).map((entry, index) => {
                    const colors = { hi: "orange", bn: "green", ta: "red", te: "blue", mr: "purple", gu: "yellow", pa: "indigo", kn: "teal", ml: "pink", en: "gray" };
                    return <Cell key={`cell-${index}`} fill={colors[entry.language] || "#8884d8"} />;
                  })}
                </Pie>
                <Tooltip content={<DarkTooltip />} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="av-chart-card flex-1">
            <h3 className="av-chart-title">Avg Sentiment per Language</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={languageStats} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis dataKey="language_name" tick={{ fill: "#666", fontSize: 11 }} />
                <YAxis domain={[0, 1]} tick={{ fill: "#666", fontSize: 11 }} />
                <Tooltip content={<DarkTooltip />} cursor={{ fill: "#2a2a2a" }} />
                <Bar dataKey="avg_sentiment" name="Avg Sentiment" radius={[4, 4, 0, 0]}>
                  {(Array.isArray(languageStats) ? languageStats : []).map((entry, index) => {
                    const colors = { hi: "orange", bn: "green", ta: "red", te: "blue", mr: "purple", gu: "yellow", pa: "indigo", kn: "teal", ml: "pink", en: "gray" };
                    return <Cell key={`cell-${index}`} fill={colors[entry.language] || "#8884d8"} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ── Row 2: Sentiment Trend + Emotion Breakdown ── */}
      <div className="av-row-2">
        {/* Sentiment Trend AreaChart */}
        <div className="av-chart-card">
          <h3 className="av-chart-title">Sentiment Trend <span className="av-chart-badge">7 days</span></h3>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={trend || []} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="sentGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis dataKey="date" tick={{ fill: "#666", fontSize: 11 }} tickFormatter={v => v?.slice(5)} />
              <YAxis domain={[0, 1]} tick={{ fill: "#666", fontSize: 11 }} />
              <Tooltip content={<DarkTooltip />} />
              <Area type="monotone" dataKey="avg_score" stroke="#3B82F6" fill="url(#sentGrad)" strokeWidth={2} animationDuration={1200} name="Avg Score" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Emotion Breakdown PieChart */}
        <div className="av-chart-card">
          <h3 className="av-chart-title">Emotion Breakdown</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={emotions || []}
                cx="50%" cy="50%" innerRadius={55} outerRadius={90}
                dataKey="count" nameKey="emotion"
                paddingAngle={3} animationDuration={1200}
                label={({ emotion, percentage }) => `${emotion} ${percentage}%`}
              >
                {(Array.isArray(emotions) ? emotions : []).map((entry, i) => (
                  <Cell key={i} fill={EMOTION_COLORS[entry.emotion] || "#6b7280"} />
                ))}
              </Pie>
              <Tooltip content={<DarkTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Row 3: Action Distribution + Hourly Activity ── */}
      <div className="av-row-2">
        {/* Action Distribution BarChart */}
        <div className="av-chart-card">
          <h3 className="av-chart-title">Action Distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={actionData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis dataKey="name" tick={{ fill: "#999", fontSize: 12 }} />
              <YAxis tick={{ fill: "#666", fontSize: 11 }} />
              <Tooltip content={<DarkTooltip />} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]} animationDuration={1000} name="Count">
                {(Array.isArray(actionData) ? actionData : []).map((entry, i) => (
                  <Cell key={i} fill={ACTION_COLORS[entry.name] || "#6b7280"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Hourly Activity */}
        <div className="av-chart-card">
          <h3 className="av-chart-title">Hourly Activity <span className="av-chart-badge">today</span></h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={hourly || []} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis dataKey="hour" tick={{ fill: "#999", fontSize: 11 }} tickFormatter={h => `${h}:00`} />
              <YAxis tick={{ fill: "#666", fontSize: 11 }} />
              <Tooltip content={<DarkTooltip />} />
              <Bar dataKey="count" fill="#8b5cf6" radius={[6, 6, 0, 0]} animationDuration={1000} name="Messages" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Row 4: Top Recurring Issues ── */}
      <div className="av-chart-card av-full">
        <h3 className="av-chart-title">Top Recurring Issues <span className="av-chart-badge">AI-analyzed</span></h3>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={topIssues || []} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" horizontal={false} />
            <XAxis type="number" tick={{ fill: "#666", fontSize: 11 }} />
            <YAxis type="category" dataKey="issue" width={200} tick={{ fill: "#ccc", fontSize: 12 }} />
            <Tooltip content={<DarkTooltip />} />
            <Bar dataKey="count" fill="#F59E0B" radius={[0, 6, 6, 0]} animationDuration={1200} name="Tickets" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Row 5: Customer Health Score Panel ── */}
      <div className="av-health-panel">
        <div className="av-health-left">
          <HealthRing score={health?.score ?? 50} />
          {health?.trend && (() => {
            const tm = trendMeta(health.trend);
            const Icon = tm.icon;
            return (
              <div className="av-trend-badge" style={{ background: tm.bg, border: `1px solid ${tm.border}`, color: tm.color }}>
                <Icon size={14} /> {health.trend.charAt(0).toUpperCase() + health.trend.slice(1)}
              </div>
            );
          })()}
        </div>
        <div className="av-health-right">
          <h3 className="av-health-title">Customer Health Score</h3>
          <p className="av-health-sub">AI-generated insights based on sentiment, resolution, and escalation data</p>
          <ul className="av-health-insights">
            {(Array.isArray(health?.key_insights) ? health.key_insights : []).map((ins, i) => (
              <li key={i}>{ins}</li>
            ))}
          </ul>
        </div>
      </div>

    </div>
  );
}
