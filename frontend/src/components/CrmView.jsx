import { useState, useEffect, useRef } from "react";
import { Users, Target, Activity, DollarSign, Brain, Search, Plus, Trash2, Calendar, FileText, ArrowLeft, Mail, MessageSquare, Mic, Ticket, X, Send } from "lucide-react";
import "./CrmView.css";

const API = "http://localhost:8000";

const STAGES = ["lead", "qualified", "proposal", "negotiation", "won", "lost"];
const STAGE_LABELS = {
  lead: "Lead", qualified: "Qualified", proposal: "Proposal",
  negotiation: "Negotiation", won: "Won", lost: "Lost"
};

const STATUS_COLORS = {
  lead: { bg: "rgba(59,130,246,0.1)", text: "#3B82F6" },
  prospect: { bg: "rgba(245,166,35,0.1)", text: "#F5A623" },
  customer: { bg: "rgba(48,164,108,0.1)", text: "#30A46C" },
  churned: { bg: "rgba(229,72,77,0.1)", text: "#E5484D" }
};

const SOURCE_COLORS = {
  chat: { bg: "rgba(48,164,108,0.12)", text: "#30A46C" },
  email: { bg: "rgba(59,130,246,0.12)", text: "#3B82F6" },
  manual: { bg: "rgba(160,160,160,0.1)", text: "#A0A0A0" },
};

