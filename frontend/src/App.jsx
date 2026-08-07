import { useState, useEffect, useRef, useCallback } from "react";
import {
  Plus, ArrowUp, MessageSquare, BarChart3, Settings,
  CircleDot, AlertTriangle, X, Clock, Wifi, Inbox, LayoutDashboard, Database, Mic, MicOff, Mail, Users, Headset,
  Volume2, VolumeX, Brain, ChevronDown, ChevronUp, ExternalLink, Sparkles, FileSpreadsheet, Send
} from "lucide-react";
import "./App.css";
import SettingsView from "./SettingsView";
import TicketsView from "./components/TicketsView";
import KnowledgeBaseView from "./components/KnowledgeBaseView";
import AnalyticsView from "./components/AnalyticsView";
import PredictionsView from "./components/PredictionsView";
import EmailView from "./components/EmailView";
import CrmView from "./components/CrmView";
import AgentConsole from "./components/AgentConsole";
import ExcelView from "./components/ExcelView";
import LandingPage from "./components/landing/LandingPage";

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
    brand: "Sentiment AI",
    greeting: "Welcome to Sentiment AI",
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
      landing: "Landing Page"
    },
  },
  hi: {
    brand: "Sentiment AI",
    greeting: "Sentiment AI में आपका स्वागत है",
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
      knowledge: "ज्ञानकोष"
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
   MAIN APP
   ───────────────────────────────────────────── */
export default function App() {
  const [lang, setLang]               = useState("en");
  const [msgs, setMsgs]               = useState([]);
  const [graphData, setGraph]         = useState([]);
  const [input, setInput]             = useState("");
  const [status, setStatus]           = useState("connecting");
  const [lastEmotion, setLastEmotion] = useState("neutral");
  const [alert, setAlert]             = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeView, setActiveView]   = useState("landing");
  const [activeTicketId, setActiveTicketId] = useState(null);
  const [channelFilter, setChannelFilter] = useState("All Channels");

  // Voice + Memory state
  const [voiceOn, setVoiceOn]         = useState(false);
  const [recording, setRecording]     = useState(false);
  const [recordTime, setRecordTime]   = useState(0);
  const [speaking, setSpeaking]       = useState(false);
  const [micError, setMicError]       = useState(null);
  const [toast, setToast]             = useState(null);
  const [customerProfile, setCustomerProfile] = useState(null);
  const [memoryPanelOpen, setMemoryPanelOpen] = useState(true);
  const [smartGreeting, setSmartGreeting] = useState(null);
  const [customerId, setCustomerId]   = useState(null);
  const [waveBars, setWaveBars]       = useState(Array(12).fill(4));

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

  // Latency Simulator Effect
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${API}/history`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.length > 0) {
            setMsgs(data.slice(-100)); // Load up to 100 recent
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

  const wsRef    = useRef(null);
  const idxRef   = useRef(0);
  const chatEnd  = useRef(null);
  const inputRef = useRef(null);
  const mediaRecRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const waveAnimRef = useRef(null);
  const recordTimeRef = useRef(0);
  const voiceOnRef = useRef(voiceOn);
  const langRef = useRef(lang);
  const T = LANG[lang];

  useEffect(() => { voiceOnRef.current = voiceOn; }, [voiceOn]);
  useEffect(() => { langRef.current = lang; }, [lang]);

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

  /* ── WebSocket ── */
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket("ws://localhost:8000/ws");
      wsRef.current = ws;
      ws.onopen  = () => setStatus("live");
      ws.onclose = () => { setStatus("disconnected"); setTimeout(connect, 3000); };
      ws.onerror = () => ws.close();
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);

        if (data.type === "greeting") {
          setSmartGreeting(data.message);
          if (data.profile) setCustomerProfile(data.profile);
          if (data.profile?.customer_identifier) setCustomerId(data.profile.customer_identifier);
          return;
        }

        idxRef.current += 1;
        const point = { ...data, index: idxRef.current, ts: Date.now() };
        setLastEmotion(data.emotion);
        setMsgs(prev => [...prev, point].slice(-100));
        setGraph(prev => [...prev, point].slice(-30));

        if (data.customer_identifier) {
          setCustomerId(data.customer_identifier);
          fetchProfile(data.customer_identifier);
        }

        if (data.ticket_id) {
          showToast(`Ticket #${data.ticket_id} created from voice message`);
        }

        if (voiceOnRef.current && data.reply) {
          setSpeaking(true);
          const utter = speakText(data.reply, data.language || langRef.current);
          if (utter) utter.onend = () => setSpeaking(false);
          else setSpeaking(false);
        }

        if (data.action === "ESCALATE") {
          setAlert(data);
        }
      };
    };
    connect();
    return () => wsRef.current?.close();
  }, [fetchProfile, showToast]);

  useEffect(() => () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (waveAnimRef.current) cancelAnimationFrame(waveAnimRef.current);
  }, []);

  const sendWs = useCallback((payload) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    const text = typeof payload === "string" ? payload : payload.text;
    if (!text?.trim()) return;
    if (typeof payload === "string") {
      wsRef.current.send(text.trim());
    } else {
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  const send = useCallback(() => {
    if (!input.trim()) return;
    sendWs(input.trim());
    setInput("");
    inputRef.current?.focus();
  }, [input, sendWs]);

  const transcribeAndSend = useCallback(async (blob, duration) => {
    try {
      const formData = new FormData();
      formData.append("file", blob, "recording.webm");
      const res = await fetch(`${API}/voice/transcribe`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.transcript?.trim()) {
        setInput(data.transcript.trim());
        sendWs({
          text: data.transcript.trim(),
          source: "voice",
          audio_duration: data.audio_duration || duration,
          language: data.language || "en"
        });
        setInput("");
      } else {
        setMicError("Couldn't understand. Please try again.");
      }
    } catch (err) {
      console.error(err);
      setMicError("Transcription failed.");
    }
  }, [sendWs]);

  const startRecording = async () => {
    setMicError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await transcribeAndSend(blob, recordTimeRef.current);
      };
      mr.start();
      mediaRecRef.current = mr;
      setRecording(true);
      setRecordTime(0);
      recordTimeRef.current = 0;
      timerRef.current = setInterval(() => {
        recordTimeRef.current += 1;
        setRecordTime(recordTimeRef.current);
      }, 1000);
      const animate = () => {
        setWaveBars(Array.from({ length: 12 }, () => 4 + Math.random() * 20));
        waveAnimRef.current = requestAnimationFrame(animate);
      };
      animate();
    } catch (err) {
      setMicError("Microphone access denied.");
    }
  };

  const stopRecording = () => {
    if (mediaRecRef.current?.state !== "inactive") mediaRecRef.current?.stop();
    setRecording(false);
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    if (waveAnimRef.current) { cancelAnimationFrame(waveAnimRef.current); waveAnimRef.current = null; }
  };

  const fmtTime = (s) => `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  const stats = {
    total:     msgs.length,
    escalated: msgs.filter(m => m.action === "ESCALATE").length,
    upsells:   msgs.filter(m => m.action === "UPSELL").length,
  };

  const statusColor = status === "live" ? "#30A46C" : status === "connecting" ? "#F5A623" : "#E5484D";

  const getIntensity = (emotion) => {
    switch (emotion) {
      case "angry":
      case "frustrated": return 9; // High intensity, red
      case "curious": return 5; // Yellow
      case "happy":
      case "grateful": return 2; // Green
      case "neutral": return 0; // Green (baseline)
      case "uninterested": return -8; // Blue (detached)
      default: return 0;
    }
  };

  const intensityScore = getIntensity(lastEmotion);



  if (activeView === "landing") {
    return (
      <div style={{ height: "100vh", overflow: "auto", background: "#0a0a0f" }}>
        <LandingPage onStart={() => setActiveView("chat")} />
      </div>
    );
  }

  return (
    <div className="app-shell">

      {/* ══════════════ SIDEBAR ══════════════ */}
      <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>

        {/* Brand */}
        <div className="sidebar-brand" style={{ display: 'flex', alignItems: 'center' }}>
          <img 
            src="/brand-eye-icon.png" 
            alt="Sentiment AI Eye" 
            className="sidebar-brand-icon w-5 h-5 object-contain inline-block mr-2 invert-[48%] sepia-[79%] saturate-[2476%] hue-rotate-[86deg] brightness-[118%] contrast-[119%]" 
            style={{ width: '20px', height: '20px', display: 'inline-block', marginRight: '8px', verticalAlign: 'middle', filter: 'invert(48%) sepia(79%) saturate(2476%) hue-rotate(86deg) brightness(118%) contrast(119%)' }}
          />
          <span className="sidebar-brand-text">{T.brand}</span>
        </div>

        {/* New Chat */}
        <button className="sidebar-new-btn" onClick={() => { setActiveView("chat"); setMsgs([]); setGraph([]); idxRef.current = 0; }}>
          <Plus size={15} />
          <span>{T.sidebar.newChat}</span>
        </button>

        {/* Nav Items */}
        <div className="sidebar-nav mt-4 flex flex-col gap-1 px-3">
          <button className={`sidebar-nav-btn ${activeView === "dashboard" ? "active" : ""}`} onClick={() => setActiveView("dashboard")}>
            <LayoutDashboard size={15} />
            <span>{T.sidebar.dashboard || "Dashboard"}</span>
          </button>
          <button className={`sidebar-nav-btn ${activeView === 'email' ? 'active' : ''}`} onClick={() => setActiveView('email')}>
            <Mail size={15} />
            <span>{T.sidebar.email || "Email"}</span>
          </button>
          <button className={`sidebar-nav-btn ${activeView === 'crm' ? 'active' : ''}`} onClick={() => setActiveView('crm')}>
            <Users size={15} />
            <span>CRM</span>
          </button>
          <button className={`sidebar-nav-btn ${activeView === 'agentConsole' ? 'active' : ''}`} onClick={() => setActiveView('agentConsole')}>
            <Headset size={15} />
            <span>Agent Console</span>
          </button>
          <button className={`sidebar-nav-btn ${activeView === "tickets" ? "active" : ""}`} onClick={() => setActiveView("tickets")}>
            <Inbox size={15} />
            <span>{T.sidebar.tickets || "Tickets"}</span>
          </button>
          <button className={`sidebar-nav-btn ${activeView === "analytics" ? "active" : ""}`} onClick={() => setActiveView("analytics")}>
            <BarChart3 size={15} />
            <span>{T.sidebar.analytics || "Analytics"}</span>
          </button>
          <button className={`sidebar-nav-btn ${activeView === "predictions" ? "active" : ""}`} onClick={() => setActiveView("predictions")}>
            <Sparkles size={15} />
            <span>{T.sidebar.predictions || "Predictions"}</span>
          </button>
          <button className={`sidebar-nav-btn ${activeView === "excel" ? "active" : ""}`} onClick={() => setActiveView("excel")}>
            <FileSpreadsheet size={15} />
            <span>{T.sidebar.excel || "Excel"}</span>
          </button>
          <button className={`sidebar-nav-btn ${activeView === "knowledge" ? "active" : ""}`} onClick={() => setActiveView("knowledge")}>
            <Database size={15} />
            <span>{T.sidebar.knowledge || "Knowledge Base"}</span>
          </button>
        </div>

        {/* Recent list */}
        <div className="sidebar-section-label">{T.sidebar.recent}</div>
        <div className="sidebar-list">
          {msgs.length > 0 ? (
            [...msgs].reverse().slice(0, 12).map((m, i) => (
              <div key={i} className="sidebar-item slide-in" style={{ animationDelay: `${i * 30}ms` }} onClick={() => setActiveView("chat")}>
                <MessageSquare size={13} className="sidebar-item-icon" />
                <span className="sidebar-item-text">
                  {m.message?.slice(0, 32)}{m.message?.length > 32 ? "…" : ""}
                </span>
              </div>
            ))
          ) : (
            <div className="sidebar-empty">{T.empty}</div>
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
        <header className="topbar">
          <div className="topbar-left">
            <ChameleonAvatar />
            <div className="topbar-status">
              <div className="status-dot" style={{ background: statusColor }} />
              <span style={{ color: statusColor }}>
                {status === "live" ? T.live : status === "connecting" ? T.connecting : T.disconnected}
              </span>
            </div>
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
          ) : activeView === "crm" ? (
            <CrmView />
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
              {/* ── LEFT PANE: Chat Workspace ── */}
              <div className="chat-pane">
                
            <div className="content-scroll">

              {/* Escalation Alert */}
              {alert && (
                <div className="alert-overlay">
                  <div className="alert-card alert-enter">
                    <div className="alert-header">
                      <AlertTriangle size={20} color="#E5484D" />
                      <div>
                        <div className="alert-title">{T.alertTitle}</div>
                        <div className="alert-sub">{T.alertSub}</div>
                      </div>
                      <button className="alert-close" onClick={() => setAlert(null)}>
                        <X size={16} />
                      </button>
                    </div>
                    <div className="alert-body">
                      <div className="alert-message">"{alert.message}"</div>
                      <div className="alert-meta">
                        <span className="alert-meta-tag">
                          {alert.emotion?.toUpperCase()}
                        </span>
                        <span className="alert-meta-tag alert-meta-score" style={{ color: scoreColor(alert.score) }}>
                          {alert.score?.toFixed(2)}
                        </span>
                      </div>
                      {alert.reply && (
                        <div className="alert-reply">{alert.reply}</div>
                      )}
                    </div>
                    <button className="alert-ack-btn" onClick={() => setAlert(null)}>
                      {T.acknowledge}
                    </button>
                  </div>
                </div>
              )}

              {/* Empty state greeting */}
              {msgs.length === 0 && (
                <div className="greeting-container fade-in flex flex-col items-center justify-center text-center">
                  <img 
                    src="/welcome-brand.png" 
                    alt="Sentiment AI Logo" 
                    className="w-full max-w-[320px] h-auto mx-auto mb-6 block object-contain" 
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                  <h1 className="greeting-title mt-6 mb-2">{T.greeting}</h1>
                  {smartGreeting && (
                    <p className="smart-greeting-text">{smartGreeting}</p>
                  )}
                  <p className="greeting-sub text-sm text-gray-400 max-w-md mx-auto">{T.greetingSub}</p>
                </div>
              )}

              {/* Messages list */}
              {msgs.length > 0 && (
                <div className="messages-area">
                  <div className="messages-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className="section-label">{T.messages}</span>
                      <span className="section-count">{msgs.length}</span>
                    </div>
                    <select 
                      className="channel-filter-select"
                      value={channelFilter}
                      onChange={(e) => setChannelFilter(e.target.value)}
                      style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '4px', fontSize: '13px' }}
                    >
                      <option value="All Channels">All Channels</option>
                      <option value="dashboard">Live Chat</option>
                      <option value="voice">Voice</option>
                      <option value="caspian-email">Email (Caspian)</option>
                      <option value="caspian-telegram">Telegram (Caspian)</option>
                    </select>
                  </div>
                  <div className="messages-list">
                    {msgs.filter(m => channelFilter === "All Channels" || m.channel === channelFilter || (channelFilter === 'voice' && m.source === 'voice')).map((m, i) => {
                      const meta = ACTION_META[m.action] || ACTION_META.NORMAL;
                      const cardClass = `card-${m.action.toLowerCase()}`;
                      
                      // Determine Channel Icon
                      const channelSrc = m.channel || (m.source === 'voice' ? 'voice' : 'dashboard');
                      let ChannelIcon = MessageSquare;
                      let channelName = "Live Chat";
                      if (channelSrc === 'voice') { ChannelIcon = Mic; channelName = "Voice"; }
                      else if (channelSrc === 'caspian-email') { ChannelIcon = Mail; channelName = "Email"; }
                      else if (channelSrc === 'caspian-telegram') { ChannelIcon = Send; channelName = "Telegram"; }
                      
                      return (
                        <div key={i} className={`message-row fade-in ${cardClass}`} style={{ animationDelay: `${Math.min(i * 20, 200)}ms` }}>
                          {/* User message */}
                          <div className="msg-user">
                            <div className="msg-user-avatar">
                              {m.message?.charAt(0)?.toUpperCase() || "?"}
                            </div>
                            <div className="msg-user-body">
                              <div className="msg-user-text">{m.message}</div>
                              <div className="msg-user-tags">
                                <span className="msg-tag msg-tag-channel" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: '#333', color: '#fff' }}>
                                  <ChannelIcon size={12} /> {channelName}
                                </span>
                                {m.language && m.language !== "en" && (
                                  <span className="msg-tag" style={{ color: "white", background: LANGUAGE_META[m.language]?.color || "gray" }}>
                                    🇮🇳 {LANGUAGE_META[m.language]?.name || m.language}
                                  </span>
                                )}
                                <span className="msg-tag" style={{ color: scoreColor(m.score), background: scoreBg(m.score) }}>
                                  {m.score?.toFixed(2)}
                                </span>
                                <span className="msg-tag" style={{ color: meta.color, background: meta.bg }}>
                                  {T.actions[m.action]}
                                </span>
                                <span className="msg-tag msg-tag-emotion">
                                  {emotionEmoji[m.emotion] || "😐"} {T.emotions[m.emotion] || m.emotion}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Bot reply */}
                          {m.reply && (
                            <div className="msg-bot">
                              <div className="msg-bot-avatar">
                                <CircleDot size={16} strokeWidth={2} />
                              </div>
                              <div className="msg-bot-body">
                                <div className="msg-bot-label-row">
                                  <span className="msg-bot-label">{T.botReply}</span>
                                  {m.memory_used > 0 && (
                                    <span className="memory-badge" title={`${T.memoryUsed} ${m.memory_used} ${T.pastInteractions}`}>
                                      <Brain size={12} />
                                    </span>
                                  )}
                                </div>
                                <div className="msg-bot-text">{m.reply}</div>
                              </div>
                            </div>
                          )}

                          {/* Score bar */}
                          <div className="msg-score-track">
                            <div className="msg-score-fill" style={{ width: `${(m.score || 0) * 100}%`, background: scoreColor(m.score) }} />
                          </div>
                        </div>
                      );
                    })}
                    <div ref={chatEnd} />
                  </div>
                </div>
              )}
            </div>

            {/* ── Unified Voice + Chat Input ── */}
            <div className="prompt-wrapper">
              {micError && (
                <div className="mic-error-banner">
                  {micError}
                  <button onClick={() => setMicError(null)}><X size={12} /></button>
                </div>
              )}
              <div className="prompt-box">
                <div className="prompt-input-row unified-input-row">
                  {recording ? (
                    <div className="recording-indicator">
                      <span className="rec-dot" />
                      <span className="rec-time">{fmtTime(recordTime)}</span>
                      <div className="waveform-bars">
                        {waveBars.map((h, i) => (
                          <span key={i} className="wave-bar" style={{ height: `${h}px` }} />
                        ))}
                      </div>
                    </div>
                  ) : (
                    <>
                      <button className="prompt-icon-btn" type="button">
                        <img 
                          src="/chat-eye-icon.png" 
                          alt="Eye Icon" 
                          style={{ width: '20px', height: '20px', filter: 'invert(54%) sepia(68%) saturate(2244%) hue-rotate(125deg) brightness(98%) contrast(101%)' }}
                        />
                      </button>
                      <input
                        ref={inputRef}
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
                        placeholder={T.placeholder}
                        className="prompt-input"
                        id="main-input"
                      />
                    </>
                  )}
                  <div className="prompt-actions">
                    <button
                      className={`voice-toggle-btn compact ${voiceOn ? "active" : ""}`}
                      onClick={() => setVoiceOn(!voiceOn)}
                      title={`${T.voiceReply} ${voiceOn ? "ON" : "OFF"}`}
                      type="button"
                    >
                      {voiceOn ? <Volume2 size={15} /> : <VolumeX size={15} />}
                    </button>
                    <button
                      className={`mic-btn ${recording ? "recording" : ""}`}
                      onClick={recording ? stopRecording : startRecording}
                      type="button"
                      title="Record voice"
                    >
                      {recording ? <MicOff size={16} /> : <Mic size={16} />}
                    </button>
                    <button className="send-btn" onClick={send} disabled={!input.trim() || recording} id="send-button">
                      <ArrowUp size={16} strokeWidth={2.5} />
                    </button>
                  </div>
                </div>
                {speaking && (
                  <div className="speaking-indicator inline-speaking">
                    <div className="speaking-bars"><span /><span /><span /><span /><span /></div>
                    <span>Speaking…</span>
                  </div>
                )}
              </div>
            </div>
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
                          {customerProfile.common_issues.map((issue, i) => (
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
