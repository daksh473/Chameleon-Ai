import { useState, useEffect } from "react";
import { Mail, Settings, CheckCircle2, AlertTriangle, Play, RefreshCw, Send, Plus } from "lucide-react";

const API = "http://localhost:8000";

const ACTION_META = {
  ESCALATE: { color: "#E5484D", bg: "rgba(229,72,77,0.08)", label: "ESCALATE" },
  NORMAL:   { color: "#A0A0A0", bg: "rgba(160,160,160,0.06)", label: "NORMAL" },
  UPSELL:   { color: "#30A46C", bg: "rgba(48,164,108,0.08)", label: "UPSELL" },
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

export default function EmailView() {
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [customReply, setCustomReply] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [checking, setChecking] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [composeOpen, setComposeOpen] = useState(false);
  const [composeData, setComposeData] = useState({ to: "", subject: "", body: "" });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [emRes, stRes] = await Promise.all([
        fetch(`${API}/email/inbox`).then(r => r.ok ? r.json() : []),
        fetch(`${API}/email/stats`).then(r => r.ok ? r.json() : null)
      ]);
      setEmails(emRes || []);
      setStats(stRes);
      if (emRes && emRes.length > 0 && !selectedEmail) setSelectedEmail(emRes[0]);
    } catch (e) {
      console.error(e);
      setError("Failed to load Email data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    const draft = sessionStorage.getItem("emailComposeDraft");
    if (draft) {
      try {
        setComposeData(JSON.parse(draft));
        setComposeOpen(true);
      } catch (e) { /* ignore */ }
      sessionStorage.removeItem("emailComposeDraft");
    }
  }, []);

  useEffect(() => {
    if (selectedEmail) {
      setCustomReply(selectedEmail.reply_sent || "");
    }
  }, [selectedEmail]);

  const handleCheckInbox = async () => {
    setChecking(true);
    try {
      const email = localStorage.getItem("emailUser") || "";
      const password = localStorage.getItem("emailPass") || "";
      const imap_host = localStorage.getItem("emailHost") || "imap.gmail.com";
      
      const payload = {
        email,
        password,
        imap_host,
        imap_port: 993
      };

      await fetch(`${API}/email/check-inbox`, { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      await fetchData();
    } catch (e) {
      console.error(e);
    } finally {
      setChecking(false);
    }
  };

  const handleSendReply = async () => {
    if (!selectedEmail) return;
    try {
      const res = await fetch(`${API}/email/send-reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email_id: selectedEmail.id, custom_reply: customReply })
      });
      const data = await res.json();
      if (data.success || data.mock_success) {
        await fetchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAutoProcess = async () => {
    setProcessing(true);
    setProgress(0);
    try {
      // Fake progress animation for UX
      const interval = setInterval(() => {
        setProgress(p => Math.min(p + 15, 90));
      }, 500);
      
      const res = await fetch(`${API}/email/auto-process`, { method: "POST" });
      const data = await res.json();
      
      clearInterval(interval);
      setProgress(100);
      
      setTimeout(async () => {
        setProcessing(false);
        setProgress(0);
        await fetchData();
        alert(`Processed: ${data.processed}\nReplied: ${data.replied}\nTickets Created: ${data.tickets_created}`);
      }, 500);
    } catch (e) {
      console.error(e);
      setProcessing(false);
    }
  };

  if (loading) return <div className="email-loading p-8 text-gray-400">Loading Emails...</div>;
  if (error) return <div className="p-8 text-red-400">Error: {error}</div>;

  return (
    <div className="email-view">
      {/* ── TOP BAR ── */}
      <div className="email-topbar">
        <div className="email-top-actions">
          <button className="btn-primary" onClick={handleCheckInbox} disabled={checking || processing}>
            <RefreshCw size={16} className={checking ? "spin" : ""} /> Check Inbox
          </button>
          <button className="btn-secondary" onClick={handleAutoProcess} disabled={checking || processing || stats?.pending === 0}>
            <Play size={16} /> Auto-Process All
          </button>
          <button className="btn-outline" onClick={() => setComposeOpen(true)}>
            <Plus size={16} /> Compose
          </button>
        </div>
        
        {stats && (
          <div className="email-stats-bar">
            <div className="stat-item"><span className="stat-val">{stats.total_received}</span><span className="stat-lbl">Total</span></div>
            <div className="stat-item"><span className="stat-val text-yellow-500">{stats.pending}</span><span className="stat-lbl">Pending</span></div>
            <div className="stat-item"><span className="stat-val text-emerald-500">{stats.replied}</span><span className="stat-lbl">Replied</span></div>
            <div className="stat-item"><span className="stat-val text-red-500">{stats.escalated}</span><span className="stat-lbl">Escalated</span></div>
          </div>
        )}
      </div>

      {processing && (
        <div className="email-progress-bar">
          <div className="email-progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
      )}

      <div className="email-content">
        {/* ── LEFT PANEL: LIST ── */}
        <div className="email-list-panel">
          {emails.length === 0 ? (
            <div className="email-empty">No emails found. Click 'Check Inbox'.</div>
          ) : (
            emails.map(em => {
              const meta = ACTION_META[em.action] || ACTION_META.NORMAL;
              return (
                <div 
                  key={em.id} 
                  className={`email-card ${selectedEmail?.id === em.id ? "selected" : ""}`}
                  onClick={() => setSelectedEmail(em)}
                >
                  <div className="email-card-header">
                    <span className="email-sender">{em.sender.split("<")[0].trim()}</span>
                    <span className="email-time">{new Date(em.received_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                  </div>
                  <div className="email-subject">{em.subject}</div>
                  <div className="email-preview">{em.body.slice(0, 100)}...</div>
                  
                  <div className="email-card-footer">
                    <div className="email-badges">
                      <span className="badge" style={{ color: scoreColor(em.sentiment_score) }}>
                        {em.sentiment_score.toFixed(2)}
                      </span>
                      <span className="badge">{emotionEmoji[em.emotion]} {em.emotion}</span>
                      <span className="badge" style={{ color: meta.color, background: meta.bg }}>{meta.label}</span>
                    </div>
                    {em.status === "replied" ? (
                      <span className="email-status-badge replied"><CheckCircle2 size={12}/> Replied</span>
                    ) : (
                      <span className="email-status-badge pending">Pending</span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* ── RIGHT PANEL: DETAIL ── */}
        <div className="email-detail-panel">
          {selectedEmail ? (
            <div className="email-detail-inner animate-in fade-in">
              <div className="detail-header">
                <h2>{selectedEmail.subject}</h2>
                <div className="detail-meta">
                  <span className="detail-sender">From: {selectedEmail.sender}</span>
                  <span className="detail-time">{new Date(selectedEmail.received_at).toLocaleString()}</span>
                </div>
              </div>
              
              <div className="detail-body-container">
                <div className="detail-body">{selectedEmail.body}</div>
              </div>
              
              <div className="detail-analysis">
                <h4>AI Analysis</h4>
                <div className="analysis-grid">
                  <div><strong>Sentiment:</strong> <span style={{color: scoreColor(selectedEmail.sentiment_score)}}>{selectedEmail.sentiment_score.toFixed(2)}</span></div>
                  <div><strong>Emotion:</strong> {emotionEmoji[selectedEmail.emotion]} {selectedEmail.emotion}</div>
                  <div>
                    <strong>Action:</strong> 
                    <span style={{ color: ACTION_META[selectedEmail.action]?.color }}> {selectedEmail.action}</span>
                  </div>
                  {selectedEmail.ticket_id && (
                    <div><strong>Ticket:</strong> <span className="ticket-link">#{selectedEmail.ticket_id}</span></div>
                  )}
                </div>
              </div>

              <div className="detail-reply-section">
                <h4>{selectedEmail.status === "replied" ? "Sent Reply" : "Draft Reply"}</h4>
                <textarea 
                  className="reply-textarea"
                  value={customReply}
                  onChange={e => setCustomReply(e.target.value)}
                  placeholder="AI is generating a reply..."
                  disabled={selectedEmail.status === "replied"}
                />
                
                {selectedEmail.status === "pending" && (
                  <div className="reply-actions">
                    <button className="btn-primary" onClick={handleSendReply}>
                      <Send size={14} /> Send Reply
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="email-empty">Select an email to view details</div>
          )}
        </div>
      </div>

      {/* Compose Modal */}
      {composeOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>New Email</h3>
            <input placeholder="To:" value={composeData.to} onChange={e => setComposeData({...composeData, to: e.target.value})} />
            <input placeholder="Subject:" value={composeData.subject} onChange={e => setComposeData({...composeData, subject: e.target.value})} />
            <textarea placeholder="Body..." rows={8} value={composeData.body} onChange={e => setComposeData({...composeData, body: e.target.value})} />
            <div className="modal-actions">
              <button className="btn-outline" onClick={() => setComposeOpen(false)}>Cancel</button>
              <button className="btn-primary" onClick={() => setComposeOpen(false)}><Send size={14} /> Send</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
