import { useState, useEffect, useRef, useCallback } from "react";
import { Send, X, CircleDot, AlertTriangle, CheckCircle2, TrendingUp, TrendingDown, Database, Sparkles, Mic, MicOff, Volume2, VolumeX } from "lucide-react";

const API = "http://localhost:8000";

const ACTION_META = {
  ESCALATE: { color: "#E5484D", bg: "rgba(229,72,77,0.08)" },
  NORMAL:   { color: "#A0A0A0", bg: "rgba(160,160,160,0.06)" },
  UPSELL:   { color: "#30A46C", bg: "rgba(48,164,108,0.08)" },
};

const emotionEmoji = {
  angry: "😠", frustrated: "😤", neutral: "😐",
  happy: "😊", grateful: "🙏", curious: "🤔", uninterested: "😑"
};

function scoreColor(s) {
  if (s < 0.3) return "#E5484D";
  if (s > 0.7) return "#30A46C";
  return "#F5A623";
}

/* ── TTS helper ── */
function speakText(text, lang = "en") {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = lang === "hi" ? "hi-IN" : "en-US";
  utter.rate = 0.95;
  utter.pitch = 1;
  // Pick best voice
  const voices = window.speechSynthesis.getVoices();
  const langPrefix = lang === "hi" ? "hi" : "en";
  const match = voices.find(v => v.lang.startsWith(langPrefix));
  if (match) utter.voice = match;
  window.speechSynthesis.speak(utter);
  return utter;
}

