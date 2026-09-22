import { useState, useEffect, useRef, useCallback } from "react";
import {
  Plus, ArrowUp, MessageSquare, BarChart3, Settings,
  CircleDot, AlertTriangle, X, Clock, Wifi, Inbox, LayoutDashboard, Database, Mic, MicOff, Mail, Users, Headset,
  Volume2, VolumeX, Brain, ChevronDown, ChevronUp, ExternalLink, Sparkles, FileSpreadsheet, Send, Receipt, Package, CheckSquare, Activity, BookOpen
} from "lucide-react";
import "./App.css";
import SettingsView from "./SettingsView";
import TicketsView from "./components/TicketsView";
import KnowledgeBaseView from "./components/KnowledgeBaseView";
import AnalyticsView from "./components/AnalyticsView";
import PredictionsView from "./components/PredictionsView";
import EmailView from "./components/EmailView";
import TelegramView from "./components/TelegramView";
import CrmView from "./components/CrmView";
import BillingView from "./components/BillingView";
import InventoryView from "./components/InventoryView";
import TasksView from "./components/TasksView";
import TenantSwitcher from "./components/TenantSwitcher";
import AgentConsole from "./components/AgentConsole";
import ExcelView from "./components/ExcelView";
import DashboardAnalytics from "./components/DashboardAnalytics";
// Landing page removed

const API = "http://localhost:8000";

const LANGUAGE_META = {
  hi: { name: "Hindi", color: "orange" },
  hin: { name: "Hinglish", color: "orange" },
  bn: { name: "Bengali", color: "green" },
  ta: { name: "Tamil", color: "red" },
  te: { name: "Telugu", color: "blue" },
  mr: { name: "Marathi", color: "purple" },
  gu: { name: "Gujarati", color: "yellow" },
  pa: { name: "Punjabi", color: "indigo" },
  kn: { name: "Kannada", color: "teal" },
  ml: { name: "Malayalam", color: "pink" },
  or: { name: "Odia", color: "orange" },
  ur: { name: "Urdu", color: "green" },
  en: { name: "English", color: "gray" }
};

function speakText(text, lang = "en") {
  if (!window.speechSynthesis) return null;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  
  const TTS_MAP = {
    "hi": "hi-IN", "hin": "hi-IN",
    "ta": "ta-IN", "bn": "bn-IN",
    "te": "te-IN", "mr": "mr-IN",
    "gu": "gu-IN", "kn": "kn-IN",
    "ml": "ml-IN", "pa": "pa-IN",
    "ur": "ur-IN", "or": "or-IN",
    "en": "en-US"
  };
  
  utter.lang = TTS_MAP[lang] || "en-US";
  utter.rate = 0.95;
  const voices = window.speechSynthesis.getVoices();
  const prefix = utter.lang.split("-")[0];
  const match = voices.find(v => v.lang.startsWith(prefix));
  if (match) utter.voice = match;
  window.speechSynthesis.speak(utter);
  return utter;
}

/* ─────────────────────────────────────────────
   LANGUAGE PACK
   ───────────────────────────────────────────── */
