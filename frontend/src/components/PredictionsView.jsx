import { useState, useEffect, useCallback } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, ReferenceLine, Line, ComposedChart
} from "recharts";
import {
  RefreshCw, TrendingUp, TrendingDown, AlertTriangle, Target,
  Ticket, DollarSign, Users, Mail, ExternalLink, Sparkles, Clock
} from "lucide-react";
import "./PredictionsView.css";

const API = "http://localhost:8000/predict";
const REFRESH_MS = 6 * 60 * 60 * 1000;

function Skeleton({ h = 100, className = "" }) {
  return <div className={`pred-skeleton ${className}`} style={{ height: h }} />;
}

function DarkTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="pred-tooltip">
      <div className="pred-tooltip-label">{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || "#fff" }}>
          {p.name}: <strong>{typeof p.value === "number" ? p.value.toFixed?.(2) ?? p.value : p.value}</strong>
        </div>
      ))}
    </div>
  );
}

function riskColor(p) {
  if (p >= 0.7) return "#E5484D";
  if (p >= 0.3) return "#F5A623";
  return "#30A46C";
}

function openEmailCompose(to, subject, body) {
  sessionStorage.setItem("emailComposeDraft", JSON.stringify({ to, subject, body }));
  window.dispatchEvent(new Event("navigate-email-compose"));
}

function openCrm() {
  window.dispatchEvent(new Event("navigate-crm"));
}