export default function LiveChatView() {
  const [sessionId, setSessionId] = useState(null);
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [voiceOn, setVoiceOn] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordTime, setRecordTime] = useState(0);
  const [speaking, setSpeaking] = useState(false);
  const [micError, setMicError] = useState(null);

  const chatEnd = useRef(null);
  const mediaRecRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  // Initialize Session
  useEffect(() => {
    fetch(`${API}/conversation/start`, { method: "POST" })
      .then(res => res.json())
      .then(data => setSessionId(data.session_id))
      .catch(err => console.error("Session start error:", err));
    // Preload voices
    window.speechSynthesis?.getVoices();
  }, []);

  // Auto-scroll
  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  // Cleanup timer
  useEffect(() => () => { if (timerRef.current) clearInterval(timerRef.current); }, []);

  const sendMessage = useCallback(async (text) => {
    const msgText = (text || input).trim();
    if (!msgText || !sessionId) return;
    if (!text) setInput("");

    const tempUserMsg = { role: "user", message: msgText, score: 0, emotion: "neutral", action: "NORMAL" };
    setMsgs(prev => [...prev, tempUserMsg]);

    try {
      const res = await fetch(`${API}/conversation/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: msgText })
      });
      const data = await res.json();

      setMsgs(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = {
          role: "user", message: msgText,
          score: data.score, emotion: data.emotion, action: data.action,
          ticket_created: data.ticket_created
        };
        newMsgs.push({
          role: "assistant", message: data.reply,
          score: data.score, emotion: data.emotion, action: data.action,
          ticket_created: data.ticket_created
        });
        return newMsgs;
      });

      // Voice reply
      if (voiceOn && data.reply) {
        setSpeaking(true);
        const utter = speakText(data.reply);
        if (utter) utter.onend = () => setSpeaking(false);
        else setSpeaking(false);
      }
    } catch (err) {
      console.error("Message send error:", err);
    }
  }, [input, sessionId, voiceOn]);

  /* ── Recording Controls ── */
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
        await transcribeAndSend(blob);
      };
      mr.start();
      mediaRecRef.current = mr;
      setRecording(true);
      setRecordTime(0);
      timerRef.current = setInterval(() => setRecordTime(t => t + 1), 1000);
    } catch (err) {
      console.error("Mic error:", err);
      setMicError("Microphone access denied. Please allow mic permission.");
    }
  };

  const stopRecording = () => {
    if (mediaRecRef.current && mediaRecRef.current.state !== "inactive") {
      mediaRecRef.current.stop();
    }
    setRecording(false);
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  };

  const transcribeAndSend = async (blob) => {
    try {
      const formData = new FormData();
      formData.append("file", blob, "recording.webm");
      const res = await fetch(`${API}/voice/transcribe`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.transcript && data.transcript.trim()) {
        await sendMessage(data.transcript.trim());
      } else {
        setMicError("Couldn't understand. Please try again.");
      }
    } catch (err) {
      console.error("Transcribe error:", err);
      setMicError("Transcription failed. Falling back to text.");
    }
  };

  const fmtTime = (s) => `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

  return (
    <div className="livechat-container">

      {/* Session sidebar */}
      <div className="livechat-sidebar">
        <h3 className="livechat-sidebar-title">Session History</h3>
        <div className="livechat-sidebar-id">ID: {sessionId?.slice(0, 8)}...</div>
        <div className="livechat-sidebar-list">
          {msgs.map((m, i) => (
            <div key={i} className={`livechat-sidebar-item ${m.role === "user" ? "user" : "bot"}`}>
              <span className="livechat-sidebar-role">{m.role === "user" ? "You" : "Bot"}:</span>
              {m.message.slice(0, 40)}{m.message.length > 40 ? "..." : ""}
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Panel */}
      <div className="livechat-main">

        {/* Voice Toggle Header */}
        <div className="livechat-voice-header">
          <button
            className={`voice-toggle-btn ${voiceOn ? "active" : ""}`}
            onClick={() => setVoiceOn(!voiceOn)}
          >
            {voiceOn ? <Volume2 size={14} /> : <VolumeX size={14} />}
            <span>Voice Reply {voiceOn ? "ON" : "OFF"}</span>
          </button>
          {speaking && (
            <div className="speaking-indicator">
              <div className="speaking-bars">
                <span /><span /><span /><span /><span />
              </div>
              <span className="speaking-label">Speaking...</span>
            </div>
          )}
        </div>

        {/* Messages Area */}
        <div className="livechat-messages">
          {msgs.length === 0 ? (
            <div className="livechat-empty">Send a message or use the 🎤 mic to start...</div>
          ) : (
            msgs.map((m, i) => {
              if (m.role === "user") {
                const meta = ACTION_META[m.action] || ACTION_META.NORMAL;
                return (
                  <div key={i} className="livechat-msg-row fade-in">
                    <div className="livechat-msg-user">
                      <div className="livechat-avatar user">U</div>
                      <div className="livechat-msg-body">
                        <div className="livechat-msg-text">{m.message}</div>
                        <div className="livechat-msg-tags">
                          <span className="livechat-tag" style={{ color: scoreColor(m.score) }}>
                            Score: {m.score?.toFixed(2)}
                          </span>
                          <span className="livechat-tag">
                            {emotionEmoji[m.emotion]} {m.emotion}
                          </span>
                          <span className="livechat-tag" style={{ color: meta.color, background: meta.bg }}>
                            {m.action}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              } else {
                return (
                  <div key={i} className="livechat-msg-row fade-in">
                    <div className="livechat-msg-bot flex-col">
                      <div className="flex items-start w-full">
                        <div className="livechat-avatar bot"><CircleDot size={14} /></div>
                        <div className="livechat-msg-text bot-text">{m.message}</div>
                      </div>
                      <div className="ml-10 mt-1 flex items-center text-[10px] uppercase font-bold tracking-wider">
                        {m.source === "knowledge_base" ? (
                          <span className="text-emerald-500 flex items-center gap-1 bg-emerald-500/10 px-2 py-1 rounded">
                            <Database size={10} /> From Knowledge Base
                          </span>
                        ) : (
                          <span className="text-indigo-400 flex items-center gap-1 bg-indigo-500/10 px-2 py-1 rounded">
                            <Sparkles size={10} /> AI Generated
                          </span>
                        )}
                      </div>
                    </div>
                    {m.action === "ESCALATE" && m.ticket_created && (
                      <div className="livechat-banner escalate">
                        <AlertTriangle size={14} /> Ticket Auto-Created for Escalation
                      </div>
                    )}
                    {m.action === "UPSELL" && (
                      <div className="livechat-banner upsell">
                        <CheckCircle2 size={14} /> Special Offer Sent
                      </div>
                    )}
                  </div>
                );
              }
            })
          )}
          <div ref={chatEnd} />
        </div>

        {/* Mic Error */}
        {micError && (
          <div className="livechat-mic-error">
            ⚠️ {micError}
            <button onClick={() => setMicError(null)}>✕</button>
          </div>
        )}

        {/* Prompt Input */}
        <div className="livechat-input-area">
          <div className="livechat-input-box">
            {/* Mic Button */}
            <button
              className={`mic-btn ${recording ? "recording" : ""}`}
              onClick={recording ? stopRecording : startRecording}
              title={recording ? "Stop recording" : "Start recording"}
            >
              {recording ? <MicOff size={16} /> : <Mic size={16} />}
              {recording && <span className="rec-dot" />}
            </button>

            {recording ? (
              <div className="rec-indicator">
                <span className="rec-pulse" />
                <span className="rec-time">{fmtTime(recordTime)}</span>
                <span className="rec-label">Recording... Click 🎤 to stop</span>
              </div>
            ) : (
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && sendMessage()}
                placeholder="Type your message..."
                className="livechat-input"
              />
            )}

            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || recording}
              className="livechat-send-btn"
            >
              <ArrowUp size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