const LANG = {
  en: {
    brand: "Chameleon AI",
    greeting: "Welcome to Chameleon AI",
    greetingSub: "Analyze emotions, detect sentiment, and route conversations intelligently.",
    placeholder: "Describe a customer interaction…",
    send: "Send",
    live: "Connected",
    connecting: "Connecting…",
    disconnected: "Offline",
    score: "Score",
    emotion: "Emotion",
    action: "Action",
    botReply: "Response",
    messages: "Conversation Log",
    graph: "Sentiment Timeline",
    empty: "Start a conversation to see analysis",
    voiceReply: "Voice Reply",
    recording: "Recording…",
    memoryPanel: "Customer Memory",
    returningCustomer: "Returning Customer",
    viewProfile: "View Full Profile",
    memoryUsed: "Response personalized based on",
    pastInteractions: "past interactions",
    ticketFromVoice: "Ticket created from voice message",
    alertTitle: "Escalation Required",
    alertSub: "This interaction needs human attention",
    acknowledge: "Acknowledge",
    stats: { total: "Total", escalated: "Escalated", upsells: "Upsells" },
    actions: { ESCALATE: "Escalate", NORMAL: "Normal", UPSELL: "Upsell" },
    emotions: {
      angry: "Angry", frustrated: "Frustrated", neutral: "Neutral",
      happy: "Happy", grateful: "Grateful", curious: "Curious",
      uninterested: "Uninterested"
    },
    sidebar: {
      newChat: "New analysis",
      recent: "Recent",
      today: "Today",
      settings: "Settings",
      livechat: "Live Chat",
      voice: "Voice",
      dashboard: "Dashboard",
      email: "Email",
      tickets: "Tickets",
      analytics: "Analytics",
      predictions: "Predictions",
      excel: "Excel",
      knowledge: "Knowledge Base",
      landing: "Landing Page",
      billing: "Billing",
      inventory: "Inventory",
      tasks: "Tasks"
    },
  },
  hi: {
    brand: "Chameleon AI",
    greeting: "Chameleon AI में आपका स्वागत है",
    greetingSub: "भावनाओं का विश्लेषण करें, भावना का पता लगाएं, और बातचीत को बुद्धिमानी से रूट करें।",
    placeholder: "ग्राहक की बातचीत का वर्णन करें…",
    send: "भेजें",
    live: "जुड़ा हुआ",
    connecting: "जुड़ रहा है…",
    disconnected: "ऑफलाइन",
    score: "स्कोर",
    emotion: "भावना",
    action: "कार्रवाई",
    botReply: "जवाब",
    messages: "बातचीत लॉग",
    graph: "भावना टाइमलाइन",
    empty: "विश्लेषण देखने के लिए बातचीत शुरू करें",
    alertTitle: "एस्केलेशन आवश्यक",
    alertSub: "इस इंटरैक्शन को मानवीय ध्यान की आवश्यकता है",
    acknowledge: "स्वीकार करें",
    stats: { total: "कुल", escalated: "एस्केलेटेड", upsells: "अपसेल" },
    actions: { ESCALATE: "एस्केलेट", NORMAL: "सामान्य", UPSELL: "अपसेल" },
    emotions: {
      angry: "गुस्सा", frustrated: "परेशान", neutral: "सामान्य",
      happy: "खुश", grateful: "शुक्रगुज़ार", curious: "जिज्ञासु",
      uninterested: "उदासीन"
    },
    sidebar: {
      newChat: "नया विश्लेषण",
      recent: "हाल ही में",
      today: "आज",
      settings: "सेटिंग्स",
      inbox: "इनबॉक्स",
      agentDashboard: "एजेंट डैशबोर्ड",
      analytics: "एनालिटिक्स",
      knowledge: "ज्ञानकोष",
      billing: "बिलिंग",
      inventory: "इन्वेंटरी",
      tasks: "कार्य (Tasks)"
    },
  }
};

const ACTION_META = {
  ESCALATE: { color: "#E5484D", bg: "rgba(229,72,77,0.08)",  border: "rgba(229,72,77,0.18)" },
  NORMAL:   { color: "#A0A0A0", bg: "rgba(160,160,160,0.06)", border: "rgba(160,160,160,0.12)" },
  UPSELL:   { color: "#30A46C", bg: "rgba(48,164,108,0.08)",  border: "rgba(48,164,108,0.18)" },
};

function scoreColor(s) {
  if (s < 0.3) return "#E5484D";
  if (s > 0.7) return "#30A46C";
  return "#F5A623";
}

function scoreBg(s) {
  if (s < 0.3) return "rgba(229,72,77,0.1)";
  if (s > 0.7) return "rgba(48,164,108,0.1)";
  return "rgba(245,166,35,0.1)";
}


/* ─────────────────────────────────────────────
   EMOTION ICON & EMOJIS
   ───────────────────────────────────────────── */
const emotionEmoji = {
  angry: "😠", frustrated: "😤", neutral: "😐",
  happy: "😊", grateful: "🙏", curious: "🤔",
  uninterested: "😑"
};

/* ─────────────────────────────────────────────
   CIRCULAR ROTATING CHAMELEON AVATAR
   ───────────────────────────────────────────── */
function ChameleonAvatar() {
  return (
    <div className="chameleon-avatar-container">
      <div 
        className="chameleon-img"
        style={{ 
          width: "40px", 
          height: "40px", 
          minWidth: "40px", 
          minHeight: "40px", 
          borderRadius: "50%", 
          backgroundImage: "url('/chameleon.png')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          display: "block"
        }}
      />
    </div>
  );
}