export default function PredictionsView() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [churnFilter, setChurnFilter] = useState("all");
  const [showActual, setShowActual] = useState(false);
  const [expandedChurn, setExpandedChurn] = useState(false);
  const [expandedUpsell, setExpandedUpsell] = useState(false);

  const fetchDashboard = useCallback(async (force = false) => {
    if (force) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const url = force ? `${API}/dashboard/recalculate` : `${API}/dashboard`;
      const res = await fetch(url, { method: force ? "POST" : "GET" });
      if (res.ok) {
        const json = await res.json();
        setData(json);
      } else {
        throw new Error("Failed to fetch dashboard data");
      }
    } catch (e) {
      console.error(e);
      setError("Failed to load Predictions data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(() => fetchDashboard(), REFRESH_MS);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  const filteredChurn = (data?.churn_risk || []).filter(c => {
    const p = c.churn_probability;
    if (churnFilter === "high") return p >= 0.7;
    if (churnFilter === "medium") return p >= 0.3 && p < 0.7;
    if (churnFilter === "low") return p < 0.3;
    return true;
  });

  const displayChurn = expandedChurn ? filteredChurn : filteredChurn.slice(0, 10);
  const displayUpsell = expandedUpsell ? (data?.upsell_opportunities || []) : (data?.upsell_opportunities || []).slice(0, 5);

  const ticketChart = data?.ticket_forecast?.next_7_days || [];
  const avgTickets = data?.ticket_forecast?.avg_daily_baseline || 1;

  const sentimentChart = showActual
    ? [
        ...(data?.sentiment_forecast?.actual_last_7_days || []).map(d => ({
          date: d.date?.slice(5),
          actual: d.actual_sentiment,
          type: "actual"
        })),
        ...(data?.sentiment_forecast?.next_7_days || []).map(d => ({
          date: d.date?.slice(5),
          predicted: d.predicted_sentiment,
          upper: d.confidence_upper,
          lower: d.confidence_lower,
          type: "predicted"
        }))
      ]
    : (data?.sentiment_forecast?.next_7_days || []).map(d => ({
        date: d.date?.slice(5),
        predicted: d.predicted_sentiment,
        upper: d.confidence_upper,
        lower: d.confidence_lower,
      }));

  if (loading) {
    return (
      <div className="predictions-view">
        <div className="pred-topbar"><Skeleton h={40} /></div>
        <div className="pred-alert-row">
          {[1,2,3,4].map(i => <Skeleton key={i} h={140} />)}
        </div>
        <Skeleton h={320} />
        <div className="pred-row-3"><Skeleton h={280} /><Skeleton h={280} /></div>
        <Skeleton h={220} />
        <Skeleton h={200} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="predictions-view p-8 flex items-center justify-center text-red-400">
        Error: {error}
      </div>
    );
  }

  const summary = data?.summary || {};
  const highRisk = (data?.churn_risk || []).filter(c => c.churn_probability >= 0.5);
  const rev = data?.revenue_forecast || {};

  return (
    <div className="predictions-view">
      {/* TOP BAR */}
      <div className="pred-topbar">
        <div className="pred-topbar-left">
          <Sparkles size={18} className="text-emerald-400" />
          <h2 className="pred-title">Predictive Analytics</h2>
          {data?.calculated_at && (
            <span className="pred-timestamp">
              <Clock size={12} /> Last calculated: {new Date(data.calculated_at).toLocaleString()}
              {data.cached && " (cached)"}
            </span>
          )}
        </div>
        <div className="pred-topbar-right">
          <span className="pred-confidence-badge">
            {data?.overall_confidence || 0}% confidence
          </span>
          <button className="pred-recalc-btn" onClick={() => fetchDashboard(true)} disabled={refreshing}>
            <RefreshCw size={14} className={refreshing ? "spin" : ""} />
            {refreshing ? "Calculating…" : "Recalculate All"}
          </button>
        </div>
      </div>

      {/* ROW 1 — Alert Cards */}
      <div className="pred-alert-row">
        <div className="pred-alert-card pred-alert-red">
          <div className="pred-alert-icon"><AlertTriangle size={20} /></div>
          <div className="pred-alert-body">
            <div className="pred-alert-label">Churn Alert</div>
            <div className="pred-alert-value">{summary.at_risk_count || highRisk.length} customers at risk</div>
            <ul className="pred-alert-list">
              {(Array.isArray(highRisk) ? highRisk : []).slice(0, 3).map(c => (
                <li key={c.customer_id}>{c.name} ({Math.round(c.churn_probability * 100)}%)</li>
              ))}
            </ul>
            <button className="pred-alert-link" onClick={() => document.getElementById("churn-table")?.scrollIntoView({ behavior: "smooth" })}>
              View All →
            </button>
          </div>
        </div>

        <div className="pred-alert-card pred-alert-green">
          <div className="pred-alert-icon"><Target size={20} /></div>
          <div className="pred-alert-body">
            <div className="pred-alert-label">Upsell Opportunity</div>
            <div className="pred-alert-value">{summary.upsell_count || 0} customers ready</div>
            <ul className="pred-alert-list">
              {(Array.isArray(data?.upsell_opportunities) ? data.upsell_opportunities : []).slice(0, 3).map(c => (
                <li key={c.customer_id}>{c.name} ({Math.round(c.upsell_probability * 100)}%)</li>
              ))}
            </ul>
            <button className="pred-alert-link" onClick={() => document.getElementById("upsell-panel")?.scrollIntoView({ behavior: "smooth" })}>
              View All →
            </button>
          </div>
        </div>

        <div className="pred-alert-card pred-alert-yellow">
          <div className="pred-alert-icon"><Ticket size={20} /></div>
          <div className="pred-alert-body">
            <div className="pred-alert-label">Ticket Forecast</div>
            <div className="pred-alert-value">{summary.tickets_this_week || 0} tickets expected</div>
            <div className="pred-alert-meta">Peak: {data?.ticket_forecast?.peak_day || "—"}</div>
            <div className="pred-alert-meta">{Math.round((data?.ticket_forecast?.confidence || 0) * 100)}% confidence</div>
          </div>
        </div>

        <div className="pred-alert-card pred-alert-blue">
          <div className="pred-alert-icon"><DollarSign size={20} /></div>
          <div className="pred-alert-body">
            <div className="pred-alert-label">Revenue Forecast</div>
            <div className="pred-alert-value">
              ₹{(summary.revenue_30_days || rev["30_days"] || 0).toLocaleString("en-IN")} <span className="pred-alert-sub">/ 30 days</span>
            </div>
            <div className="pred-alert-meta flex items-center gap-1">
              {rev.trend === "up" ? <TrendingUp size={14} className="text-green-400" /> : <TrendingDown size={14} className="text-red-400" />}
              {Math.round((rev.confidence || 0) * 100)}% confidence
            </div>
          </div>
        </div>
      </div>

      {/* ROW 2 — Churn Table */}
      <div className="pred-panel" id="churn-table">
        <div className="pred-panel-header">
          <h3>Churn Risk Analysis</h3>
          <div className="pred-filters">
            {["all", "high", "medium", "low"].map(f => (
              <button key={f} className={`pred-filter-btn ${churnFilter === f ? "active" : ""}`} onClick={() => setChurnFilter(f)}>
                {f === "all" ? "All" : f === "high" ? "High (>70%)" : f === "medium" ? "Medium (30-70%)" : "Low (<30%)"}
              </button>
            ))}
          </div>
        </div>
        <div className="pred-table-wrap">
          <table className="pred-table">
            <thead>
              <tr>
                <th>Customer</th><th>Last Contact</th><th>Sentiment Trend</th>
                <th>Churn Risk</th><th>Risk Factors</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {displayChurn.map(c => (
                <tr key={c.customer_id}>
                  <td>
                    <div className="pred-cust-name">{c.name}</div>
                    <div className="pred-cust-email">{c.email || "—"}</div>
                  </td>
                  <td>{c.last_contact ? new Date(c.last_contact).toLocaleDateString() : "—"}</td>
                  <td>
                    <span className={`pred-trend pred-trend-${c.sentiment_trend}`}>{c.sentiment_trend}</span>
                  </td>
                  <td>
                    <div className="pred-risk-cell">
                      <div className="pred-risk-bar-track">
                        <div className="pred-risk-bar-fill" style={{ width: `${c.churn_probability * 100}%`, background: riskColor(c.churn_probability) }} />
                      </div>
                      <span style={{ color: riskColor(c.churn_probability) }}>{Math.round(c.churn_probability * 100)}%</span>
                    </div>
                  </td>
                  <td>
                    <div className="pred-chips">
                      {(c.risk_factors || []).map((f, i) => (
                        <span key={i} className="pred-chip">{f}</span>
                      ))}
                    </div>
                  </td>
                  <td>
                    <div className="pred-actions">
                      <button className="pred-action-btn" onClick={() => openEmailCompose(
                        c.email || "",
                        `We value your business, ${c.name}`,
                        `Hi ${c.name},\n\nWe noticed you haven't been in touch recently and wanted to check in. ${c.recommended_action || ""}\n\nBest regards,\nChameleon AI Team`
                      )}>
                        <Mail size={12} /> Contact
                      </button>
                      <button className="pred-action-btn secondary" onClick={openCrm}>
                        <ExternalLink size={12} /> CRM
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {displayChurn.length === 0 && (
                <tr><td colSpan={6} className="pred-empty">No customers match this filter</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {filteredChurn.length > 10 && (
          <button className="pred-expand-btn" onClick={() => setExpandedChurn(!expandedChurn)}>
            {expandedChurn ? "Show Less" : `Show All (${filteredChurn.length})`}
          </button>
        )}
      </div>

      {/* ROW 3 — Upsell + Ticket Forecast */}
      <div className="pred-row-3">
        <div className="pred-panel" id="upsell-panel">
          <h3>Upsell Opportunities</h3>
          <div className="pred-upsell-list">
            {displayUpsell.map(c => (
              <div key={c.customer_id} className="pred-upsell-item">
                <div className="pred-upsell-header">
                  <div>
                    <div className="pred-cust-name">{c.name}</div>
                    <div className="pred-cust-email">{c.company || c.email || "—"}</div>
                  </div>
                  <span className="pred-upsell-pct">{Math.round(c.upsell_probability * 100)}%</span>
                </div>
                <div className="pred-risk-bar-track">
                  <div className="pred-risk-bar-fill" style={{ width: `${c.upsell_probability * 100}%`, background: "#30A46C" }} />
                </div>
                <div className="pred-upsell-offer">{c.best_offer}</div>
                <div className="pred-upsell-time">Best time: {c.best_time_to_contact}</div>
                <button className="pred-action-btn full" onClick={() => openEmailCompose(
                  c.email || "",
                  `Special offer for ${c.name}`,
                  `Hi ${c.name},\n\nBased on your positive experience with us, we'd like to offer you: ${c.best_offer}.\n\nWould you be interested in learning more?\n\nBest regards,\nChameleon AI Team`
                )}>
                  Send Offer
                </button>
              </div>
            ))}
            {(data?.upsell_opportunities || []).length === 0 && (
              <div className="pred-empty">No upsell opportunities detected yet</div>
            )}
          </div>
          {(data?.upsell_opportunities || []).length > 5 && (
            <button className="pred-expand-btn" onClick={() => setExpandedUpsell(!expandedUpsell)}>
              {expandedUpsell ? "Show Less" : "View All"}
            </button>
          )}
        </div>

        <div className="pred-panel">
          <h3>Ticket Forecast — Next 7 Days</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={ticketChart} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis dataKey="day_name" tick={{ fill: "#888", fontSize: 11 }} tickFormatter={d => d?.slice(0, 3)} />
              <YAxis tick={{ fill: "#888", fontSize: 11 }} />
              <Tooltip content={<DarkTooltip />} />
              <ReferenceLine y={avgTickets} stroke="#666" strokeDasharray="4 4" label={{ value: "Avg", fill: "#666", fontSize: 10 }} />
              <Bar dataKey="predicted_tickets" name="Predicted" radius={[4, 4, 0, 0]}
                fill="#888"
                shape={(props) => {
                  const { x, y, width, height, payload } = props;
                  const color = payload.predicted_tickets > avgTickets ? "#E5484D" : "#30A46C";
                  const isPeak = payload.day_name === data?.ticket_forecast?.peak_day;
                  return (
                    <rect x={x} y={y} width={width} height={height} fill={color}
                      opacity={isPeak ? 1 : 0.85} rx={4}
                      stroke={isPeak ? "#F5A623" : "none"} strokeWidth={isPeak ? 2 : 0}
                    />
                  );
                }}
              />
            </BarChart>
          </ResponsiveContainer>
          <p className="pred-chart-note">{data?.ticket_forecast?.recommendation}</p>
        </div>
      </div>

      {/* ROW 4 — Sentiment Forecast */}
      <div className="pred-panel">
        <div className="pred-panel-header">
          <h3>Sentiment Forecast — Next 7 Days</h3>
          <label className="pred-toggle">
            <input type="checkbox" checked={showActual} onChange={e => setShowActual(e.target.checked)} />
            Actual vs Predicted
          </label>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <ComposedChart data={sentimentChart} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="sentGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#30A46C" stopOpacity={0.4} />
                <stop offset="100%" stopColor="#E5484D" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
            <XAxis dataKey="date" tick={{ fill: "#888", fontSize: 11 }} />
            <YAxis domain={[0, 1]} tick={{ fill: "#888", fontSize: 11 }} />
            <Tooltip content={<DarkTooltip />} />
            <Area type="monotone" dataKey="upper" stroke="none" fill="#30A46C" fillOpacity={0.08} name="Upper bound" />
            <Area type="monotone" dataKey="lower" stroke="none" fill="#1a1a1a" fillOpacity={0.5} name="Lower bound" />
            <Area type="monotone" dataKey="predicted" stroke="#30A46C" fill="url(#sentGrad)" strokeWidth={2} name="Predicted" />
            {showActual && <Line type="monotone" dataKey="actual" stroke="#3B82F6" strokeWidth={2} dot={false} name="Actual" />}
          </ComposedChart>
        </ResponsiveContainer>
        <div className="pred-trend-badge">
          Trend: <strong className={`pred-trend-${data?.sentiment_forecast?.trend_direction}`}>
            {data?.sentiment_forecast?.trend_direction || "stable"}
          </strong>
        </div>
      </div>

      {/* ROW 5 — AI Insights */}
      <div className="pred-panel pred-insights-panel">
        <h3><Sparkles size={16} /> AI Strategic Recommendations</h3>
        <div className="pred-insights-grid">
          {(data?.ai_insights || []).map((ins, i) => (
            <div key={i} className={`pred-insight pred-insight-${ins.priority || "medium"}`}>
              <div className="pred-insight-icon">
                {ins.icon === "alert" ? <AlertTriangle size={16} /> :
                 ins.icon === "revenue" ? <DollarSign size={16} /> :
                 ins.icon === "ticket" ? <Ticket size={16} /> :
                 ins.icon === "users" ? <Users size={16} /> :
                 <TrendingUp size={16} />}
              </div>
              <div className="pred-insight-body">
                <p>{ins.text}</p>
                <div className="pred-insight-footer">
                  <span className={`pred-priority pred-priority-${ins.priority}`}>{ins.priority}</span>
                  <button className="pred-insight-action">{ins.action || "Take Action"}</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