export default function CrmView() {
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [deals, setDeals] = useState([]);
  const [pipeline, setPipeline] = useState({});
  const [loading, setLoading] = useState(true);

  // Profile specific
  const [selectedProfileId, setSelectedProfileId] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [aiSummary, setAiSummary] = useState(null);
  const [generatingSummary, setGeneratingSummary] = useState(false);
  const [newNote, setNewNote] = useState("");
  const [newTag, setNewTag] = useState("");

  const [forecastData, setForecastData] = useState(null);
  const [forecasting, setForecasting] = useState(false);
  const [showAddDeal, setShowAddDeal] = useState(false);
  const [newDeal, setNewDeal] = useState({ title: "", value: 0, stage: "lead", customer_id: "", expected_close: "" });

  const fetchData = async () => {
    try {
      const [stRes, cRes, dRes, pRes] = await Promise.all([
        fetch(`${API}/crm/stats`),
        fetch(`${API}/crm/customers`),
        fetch(`${API}/crm/deals`),
        fetch(`${API}/crm/pipeline`)
      ]);
      setStats(await stRes.json());
      setCustomers(await cRes.json());
      setDeals(await dRes.json());
      setPipeline(await pRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { 
    if(activeTab !== "profile") {
      fetchData(); 
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === "profile" && selectedProfileId) {
      loadProfile(selectedProfileId);
    }
  }, [selectedProfileId, activeTab]);

  const loadProfile = async (id) => {
    console.log("Fetching profile data for ID:", id);
    // Show loading state by setting profileData to null initially
    setProfileData(null);
    try {
      const res = await fetch(`${API}/crm/customers/${id}/profile`);
      if (res.ok) {
        const data = await res.json();
        console.log("Profile Data loaded:", data);
        setProfileData(data);
        setNewNote(data?.profile?.notes || "");
      } else {
        console.error("API returned error status:", res.status);
      }
    } catch(e) {
      console.error("Failed to load profile:", e);
    }
  };

  // Actions
  const handleGenerateForecast = async () => {
    setForecasting(true);
    try {
      const res = await fetch(`${API}/crm/forecast`, { method: "POST" });
      setForecastData(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setForecasting(false);
    }
  };

  const openCustomer = (cust) => {
    setSelectedProfileId(cust.id);
    setActiveTab("profile");
    setAiSummary(null); // reset
  };

  const generateRiskScore = async () => {
    if(!selectedProfileId) return;
    try {
      const res = await fetch(`${API}/crm/customers/${selectedProfileId}/recalculate-risk`, { method: "POST" });
      const data = await res.json();
      alert(`AI Risk Analysis:\nScore: ${data.risk_score}\nReason: ${data.reason}\nAction: ${data.recommendation}`);
      loadProfile(selectedProfileId);
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerateSummary = async () => {
    if(!selectedProfileId) return;
    setGeneratingSummary(true);
    try {
      const res = await fetch(`${API}/crm/customers/${selectedProfileId}/summary`, { method: "POST" });
      const data = await res.json();
      setAiSummary(data);
    } catch(e) {
      console.error(e);
    } finally {
      setGeneratingSummary(false);
    }
  };

  const handleUpdateNotes = async () => {
    try {
      await fetch(`${API}/crm/customers/${selectedProfileId}/update-notes`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: newNote })
      });
      alert("Notes updated");
      loadProfile(selectedProfileId);
    } catch(e) { console.error(e); }
  };

  const handleAddTag = async (e) => {
    e.preventDefault();
    if(!newTag.trim()) return;
    try {
      const currentTags = profileData?.profile?.tags ? profileData.profile.tags.split(",").filter(t=>t) : [];
      if(!currentTags.includes(newTag.trim())) {
        currentTags.push(newTag.trim());
        await fetch(`${API}/crm/customers/${selectedProfileId}/update-tags`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tags: currentTags.join(",") })
        });
        setNewTag("");
        loadProfile(selectedProfileId);
      }
    } catch(e) { console.error(e); }
  };

  const removeTag = async (tagToRemove) => {
    try {
      const currentTags = profileData?.profile?.tags ? profileData.profile.tags.split(",").filter(t=>t) : [];
      const newTags = currentTags.filter(t => t !== tagToRemove);
      await fetch(`${API}/crm/customers/${selectedProfileId}/update-tags`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tags: newTags.join(",") })
      });
      loadProfile(selectedProfileId);
    } catch(e) { console.error(e); }
  };

  const createDeal = async () => {
    try {
      await fetch(`${API}/crm/deals`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({...newDeal, customer_id: parseInt(newDeal.customer_id) || selectedProfileId})
      });
      setShowAddDeal(false);
      if (activeTab === "profile") {
        loadProfile(selectedProfileId);
      } else {
        fetchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const deleteCustomer = async () => {
    if(window.confirm("Are you sure you want to delete this customer? This cannot be undone.")) {
      try {
        await fetch(`${API}/crm/customers/${selectedProfileId}`, { method: "DELETE" });
        setActiveTab("customers");
      } catch(e) { console.error(e); }
    }
  };

  // Drag and Drop for Kanban
  const handleDragStart = (e, dealId) => {
    e.dataTransfer.setData("dealId", dealId);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = async (e, stage) => {
    const dealId = e.dataTransfer.getData("dealId");
    if(!dealId) return;
    try {
      await fetch(`${API}/crm/deals/${dealId}`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage })
      });
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const getInitials = (name) => {
    if(!name) return "?";
    return name.split(" ").map(n => n[0]).join("").substring(0,2).toUpperCase();
  };

  const getRiskColor = (score) => {
    if(score < 0.3) return '#E5484D'; // Red
    if(score < 0.7) return '#F5A623'; // Yellow
    return '#30A46C'; // Green
  };

  // SVG Chart Generator for Sentiment Trend
  const renderSentimentChart = (trend) => {
    if(!trend || trend.length === 0) return <div className="text-gray-500 text-sm">Not enough data</div>;
    
    // Scale X from 0 to 100% of width
    // Scale Y from 0 to 1 (score is 0-1), map to 100 to 0 (SVG y is inverted)
    const points = trend.map((t, i) => {
      const x = trend.length > 1 ? (i / (trend.length - 1)) * 100 : 50;
      const y = 100 - (t.sentiment_score * 100);
      return `${x},${y}`;
    }).join(" ");

    return (
      <div className="sentiment-chart-wrapper">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="sentiment-svg">
          {/* Grid lines */}
          <line x1="0" y1="25" x2="100" y2="25" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5"/>
          <line x1="0" y1="50" x2="100" y2="50" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5"/>
          <line x1="0" y1="75" x2="100" y2="75" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5"/>
          
          <polyline
            fill="none"
            stroke="url(#gradient)"
            strokeWidth="3"
            points={points}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          
          <defs>
            <linearGradient id="gradient" x1="0%" y1="100%" x2="0%" y2="0%">
              <stop offset="0%" stopColor="#E5484D" />
              <stop offset="50%" stopColor="#F5A623" />
              <stop offset="100%" stopColor="#30A46C" />
            </linearGradient>
          </defs>

          {/* Dots */}
          {trend.map((t, i) => {
            const x = trend.length > 1 ? (i / (trend.length - 1)) * 100 : 50;
            const y = 100 - (t.sentiment_score * 100);
            return (
              <circle key={i} cx={x} cy={y} r="2" fill="#fff" className="chart-dot">
                <title>{new Date(t.created_at).toLocaleDateString()}: {t.sentiment_score}</title>
              </circle>
            )
          })}
        </svg>
        <div className="chart-labels">
          <span>Oldest</span>
          <span>Newest</span>
        </div>
      </div>
    );
  };

  const getIconForType = (type) => {
    switch(type) {
      case 'email': 
      case 'caspian-email': return <Mail size={14} className="text-blue-400"/>;
      case 'chat': 
      case 'dashboard': return <MessageSquare size={14} className="text-green-400"/>;
      case 'caspian-telegram': return <Send size={14} className="text-blue-400"/>;
      case 'ticket': return <Ticket size={14} className="text-purple-400"/>;
      case 'voice': return <Mic size={14} className="text-green-400"/>;
      default: return <MessageSquare size={14} className="text-gray-400"/>;
    }
  };

  const SourceBadge = ({ source }) => {
    const s = source || "manual";
    const colors = SOURCE_COLORS[s] || SOURCE_COLORS.manual;
    return (
      <span className="crm-badge source-badge" style={{ background: colors.bg, color: colors.text }}>
        {s.toUpperCase()}
      </span>
    );
  };

  if (loading) return <div className="crm-loading">Loading CRM...</div>;

  return (
    <div className="crm-view">
      {/* HEADER NAV */}
      <div className="crm-header">
        <h2 className="crm-title">
          {activeTab === "profile" ? (
            <div className="flex items-center gap-2 cursor-pointer hover:text-gray-300" onClick={() => setActiveTab("customers")}>
              <ArrowLeft size={20} /> Back to Customers
            </div>
          ) : "SmartCare CRM"}
        </h2>
        {activeTab !== "profile" && (
          <div className="crm-tabs">
            {["overview", "customers", "pipeline", "deals"].map(t => (
              <button 
                key={t} 
                className={`crm-tab-btn ${activeTab === t ? "active" : ""}`}
                onClick={() => setActiveTab(t)}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="crm-content">
        {/* ================= OVERVIEW TAB ================= */}
        {activeTab === "overview" && stats && (
          <div className="crm-overview animate-in fade-in">
            <div className="crm-kpi-grid">
              <div className="crm-kpi-card">
                <div className="kpi-icon bg-blue"><Users size={18}/></div>
                <div className="kpi-info"><span>Total Customers</span><strong>{stats.total_customers}</strong></div>
              </div>
              <div className="crm-kpi-card">
                <div className="kpi-icon bg-emerald"><Plus size={18}/></div>
                <div className="kpi-info"><span>New This Month</span><strong>{stats.new_this_month}</strong></div>
              </div>
              <div className="crm-kpi-card">
                <div className="kpi-icon bg-purple"><Target size={18}/></div>
                <div className="kpi-info"><span>Pipeline Value</span><strong>${stats.total_deals_value.toLocaleString()}</strong></div>
              </div>
              <div className="crm-kpi-card">
                <div className="kpi-icon bg-green"><DollarSign size={18}/></div>
                <div className="kpi-info"><span>Won Revenue</span><strong>${stats.won_deals_value.toLocaleString()}</strong></div>
              </div>
              <div className="crm-kpi-card">
                <div className="kpi-icon bg-red"><Activity size={18}/></div>
                <div className="kpi-info"><span>At-Risk Customers</span><strong className={stats.at_risk_customers > 0 ? "text-red-500" : ""}>{stats.at_risk_customers}</strong></div>
              </div>
              <div className="crm-kpi-card">
                <div className="kpi-icon bg-yellow"><Activity size={18}/></div>
                <div className="kpi-info"><span>Win Rate</span><strong>{stats.conversion_rate}%</strong></div>
              </div>
            </div>

            <div className="crm-forecast-panel">
              <div className="forecast-header">
                <h3><Brain size={18}/> AI Revenue Forecast</h3>
                <button className="btn-primary" onClick={handleGenerateForecast} disabled={forecasting}>
                  {forecasting ? "Analyzing..." : "Generate AI Forecast"}
                </button>
              </div>
              {forecastData ? (
                <div className="forecast-body">
                  <div className="forecast-bars">
                    <div className="f-bar-wrap">
                      <div className="f-bar" style={{height: '60%'}}></div>
                      <span>30 Days: ${forecastData.forecast["30_days"]}</span>
                    </div>
                    <div className="f-bar-wrap">
                      <div className="f-bar" style={{height: '80%'}}></div>
                      <span>60 Days: ${forecastData.forecast["60_days"]}</span>
                    </div>
                    <div className="f-bar-wrap">
                      <div className="f-bar" style={{height: '100%'}}></div>
                      <span>90 Days: ${forecastData.forecast["90_days"]}</span>
                    </div>
                  </div>
                  <div className="forecast-top-deals">
                    <h4>Top Deals to Focus On</h4>
                    {forecastData.top_deals.map((id, i) => {
                      const d = deals.find(x => x.id === id);
                      return d ? <div key={i} className="f-deal">⭐ {d.title} (${d.value})</div> : null;
                    })}
                  </div>
                </div>
              ) : (
                <div className="forecast-empty">Click generate to let AI analyze your pipeline and predict upcoming revenue.</div>
              )}
            </div>
          </div>
        )}

        {/* ================= CUSTOMERS TAB ================= */}
        {activeTab === "customers" && (
          <div className="crm-table-container animate-in fade-in">
            <div className="crm-table-header">
              <div className="search-box">
                <Search size={16}/> <input type="text" placeholder="Search customers..." />
              </div>
            </div>
            <table className="crm-table">
              <thead>
                <tr>
                  <th>Name</th><th>Company</th><th>Source</th><th>Status</th><th>Risk Score</th><th>Avg Sentiment</th><th>Last Contact</th>
                </tr>
              </thead>
              <tbody>
                {customers.map(c => (
                  <tr key={c.id} onClick={() => openCustomer(c)}>
                    <td>
                      <div className="font-semibold text-white">{c.name}</div>
                      <div className="text-xs text-gray-400">{c.email}</div>
                    </td>
                    <td>{c.company || "-"}</td>
                    <td><SourceBadge source={c.source} /></td>
                    <td>
                      <span className="crm-badge" style={{background: STATUS_COLORS[c.status]?.bg, color: STATUS_COLORS[c.status]?.text}}>
                        {c.status.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <div className="risk-bar-container">
                        <div className="risk-bar-fill" style={{width: `${c.risk_score * 100}%`, background: getRiskColor(c.risk_score)}}></div>
                      </div>
                    </td>
                    <td>{c.avg_sentiment.toFixed(2)}</td>
                    <td>{new Date(c.last_contact || c.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ================= FULL PAGE PROFILE TAB ================= */}
        {activeTab === "profile" && !profileData && (
          <div className="crm-loading">Loading customer profile...</div>
        )}
        
        {activeTab === "profile" && profileData && profileData.profile && (
          <div className="crm-profile-view animate-in fade-in">
            <div className="profile-grid-3">
              
              {/* LEFT PANEL */}
              <div className="prof-col prof-left">
                <div className="prof-card text-center relative">
                  <div className="prof-avatar mx-auto" style={{borderColor: getRiskColor(profileData.profile.risk_score)}}>
                    {getInitials(profileData.profile.name)}
                  </div>
                  <h3 className="mt-4 mb-1 text-xl font-bold">{profileData.profile.name}</h3>
                  <div className="text-sm text-gray-400 mb-4">{profileData.profile.email}</div>
                  
                  <div className="flex justify-center gap-2 mb-6">
                    <span className="crm-badge" style={{background: STATUS_COLORS[profileData.profile.status || 'lead']?.bg, color: STATUS_COLORS[profileData.profile.status || 'lead']?.text}}>
                      {(profileData.profile.status || 'lead').toUpperCase()}
                    </span>
                    <SourceBadge source={profileData.profile.source} />
                  </div>

                  <div className="risk-dial-container mb-6">
                    <div className="risk-dial" style={{background: `conic-gradient(${getRiskColor(profileData.profile.risk_score || 0)} ${(profileData.profile.risk_score || 0) * 100}%, #222 0)`}}>
                      <div className="risk-dial-inner">
                        <span style={{color: getRiskColor(profileData.profile.risk_score || 0)}}>{(profileData.profile.risk_score || 0).toFixed(2)}</span>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-2">AI Risk Score</div>
                    <button className="btn-outline-small w-full mt-3" onClick={generateRiskScore}><Brain size={12}/> Recalculate Risk</button>
                  </div>
                </div>

                <div className="prof-card">
                  <h4>Quick Stats</h4>
                  <div className="stats-list">
                    <div className="stat-row"><span>Interactions:</span> <strong>{profileData.total_interactions || 0}</strong></div>
                    <div className="stat-row"><span>Avg Sentiment:</span> <strong>{(profileData.profile.avg_sentiment || 0).toFixed(2)}</strong></div>
                    <div className="stat-row"><span>Total Revenue:</span> <strong>${(profileData.profile.revenue_generated || 0).toLocaleString()}</strong></div>
                    <div className="stat-row"><span>Open Tickets:</span> <strong>{(profileData.tickets || []).filter(t=>t.status !== 'resolved').length}</strong></div>
                    <div className="stat-row"><span>First Contact:</span> <strong>{profileData.profile.created_at ? new Date(profileData.profile.created_at).toLocaleDateString() : '-'}</strong></div>
                  </div>
                </div>

                <div className="prof-card">
                  <h4>Notes</h4>
                  <textarea 
                    className="notes-area" 
                    value={newNote} 
                    onChange={e => setNewNote(e.target.value)}
                    placeholder="Add customer notes here..."
                  />
                  <button className="btn-outline-small mt-2 w-full" onClick={handleUpdateNotes}>Save Notes</button>
                </div>

                <button className="btn-outline-small text-red-500 border-red-900 w-full hover:bg-red-900" onClick={deleteCustomer}>
                  <Trash2 size={14}/> Delete Customer
                </button>
              </div>

              {/* MIDDLE PANEL */}
              <div className="prof-col prof-middle">
                <div className="prof-card ai-summary-card">
                  <div className="flex-between mb-3">
                    <h4 className="m-0 flex items-center gap-2"><Brain size={16} className="text-purple-400"/> AI Customer Summary</h4>
                    <button className="btn-primary text-xs py-1" onClick={handleGenerateSummary} disabled={generatingSummary}>
                      {generatingSummary ? "Thinking..." : "Generate Summary"}
                    </button>
                  </div>
                  {aiSummary ? (
                    <div className="ai-summary-content">
                      <p className="summary-text">{aiSummary.summary}</p>
                      <div className="summary-meta">
                        <div className="meta-box">
                          <span className="meta-label">Risk Level</span>
                          <strong className={aiSummary.risk_level.includes("High") ? "text-red-400" : "text-green-400"}>{aiSummary.risk_level}</strong>
                        </div>
                        <div className="meta-box flex-1">
                          <span className="meta-label">Recommended Action</span>
                          <strong>{aiSummary.recommended_action}</strong>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-gray-500 text-sm italic py-4 text-center">Click generate to let AI analyze all past interactions and summarize this relationship.</div>
                  )}
                </div>

                <div className="prof-card">
                  <h4>Sentiment Trend (Last 10)</h4>
                  {renderSentimentChart(profileData.sentiment_trend)}
                </div>

                <div className="prof-card flex-1 flex flex-col">
                  <h4>Activity Timeline</h4>
                  <div className="timeline-container">
                    <div className="timeline">
                      {profileData.timeline && profileData.timeline.length > 0 ? profileData.timeline.map((t, i) => (
                        <div key={i} className="timeline-item">
                          <div className="t-dot t-dot-icon">{getIconForType(t.type)}</div>
                          <div className="t-content">
                            <span className="t-time">{new Date(t.created_at).toLocaleString()}</span>
                            <span className="t-type badge-small capitalize">{t.type}</span>
                            <p>{t.description}</p>
                            {t.sentiment_score !== null && (
                              <span className="t-sent" style={{color: getRiskColor(t.sentiment_score)}}>
                                Sentiment: {t.sentiment_score}
                              </span>
                            )}
                          </div>
                        </div>
                      )) : <div className="text-gray-500 text-sm">No activity recorded yet.</div>}
                    </div>
                  </div>
                </div>
              </div>

              {/* RIGHT PANEL */}
              <div className="prof-col prof-right">
                
                <div className="prof-card">
                  <div className="flex-between mb-3">
                    <h4 className="m-0">Tags</h4>
                  </div>
                  <div className="tags-container mb-3">
                    {(profileData.profile.tags ? profileData.profile.tags.split(",") : []).filter(t=>t).map((tag, i) => (
                      <span key={i} className="tag-chip">
                        {tag} <button onClick={() => removeTag(tag)}><X size={10}/></button>
                      </span>
                    ))}
                  </div>
                  <form onSubmit={handleAddTag} className="flex gap-2">
                    <input type="text" className="input-small flex-1" placeholder="Add tag..." value={newTag} onChange={e=>setNewTag(e.target.value)} />
                    <button type="submit" className="btn-outline-small">Add</button>
                  </form>
                </div>

                <div className="prof-card">
                  <div className="flex-between mb-3">
                    <h4 className="m-0">Linked Deals</h4>
                    <button className="btn-outline-small" onClick={() => { setNewDeal({...newDeal, customer_id: selectedProfileId}); setShowAddDeal(true); }}><Plus size={12}/></button>
                  </div>
                  <div className="linked-list">
                    {profileData.deals && profileData.deals.length > 0 ? profileData.deals.map(d => (
                      <div key={d.id} className="linked-item">
                        <div className="font-semibold">{d.title}</div>
                        <div className="flex-between text-sm mt-1">
                          <span className="text-green-400">${d.value.toLocaleString()}</span>
                          <span className={`kanban-badge ${d.stage} scale-75 origin-right`}>{STAGE_LABELS[d.stage]}</span>
                        </div>
                      </div>
                    )) : <div className="text-gray-500 text-sm">No deals.</div>}
                  </div>
                </div>

                <div className="prof-card">
                  <h4>Support Tickets</h4>
                  <div className="linked-list">
                    {profileData.tickets && profileData.tickets.length > 0 ? profileData.tickets.map(t => (
                      <div key={t.id} className="linked-item">
                        <div className="text-sm font-semibold truncate">#{t.id} - {t.issue}</div>
                        <div className="flex-between text-xs mt-1 text-gray-400">
                          <span className="uppercase">{t.status}</span>
                          <span className={t.priority === 'urgent' ? 'text-red-400' : ''}>{t.priority}</span>
                        </div>
                      </div>
                    )) : <div className="text-gray-500 text-sm">No tickets.</div>}
                  </div>
                </div>

              </div>

            </div>
          </div>
        )}

        {/* ================= PIPELINE (KANBAN) TAB ================= */}
        {activeTab === "pipeline" && (
          <div className="crm-kanban animate-in fade-in">
            {STAGES.map(stage => {
              const colDeals = pipeline[stage]?.deals || [];
              const colValue = pipeline[stage]?.total_value || 0;
              return (
                <div 
                  key={stage} 
                  className="kanban-col"
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, stage)}
                >
                  <div className={`kanban-col-header ${stage}`}>
                    <span className="col-title">{STAGE_LABELS[stage]} ({colDeals.length})</span>
                    <span className="col-val">${colValue.toLocaleString()}</span>
                  </div>
                  <div className="kanban-cards">
                    {colDeals.map(d => (
                      <div 
                        key={d.id} 
                        className="kanban-card"
                        draggable
                        onDragStart={(e) => handleDragStart(e, d.id)}
                      >
                        <div className="k-card-title">{d.title}</div>
                        <div className="k-card-val">${d.value.toLocaleString()}</div>
                        <div className="k-card-cust"><Users size={12}/> {d.customer_name}</div>
                        <div className="k-card-meta">
                          <span>{d.probability}% Prob</span>
                          <span><Calendar size={12}/> {new Date(d.expected_close).toLocaleDateString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ================= DEALS TAB ================= */}
        {activeTab === "deals" && (
          <div className="crm-table-container animate-in fade-in">
            <div className="crm-table-header">
              <h3>All Deals</h3>
              <button className="btn-primary" onClick={() => setShowAddDeal(true)}><Plus size={16}/> Add Deal</button>
            </div>
            <table className="crm-table">
              <thead>
                <tr>
                  <th>Title</th><th>Customer</th><th>Value</th><th>Stage</th><th>Probability</th><th>Expected Close</th>
                </tr>
              </thead>
              <tbody>
                {deals.map(d => (
                  <tr key={d.id}>
                    <td className="font-semibold text-white">{d.title}</td>
                    <td>{d.customer_name}</td>
                    <td>${d.value.toLocaleString()}</td>
                    <td>
                      <span className={`kanban-badge ${d.stage}`}>{STAGE_LABELS[d.stage]}</span>
                    </td>
                    <td>{d.probability}%</td>
                    <td>{new Date(d.expected_close).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ADD DEAL MODAL */}
      {showAddDeal && (
        <div className="modal-overlay" onClick={() => setShowAddDeal(false)}>
          <div className="crm-modal" onClick={e => e.stopPropagation()}>
            <h3>New Deal</h3>
            <div className="form-group">
              <label>Customer</label>
              <select value={newDeal.customer_id} onChange={e => setNewDeal({...newDeal, customer_id: e.target.value})}>
                <option value="">Select Customer...</option>
                {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Deal Title</label>
              <input type="text" value={newDeal.title} onChange={e => setNewDeal({...newDeal, title: e.target.value})} />
            </div>
            <div className="form-group">
              <label>Value ($)</label>
              <input type="number" value={newDeal.value} onChange={e => setNewDeal({...newDeal, value: parseFloat(e.target.value)})} />
            </div>
            <div className="form-group">
              <label>Expected Close</label>
              <input type="date" value={newDeal.expected_close} onChange={e => setNewDeal({...newDeal, expected_close: e.target.value})} />
            </div>
            <div className="modal-actions">
              <button className="btn-outline" onClick={() => setShowAddDeal(false)}>Cancel</button>
              <button className="btn-primary" onClick={createDeal}>Create Deal</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