/* ─────────────────────────────────────────────
   NAVIGATION ITEMS DEFINITION
   ───────────────────────────────────────────── */
const MAIN_NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "crm", label: "CRM", icon: Users },
  { id: "billing", label: "Billing", icon: Receipt },
  { id: "inventory", label: "Inventory", icon: Package },
  { id: "tasks", label: "Tasks", icon: CheckSquare },
  { id: "tickets", label: "Tickets", icon: Inbox },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "predictions", label: "Predictions", icon: Sparkles },
  { id: "excel", label: "Excel", icon: FileSpreadsheet },
];

const CUSTOMER_CARE_ITEMS = [
  { id: "telegram", label: "Telegram", icon: Send, badge: "Bot" },
  { id: "email", label: "Email", icon: Mail, badge: "Caspian" },
  { id: "agentConsole", label: "Agent Console", icon: Headset },
  { id: "knowledge", label: "Knowledge Base", icon: BookOpen },
];

/* ─────────────────────────────────────────────
   MAIN APP
   ───────────────────────────────────────────── */
export default function App() {
  const [lang, setLang]               = useState("en");
  const [msgs, setMsgs]               = useState([]);
  const [status, setStatus]           = useState("connecting");
  const [lastEmotion, setLastEmotion] = useState("neutral");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeView, setActiveView]   = useState("dashboard");
  const [customerCareOpen, setCustomerCareOpen] = useState(true);
  const [toast, setToast]             = useState(null);
  const [customerProfile, setCustomerProfile] = useState(null);
  const [memoryPanelOpen, setMemoryPanelOpen] = useState(true);
  const [customerId, setCustomerId]   = useState(null);

  // Auto-expand Customer Care section if an active item belongs to it
  useEffect(() => {
    if (CUSTOMER_CARE_ITEMS.some((item) => item.id === activeView)) {
      setCustomerCareOpen(true);
    }
  }, [activeView]);

  // System Metrics State
  const [sessionStart] = useState(Date.now());
  const [sessionTime, setSessionTime] = useState({h: 0, m: 0});
  const [ping, setPing] = useState(42);

  // Session Timer Effect
  useEffect(() => {
    const updateTime = () => {
      const diff = Math.floor((Date.now() - sessionStart) / 60000);
      setSessionTime({ h: Math.floor(diff / 60), m: diff % 60 });
    };
    updateTime();
    const interval = setInterval(updateTime, 60000);
    return () => clearInterval(interval);
  }, [sessionStart]);

  // Latency Simulator & History Effect
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${API}/history`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.length > 0) {
            setMsgs(data.slice(-50));
          }
        }
      } catch (e) {
        console.error("Failed to load history", e);
      }
    };
    fetchHistory();
    
    const updatePing = () => {
      const newPing = Math.floor(Math.random() * 50) + 20; 
      const finalPing = Math.random() > 0.9 ? Math.floor(Math.random() * 300) + 100 : newPing;
      setPing(finalPing);
    };
    const interval = setInterval(updatePing, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const onEmail = () => setActiveView("email");
    const onCrm = () => setActiveView("crm");
    window.addEventListener("navigate-email-compose", onEmail);
    window.addEventListener("navigate-crm", onCrm);
    return () => {
      window.removeEventListener("navigate-email-compose", onEmail);
      window.removeEventListener("navigate-crm", onCrm);
    };
  }, []);

  const wsRef  = useRef(null);
  const idxRef = useRef(0);
  const T = LANG[lang];

  const showToast = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  }, []);

  const fetchProfile = useCallback(async (cid) => {
    if (!cid) return;
    try {
      const res = await fetch(`${API}/memory/profile/${encodeURIComponent(cid)}`);
      const data = await res.json();
      setCustomerProfile(data);
    } catch (e) { console.error(e); }
  }, []);

  /* ── WebSocket for live system telemetry ── */
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket("ws://localhost:8000/ws");
      wsRef.current = ws;
      ws.onopen  = () => { setStatus("live"); };
      ws.onclose = () => { setStatus("disconnected"); setTimeout(connect, 3000); };
      ws.onerror = (e) => { console.error("WebSocket error:", e); ws.close(); };
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === "greeting") {
            if (data.profile) setCustomerProfile(data.profile);
            if (data.profile?.customer_identifier) setCustomerId(data.profile.customer_identifier);
            return;
          }
          idxRef.current += 1;
          const point = { ...data, index: idxRef.current, ts: Date.now() };
          if (data.emotion) setLastEmotion(data.emotion);
          setMsgs(prev => [...prev, point].slice(-50));

          if (data.customer_identifier) {
            setCustomerId(data.customer_identifier);
            fetchProfile(data.customer_identifier);
          }

          if (data.ticket_id) {
            showToast(`Support Ticket #${data.ticket_id} updated`);
          }
        } catch (err) {
          console.error("WS message parse error:", err);
        }
      };
    };
    connect();
    return () => wsRef.current?.close();
  }, [fetchProfile, showToast]);

  const statusColor = status === "live" ? "#30A46C" : status === "connecting" ? "#F5A623" : "#E5484D";

  const getIntensity = (emotion) => {
    switch (emotion) {
      case "angry":
      case "frustrated": return 9;
      case "curious": return 5;
      case "happy":
      case "grateful": return 2;
      case "neutral": return 0;
      case "uninterested": return -8;
      default: return 0;
    }
  };

  const intensityScore = getIntensity(lastEmotion);




  return (
    <div className="app-shell">

      {/* ══════════════ SIDEBAR ══════════════ */}
      <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>

        {/* Brand */}
        <div className="sidebar-brand" style={{ display: 'flex', alignItems: 'center' }}>
          <img 
            src="/brand-eye-icon.png" 
            alt="Chameleon AI Eye" 
            className="sidebar-brand-icon w-5 h-5 object-contain inline-block mr-2 invert-[48%] sepia-[79%] saturate-[2476%] hue-rotate-[86deg] brightness-[118%] contrast-[119%]" 
            style={{ width: '20px', height: '20px', display: 'inline-block', marginRight: '8px', verticalAlign: 'middle', filter: 'invert(48%) sepia(79%) saturate(2476%) hue-rotate(86deg) brightness(118%) contrast(119%)' }}
          />
          <span className="sidebar-brand-text">{T.brand}</span>
        </div>

        {/* Analytics Dashboard Quick Link */}
        <button className="sidebar-new-btn" onClick={() => setActiveView("dashboard")}>
          <LayoutDashboard size={15} />
          <span>Analytics Overview</span>
        </button>

        {/* Nav Items */}
        <div className="sidebar-nav mt-4 flex flex-col gap-1 px-3">
          {MAIN_NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                className={`sidebar-nav-btn ${isActive ? "active" : ""}`}
                onClick={() => setActiveView(item.id)}
              >
                <Icon size={15} />
                <span>{item.label}</span>
              </button>
            );
          })}

          {/* ── Collapsible Section: Customer Care ── */}
          <button
            type="button"
            className="sidebar-group-header"
            onClick={() => setCustomerCareOpen(!customerCareOpen)}
            title="Toggle Customer Care channels"
          >
            <div className="sidebar-group-title">
              <Headset size={14} color="#10b981" />
              <span>Customer Care</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span className="sidebar-group-badge">{CUSTOMER_CARE_ITEMS.length}</span>
              {customerCareOpen ? <ChevronUp size={13} color="#94a3b8" /> : <ChevronDown size={13} color="#94a3b8" />}
            </div>
          </button>

          {customerCareOpen && (
            <div className="sidebar-group-items">
              {CUSTOMER_CARE_ITEMS.map((item) => {
                const Icon = item.icon;
                const isActive = activeView === item.id;
                return (
                  <button
                    key={item.id}
                    className={`sidebar-nav-btn nested ${isActive ? "active" : ""}`}
                    onClick={() => setActiveView(item.id)}
                  >
                    <Icon size={14} />
                    <span>{item.label}</span>
                    {item.badge && (
                      <span className="sidebar-badge-pill">{item.badge}</span>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent list */}
        <div className="sidebar-section-label">LIVE TELEMETRY</div>
        <div className="sidebar-list">
          {msgs.length > 0 ? (
            (Array.isArray(msgs) ? [...msgs] : []).reverse().slice(0, 8).map((m, i) => (
              <div key={i} className="sidebar-item slide-in" style={{ animationDelay: `${i * 30}ms` }} onClick={() => setActiveView("dashboard")}>
                <Activity size={13} className="sidebar-item-icon" />
                <span className="sidebar-item-text">
                  {m.message || m.reply || "Telemetry Event"}
                </span>
              </div>
            ))
          ) : (
            <div className="sidebar-empty">
              <span>All systems active</span>
              <br />
              <small style={{ color: "#10b981", fontSize: "11px" }}>● Live Telemetry</small>
            </div>
          )}
        </div>

        {/* System Metrics */}
        <div className="sidebar-metrics">
          <div className="sidebar-metric-row">
            <Clock size={13} className="metric-icon" />
            <span className="metric-label">Session</span>
            <span className="metric-value">{sessionTime.h > 0 ? `${sessionTime.h}h ` : ''}{sessionTime.m}m</span>
          </div>
          <div className="sidebar-metric-row">
            <BarChart3 size={13} className="metric-icon" />
            <span className="metric-label">Analyzed</span>
            <span className="metric-value">{msgs.length}</span>
          </div>
          <div className="sidebar-metric-row">
            <Wifi size={13} className="metric-icon" color={ping < 100 ? '#30A46C' : ping < 300 ? '#F5A623' : '#E5484D'} />
            <span className="metric-label">Latency</span>
            <span className="metric-value" style={{ color: ping < 100 ? '#30A46C' : ping < 300 ? '#F5A623' : '#E5484D' }}>{ping}ms</span>
          </div>
        </div>

        {/* Language + Settings bottom */}
        <div className="sidebar-footer">
          <div className="sidebar-lang">
            {["en", "hi"].map(l => (
              <button
                key={l}
                className={`sidebar-lang-btn ${lang === l ? "active" : ""}`}
                onClick={() => setLang(l)}
              >
                {l.toUpperCase()}
              </button>
            ))}
          </div>
          <button className={`sidebar-settings-btn ${activeView === "settings" ? "bg-white/10 text-white" : ""}`} onClick={() => setActiveView("settings")}>
            <Settings size={15} />
            <span>{T.sidebar.settings}</span>
          </button>
        </div>
      </aside>

      {/* ══════════════ MAIN AREA ══════════════ */}
      <main className="main-area">

        {/* ── Top bar ── */}
        <header className="topbar" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div className="topbar-left">
            <ChameleonAvatar />
            <div className="topbar-status">
              <div className="status-dot" style={{ background: statusColor }} />
              <span style={{ color: statusColor }}>
                {status === "live" ? T.live : status === "connecting" ? T.connecting : T.disconnected}
              </span>
            </div>
          </div>
          <div className="topbar-right" style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <TenantSwitcher />
          </div>
        </header>

        {/* ── Splitted Dashboard Container ── */}
        <div className="main-split-container animate-in fade-in duration-300">
          
          {activeView === "settings" ? (
            <SettingsView lang={lang} setLang={setLang} />
          ) : activeView === "tickets" ? (
            <TicketsView />
          ) : activeView === "knowledge" ? (
            <KnowledgeBaseView />
          ) : activeView === "email" ? (
            <EmailView />
          ) : activeView === "telegram" ? (
            <TelegramView setActiveTab={setActiveView} />
          ) : activeView === "crm" ? (
            <CrmView />
          ) : activeView === "billing" ? (
            <BillingView />
          ) : activeView === "inventory" ? (
            <InventoryView />
          ) : activeView === "tasks" ? (
            <TasksView />
          ) : activeView === "analytics" ? (
            <AnalyticsView />
          ) : activeView === "predictions" ? (
            <PredictionsView />
          ) : activeView === "agentConsole" ? (
            <AgentConsole />
          ) : activeView === "excel" ? (
            <ExcelView />
          ) : (
            <>
              {/* ── LEFT PANE: Modern Responsive Analytics Section (Replaced Chat) ── */}
              <div className="chat-pane" style={{ overflowY: "auto", minWidth: 0, flex: 1 }}>
                <DashboardAnalytics />
              </div>

          {/* ── RIGHT PANE: Emotional Intensity Meter ── */}
          <div className="analytics-pane">
            <div className="analytics-header">
              <h3 className="section-title-serif">LIVE AGENT MOOD LEVEL</h3>
              <p className="analytics-subtitle">Real-time dialectical arousal tracking</p>
            </div>

            {/* Vertical Scale Meter */}
            <div className="intensity-meter-wrapper">
              <div className="intensity-labels-left">
                <div className="i-label i-red">
                  <span className="i-num">10</span>
                  <div className="i-text"><strong>RED:</strong> Overwhelmed Emotion Is Favored Over Reason</div>
                </div>
                <div className="i-label i-yellow">
                  <span className="i-num">5</span>
                  <div className="i-text"><strong>YELLOW/GREEN:</strong> On the edge / Calm Reason Is Favored</div>
                </div>
                <div className="i-label i-blue">
                  <span className="i-num">-10</span>
                  <div className="i-text"><strong>BLUE:</strong> Detached Intense Emotion Is Numbed</div>
                </div>
              </div>

              <div className="intensity-scale-track">
                <div 
                  className="intensity-pointer" 
                  style={{ top: `${50 - (intensityScore * 5)}%` }}
                >
                  <div className="pointer-arrow"></div>
                  <div className="pointer-glow"></div>
                </div>
              </div>
            </div>

            {/* Action Strategy Grid */}
            <div className="strategy-section-title">EMOTION-BASED ACTION STRATEGY</div>
            <div className="strategy-grid">
              
              <div className={`strategy-card sc-red ${intensityScore >= 7 ? 'active' : ''}`}>
                <div className="sc-header">High Intensity (7-10)</div>
                <div className="sc-body">
                  <strong>Strategy:</strong> Provide immediate empathy, validation, or special retention discount. DO NOT push sales.
                </div>
                <div className="sc-timing">Timing: IMMEDIATE</div>
              </div>

              <div className={`strategy-card sc-green ${intensityScore > -5 && intensityScore < 7 ? 'active' : ''}`}>
                <div className="sc-header">Calm / Low Intensity (-4 to 6)</div>
                <div className="sc-body">
                  <strong>Strategy:</strong> Introduce upgrade options or bundle offers naturally.
                </div>
                <div className="sc-timing">Timing: AFTER RESOLUTION</div>
              </div>

              <div className={`strategy-card sc-blue ${intensityScore <= -5 ? 'active' : ''}`}>
                <div className="sc-header">Detached (-5 to -10)</div>
                <div className="sc-body">
                  <strong>Strategy:</strong> Offer deep service recovery, proactive problem-solving, or value-add features.
                </div>
                <div className="sc-timing">Timing: MID-INTERACTION</div>
              </div>

            </div>

            {/* ── Customer Memory Panel ── */}
            <div className={`memory-panel ${memoryPanelOpen ? "open" : "collapsed"}`}>
              <button className="memory-panel-toggle" onClick={() => setMemoryPanelOpen(!memoryPanelOpen)}>
                <Brain size={14} />
                <span>{T.memoryPanel}</span>
                {memoryPanelOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
              {memoryPanelOpen && (
                <div className="memory-panel-body">
                  {customerProfile?.is_returning ? (
                    <>
                      <span className="returning-badge">{T.returningCustomer}</span>
                      <div className="memory-name">{customerProfile.display_name}</div>
                      <div className="memory-stat">
                        <span>{customerProfile.interaction_count || 0}</span> past interactions
                      </div>
                      {customerProfile.common_issues?.length > 0 && (
                        <div className="memory-issues">
                          {(Array.isArray(customerProfile.common_issues) ? customerProfile.common_issues : []).map((issue, i) => (
                            <span key={i} className="memory-chip">{issue}</span>
                          ))}
                        </div>
                      )}
                      <p className="memory-personality">{customerProfile.personality_summary}</p>
                      {customerProfile.last_visit && (
                        <div className="memory-last-visit">
                          Last visit: {new Date(customerProfile.last_visit).toLocaleDateString()}
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="memory-empty">New customer — no history yet</p>
                  )}
                  <button className="memory-profile-btn" onClick={() => setActiveView("crm")}>
                    <ExternalLink size={13} />
                    {T.viewProfile}
                  </button>
                </div>
              )}
            </div>
          </div>

            </>
          )}
        </div>
      </main>

      {toast && (
        <div className="toast-notification">{toast}</div>
      )}
    </div>
  );
}
