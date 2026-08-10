import { useState, useEffect } from "react";
import { Send, Settings, CheckCircle2, AlertTriangle, Play, RefreshCw, User } from "lucide-react";

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

function formatTimeAgo(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);
  
  if (diffInSeconds < 60) return "Just now";
  
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours}h ago`;
  
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays === 1) return "Yesterday";
  if (diffInDays < 7) return `${diffInDays}d ago`;
  
  return date.toLocaleDateString();
}

export default function TelegramView({ setActiveTab }) {
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingChat, setLoadingChat] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [usersRes, statsRes] = await Promise.all([
        fetch(`${API}/telegram/users`).then(r => r.ok ? r.json() : []),
        fetch(`${API}/telegram/stats`).then(r => r.ok ? r.json() : null)
      ]);
      setUsers(usersRes || []);
      setStats(statsRes);
    } catch (e) {
      console.error(e);
      setError("Failed to load Telegram data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedUser) {
      fetchConversation(selectedUser.sender_id);
    }
  }, [selectedUser]);

  const fetchConversation = async (sender_id) => {
    setLoadingChat(true);
    try {
      const res = await fetch(`${API}/telegram/users/${encodeURIComponent(sender_id)}/conversation`);
      if (res.ok) {
        const data = await res.json();
        setConversation(data);
      } else {
        setConversation([]);
      }
    } catch (e) {
      console.error(e);
      setConversation([]);
    } finally {
      setLoadingChat(false);
    }
  };
  
  const filteredUsers = users.filter(u => 
    (u.sender_name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
    (u.sender_id || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) return <div className="email-loading p-8 text-gray-400">Loading Telegram...</div>;
  if (error) return <div className="p-8 text-red-400">Error: {error}</div>;

  return (
    <div className="email-view">
      {/* ── TOP BAR ── */}
      <div className="email-topbar">
        <div className="email-top-actions">
          <button className="btn-primary" onClick={fetchData}>
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
        
        {stats && (
          <div className="email-stats-bar">
            <div className="stat-item"><span className="stat-val">{stats.total_unique_users}</span><span className="stat-lbl">Total Users</span></div>
            <div className="stat-item"><span className="stat-val">{stats.total_messages}</span><span className="stat-lbl">Total Messages</span></div>
            <div className="stat-item"><span className="stat-val text-emerald-500">{stats.messages_today}</span><span className="stat-lbl">Messages Today</span></div>
            <div className="stat-item"><span className="stat-val" style={{color: scoreColor(stats.avg_sentiment_across_all)}}>{stats.avg_sentiment_across_all.toFixed(2)}</span><span className="stat-lbl">Avg Sentiment</span></div>
            <div className="stat-item"><span className="stat-val text-red-500">{stats.escalated_count}</span><span className="stat-lbl">Escalated</span></div>
          </div>
        )}
      </div>

      <div className="email-content">
        {/* ── LEFT PANEL: USER LIST ── */}
        <div className="email-list-panel">
          <div className="p-3 border-b border-[rgba(255,255,255,0.1)]">
            <input 
              type="text" 
              placeholder="Search by name or ID..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[rgba(255,255,255,0.05)] border border-[rgba(255,255,255,0.1)] rounded-md px-3 py-2 text-sm text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>
          
          {filteredUsers.length === 0 ? (
            <div className="email-empty">
              {users.length === 0 
                ? "No Telegram conversations yet. Message @Chameleon_aibot on Telegram to test it live."
                : "No matching users found."
              }
            </div>
          ) : (
            filteredUsers.map(u => {
              const meta = ACTION_META[u.last_action] || ACTION_META.NORMAL;
              return (
                <div 
                  key={u.sender_id} 
                  className={`email-card ${selectedUser?.sender_id === u.sender_id ? "selected" : ""}`}
                  onClick={() => setSelectedUser(u)}
                >
                  <div className="email-card-header">
                    <span className="email-sender">{u.sender_name || u.sender_id}</span>
                    <span className="email-time">{formatTimeAgo(u.last_message_time)}</span>
                  </div>
                  <div className="email-subject text-xs text-gray-400 mb-1">{u.sender_id}</div>
                  <div className="email-preview">{u.last_message.slice(0, 100)}{u.last_message.length > 100 ? '...' : ''}</div>
                  
                  <div className="email-card-footer">
                    <div className="email-badges">
                      <span className="badge" style={{ color: scoreColor(u.avg_sentiment) }}>
                        {u.avg_sentiment.toFixed(2)} Avg
                      </span>
                      {u.last_action && (
                        <span className="badge" style={{ color: meta.color, background: meta.bg }}>{meta.label}</span>
                      )}
                    </div>
                    {u.open_tickets_count > 0 && (
                      <span className="email-status-badge pending"><AlertTriangle size={12}/> {u.open_tickets_count} Open Ticket(s)</span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* ── RIGHT PANEL: CONVERSATION DETAIL ── */}
        <div className="email-detail-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          {selectedUser ? (
            <div className="email-detail-inner animate-in fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
              
              {/* Header */}
              <div className="detail-header" style={{ flexShrink: 0, paddingBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Send size={20} className="text-[#3390ec]" /> 
                    {selectedUser.sender_name || selectedUser.sender_id}
                  </h2>
                  <div className="detail-meta">
                    <span className="detail-sender">ID: {selectedUser.sender_id}</span>
                    <span className="detail-time">Total Msgs: {selectedUser.total_messages}</span>
                  </div>
                </div>
                
                <button 
                  className="btn-outline" 
                  onClick={() => setActiveTab("crm")}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <User size={14} /> View in CRM
                </button>
              </div>
              
              {/* Tickets Chip */}
              {selectedUser.open_tickets_count > 0 && (
                <div style={{ padding: '12px 24px', background: 'rgba(229,72,77,0.05)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <span className="badge" style={{ color: "#E5484D", background: "rgba(229,72,77,0.1)", fontSize: '13px', padding: '4px 10px' }}>
                    <AlertTriangle size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} /> 
                    {selectedUser.open_tickets_count} Open Ticket{selectedUser.open_tickets_count > 1 ? 's' : ''} Linked
                  </span>
                </div>
              )}
              
              {/* Chat View */}
              <div className="chat-history-view" style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', background: 'var(--bg-card)' }}>
                {loadingChat ? (
                  <div className="text-gray-400 text-center">Loading conversation...</div>
                ) : (
                  conversation.map((msg, idx) => {
                    const isBot = msg.role === "assistant";
                    const meta = ACTION_META[msg.action] || ACTION_META.NORMAL;
                    
                    return (
                      <div key={idx} style={{
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: isBot ? 'flex-start' : 'flex-end',
                        maxWidth: '85%',
                        alignSelf: isBot ? 'flex-start' : 'flex-end'
                      }}>
                        <div style={{
                          padding: '12px 16px',
                          borderRadius: '16px',
                          borderBottomRightRadius: !isBot ? '4px' : '16px',
                          borderBottomLeftRadius: isBot ? '4px' : '16px',
                          background: isBot ? 'rgba(255,255,255,0.05)' : '#3390ec',
                          color: '#fff',
                          border: msg.role === 'user' && msg.action === 'ESCALATE' ? '1px solid #E5484D' : 
                                  msg.role === 'user' && msg.action === 'UPSELL' ? '1px solid #30A46C' : 'none',
                          boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          lineHeight: '1.5',
                          fontSize: '14px'
                        }}>
                          {msg.message}
                        </div>
                        
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          marginTop: '6px',
                          fontSize: '11px',
                          color: 'var(--text-muted)'
                        }}>
                          {isBot ? 'Bot' : selectedUser.sender_name || 'Customer'}
                          <span>•</span>
                          {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                          
                          {msg.role === 'user' && msg.sentiment_score !== null && (
                            <>
                              <span>•</span>
                              <span style={{ color: scoreColor(msg.sentiment_score) }}>
                                {msg.sentiment_score.toFixed(2)}
                              </span>
                              <span>{emotionEmoji[msg.emotion]}</span>
                              <span style={{ color: meta.color, marginLeft: '4px' }}>{msg.action}</span>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
                
                {conversation.length === 0 && !loadingChat && (
                  <div className="text-gray-400 text-center mt-8">No messages found.</div>
                )}
              </div>

            </div>
          ) : (
            <div className="email-empty" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              Select a Telegram user to view their conversation
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
