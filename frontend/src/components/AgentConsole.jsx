import React, { useState, useEffect, useRef } from 'react';
import './AgentConsole.css';
import { 
  Users, List, MessageSquare, Clock, ShieldAlert,
  Send, CheckCircle, ArrowRightCircle, Search, Headset, Mic, Mail, Phone, PhoneCall
} from 'lucide-react';

const API = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/agents';

export default function AgentConsole() {
  const [activeTab, setActiveTab] = useState('queue');
  const [agents, setAgents] = useState([]);
  const [currentAgentId, setCurrentAgentId] = useState(null);
  
  // Data States
  const [queue, setQueue] = useState([]);
  const [myConvos, setMyConvos] = useState([]);
  const [activeConvo, setActiveConvo] = useState(null);
  const [history, setHistory] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [replyText, setReplyText] = useState('');
  const [callStatus, setCallStatus] = useState(null);
  const [phoneInput, setPhoneInput] = useState('');
  const [showPhonePrompt, setShowPhonePrompt] = useState(false);
  const ws = useRef(null);

  // Initialize data
  useEffect(() => {
    Promise.all([
      fetch(`${API}/handoff/agents`).then(r => r.ok ? r.json() : []),
      fetch(`${API}/handoff/queue`).then(r => r.ok ? r.json() : [])
    ]).then(([agentsData, queueData]) => {
      setAgents(agentsData || []);
      setQueue(queueData || []);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setError("Failed to load Agent Console data");
      setLoading(false);
    });
    
    // Connect WebSocket for live notifications
    ws.current = new WebSocket(WS_URL);
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'new_handoff') {
        // Play sound (mock)
        console.log("DING! New handoff.");
        fetchQueue();
      }
    };

    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  // Set default agent on load
  useEffect(() => {
    if (agents.length > 0 && !currentAgentId) {
      setCurrentAgentId(agents[0].id);
    }
  }, [agents]);

  // Fetch my active convos when agent changes
  useEffect(() => {
    if (currentAgentId) {
      fetchMyConvos();
    }
  }, [currentAgentId]);

  const fetchQueue = async () => {
    try {
      const res = await fetch(`${API}/handoff/queue`);
      if (res.ok) setQueue(await res.json());
    } catch(e) { console.error(e); }
  };

  const fetchMyConvos = async () => {
    try {
      const res = await fetch(`${API}/handoff/active`);
      if (res.ok) {
        const allActive = await res.json();
        setMyConvos((allActive || []).filter(h => h.agent_id === parseInt(currentAgentId)));
      }
    } catch(e) { console.error(e); }
  };

  const fetchHistory = async () => {};

  const handleAccept = async (handoffId) => {
    const res = await fetch(`${API}/handoff/accept/${handoffId}`, { method: 'POST' });
    if (res.ok) {
      fetchQueue();
      fetchMyConvos();
      setActiveTab('conversations');
    }
  };

  const handleResolve = async () => {
    if (!activeConvo) return;
    const res = await fetch(`${API}/handoff/resolve/${activeConvo.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolution_notes: 'Resolved via agent console', customer_rating: 5 })
    });
    if (res.ok) {
      setActiveConvo(null);
      fetchMyConvos();
    }
  };

  const [toast, setToast] = useState(null); // Added state for toast
  
  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 5000);
  };

  const handleSendMessage = async () => {
    if (!replyText.trim() || !activeConvo) return;
    const msg = replyText;
    setReplyText(''); 
    
    // Optimistically add to UI, we will remove if failed
    const tempHistory = [...(activeConvo.conversation_history || []), {sender_type: 'agent', text: msg, name: 'Agent'}];
    setActiveConvo({ ...activeConvo, conversation_history: tempHistory });
    
    try {
      const res = await fetch(`${API}/handoff/agent-message/${activeConvo.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
      });
      const data = await res.json();
      if (!res.ok || data.success === false) {
        throw new Error(data.error || 'Failed to send message');
      }
      fetchMyConvos();
    } catch (e) {
      showToast(`Message failed to send — customer did not receive it. Error: ${e.message}`);
      // Revert optimistic UI update
      const reverted = tempHistory.slice(0, -1);
      setActiveConvo({ ...activeConvo, conversation_history: reverted });
    }
  };

  const handleCallCustomer = async () => {
    if (!activeConvo) return;
    setCallStatus('Calling...');
    try {
      const res = await fetch(`${API}/handoff/call-customer/${activeConvo.id}`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        setCallStatus(`Connected: ${data.status}`);
        setTimeout(() => setCallStatus(null), 5000);
      } else {
        if (data.error === "no_phone_number") setShowPhonePrompt(true);
        setCallStatus(data.message || 'Call failed');
        setTimeout(() => setCallStatus(null), 3000);
      }
    } catch (e) {
      setCallStatus('Error calling');
      setTimeout(() => setCallStatus(null), 3000);
    }
  };

  const handleAddPhone = async () => {
    if (!activeConvo || !phoneInput) return;
    const res = await fetch(`${API}/handoff/add-phone/${activeConvo.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: phoneInput })
    });
    if (res.ok) {
      setShowPhonePrompt(false);
      // Update local state so call button activates
      setActiveConvo({ ...activeConvo, customer_phone: phoneInput });
    }
  };

  // UI Components
  const LiveQueue = () => (
    <div>
      {toast && (
        <div style={{ position: 'fixed', top: '20px', right: '20px', background: '#ef4444', color: 'white', padding: '12px 24px', borderRadius: '8px', zIndex: 9999, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
          {toast}
        </div>
      )}
      <div className="queue-stats">
        <div className="stat-card">
          <span>Pending Handoffs</span>
          <h3 style={{ color: queue.length > 3 ? '#ef4444' : 'white' }}>{queue.length}</h3>
        </div>
        <div className="stat-card">
          <span>Active Agents</span>
          <h3>{agents.filter(a => a.status === 'online').length}</h3>
        </div>
        <div className="stat-card">
          <span>Avg Wait Time</span>
          <h3>1m 24s</h3>
        </div>
      </div>
      
      <div className="queue-grid">
        {queue.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>Queue is empty. Great job!</div>
        ) : queue.map(item => {
          
          let ChannelIcon = MessageSquare;
          let channelLabel = "Live Chat";
          if (item.channel === "voice") { ChannelIcon = Mic; channelLabel = "Voice"; }
          else if (item.channel === "email" || item.channel === "caspian-email") { ChannelIcon = Mail; channelLabel = "Email"; }
          else if (item.channel === "caspian-telegram" || item.channel === "telegram") { ChannelIcon = Send; channelLabel = "Telegram"; }

          return (
          <div className="handoff-card" key={item.id}>
            <div className="handoff-info">
              <div className="handoff-header" style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                <span className={`priority-badge priority-${item.priority}`}>{item.priority}</span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px', fontSize: '11px', color: '#e2e8f0' }}>
                  <ChannelIcon size={12} /> {channelLabel}
                </span>
                <span className="handoff-customer" style={{ fontWeight: 'bold' }}>{item.sender_name || item.customer_name || item.sender_id || item.session_id}</span>
              </div>
              <div className="handoff-preview">{item.reason}</div>
              <div className="handoff-meta">
                <span>Sentiment: {item.sentiment_score?.toFixed(2) || 'N/A'} {item.emotion ? `(${item.emotion})` : ''}</span>
                <span>Wait: Just now</span>
              </div>
            </div>
            <div className="handoff-actions">
              <button className="btn-accept" onClick={() => handleAccept(item.id)}>Accept</button>
            </div>
          </div>
        )})}
      </div>
    </div>
  );

  const MyConversations = () => (
    <div className="split-view">
      {toast && (
        <div style={{ position: 'fixed', top: '20px', right: '20px', background: '#ef4444', color: 'white', padding: '12px 24px', borderRadius: '8px', zIndex: 9999, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
          {toast}
        </div>
      )}
      <div className="convo-list">
        {myConvos.length === 0 ? (
          <div style={{ padding: '20px', color: '#94a3b8' }}>No active conversations.</div>
        ) : myConvos.map(c => (
          <div 
            key={c.id} 
            className={`convo-item ${activeConvo?.id === c.id ? 'active' : ''}`}
            onClick={() => setActiveConvo(c)}
          >
            <div className="convo-item-header">
              <span>{c.customer_name || c.session_id}</span>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>{new Date(c.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
            </div>
            <div className="convo-item-preview">
              {c.reason}
            </div>
          </div>
        ))}
      </div>
      
      <div className="convo-workspace">
        {activeConvo ? (
          <>
            <div className="workspace-header">
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <h3 style={{ margin: 0 }}>{activeConvo.customer_name || activeConvo.session_id}</h3>
                {activeConvo.conversation_history && activeConvo.conversation_history.length > 0 && (
                  <span style={{ fontSize: '12px', color: '#ff9800', marginTop: '4px', fontWeight: 'bold' }}>
                    Customer speaks: {(() => {
                      const userMsgs = activeConvo.conversation_history.filter(m => m.role === 'user');
                      const lastLang = userMsgs.length > 0 ? userMsgs[userMsgs.length - 1].language : null;
                      return lastLang && lastLang !== 'en' ? `🇮🇳 ${lastLang.toUpperCase()}` : 'EN';
                    })()}
                  </span>
                )}
              </div>
              <div className="workspace-actions">
                {callStatus && <span style={{ color: '#10b981', fontSize: '12px', marginRight: '8px' }}>{callStatus}</span>}
                
                {activeConvo.customer_phone ? (
                  <button className="btn-call" onClick={handleCallCustomer} title="Call Customer" style={{ background: '#059669', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', marginRight: '8px' }}>
                    <PhoneCall size={16} /> Call
                  </button>
                ) : (
                  <div style={{ display: 'inline-flex', alignItems: 'center', marginRight: '8px' }}>
                    <button className="btn-call disabled" disabled title="No phone on file" style={{ background: '#334155', color: '#94a3b8', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'not-allowed', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <Phone size={16} /> Call
                    </button>
                    {!showPhonePrompt ? (
                      <span onClick={() => setShowPhonePrompt(true)} style={{ color: '#3b82f6', fontSize: '11px', marginLeft: '4px', cursor: 'pointer' }}>+ Add Phone</span>
                    ) : (
                      <div style={{ display: 'inline-flex', marginLeft: '4px' }}>
                        <input type="text" placeholder="+1234567890" value={phoneInput} onChange={e => setPhoneInput(e.target.value)} style={{ padding: '2px 4px', fontSize: '11px', width: '90px' }} />
                        <button onClick={handleAddPhone} style={{ fontSize: '11px', padding: '2px 4px' }}>Save</button>
                      </div>
                    )}
                  </div>
                )}
                
                <button className="btn-transfer" title="Transfer"><ArrowRightCircle size={16} /> Transfer</button>
                <button className="btn-resolve" onClick={handleResolve}><CheckCircle size={16} /> Resolve</button>
              </div>
            </div>
            
            <div className="workspace-chat">
              {activeConvo.conversation_history.map((msg, idx) => {
                const isUser = msg.role === 'user' || msg.sender_type === 'customer' || msg.sender_type === 'user';
                const isAgent = msg.role === 'agent' || msg.sender_type === 'agent';
                return (
                <div key={idx} className={`chat-bubble ${isUser ? 'bubble-user' : (isAgent ? 'bubble-human-agent' : 'bubble-agent')}`}
                  style={isAgent ? { background: '#2563eb', color: 'white', alignSelf: 'flex-end', borderBottomRightRadius: 0 } : (!isUser ? { background: '#1e293b', color: '#f8fafc', alignSelf: 'flex-start', borderBottomLeftRadius: 0 } : {})}
                >
                  {isAgent && <div style={{ fontSize: '10px', opacity: 0.8, marginBottom: '2px' }}>{msg.name || 'Agent'}</div>}
                  {!isUser && !isAgent && <div style={{ fontSize: '10px', opacity: 0.8, marginBottom: '2px' }}>Bot</div>}
                  {msg.text ?? msg.message ?? msg.content ?? ""}
                </div>
              )})}
            </div>
            
            <div className="workspace-input">
              <div className="quick-replies">
                <button className="quick-reply-btn" onClick={() => setReplyText('I understand your frustration, let me help.')}>I understand...</button>
                <button className="quick-reply-btn" onClick={() => setReplyText('Let me check on this for you right away.')}>Let me check...</button>
              </div>
              <div className="input-box">
                <input 
                  type="text" 
                  placeholder="Type your message..." 
                  value={replyText}
                  onChange={e => setReplyText(e.target.value)}
                  onKeyDown={e => {
                    if(e.key === 'Enter') {
                      handleSendMessage();
                    }
                  }}
                />
                <button onClick={handleSendMessage}><Send size={18} /></button>
              </div>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
            Select a conversation from the left to start helping.
          </div>
        )}
      </div>
    </div>
  );

  const AgentDirectory = () => (
    <div className="agent-grid">
      {agents.map(a => (
        <div className="agent-card" key={a.id}>
          <div className="agent-card-header">
            <div className="agent-avatar">{a.name.substring(0, 2).toUpperCase()}</div>
            <div className="agent-details">
              <h3>{a.name}</h3>
              <span className="agent-status">
                <span className={`status-dot status-${a.status}`}></span>
                {a.status.charAt(0).toUpperCase() + a.status.slice(1)} • {a.specialization}
              </span>
            </div>
          </div>
          <div style={{ fontSize: '13px', color: '#94a3b8' }}>
            Load: {a.current_conversations} / {a.max_conversations}
            <br/>Rating: {a.avg_rating?.toFixed(1) || '5.0'} ⭐
          </div>
        </div>
      ))}
    </div>
  );

  if (loading) return <div className="p-8 text-gray-400">Loading Agent Console...</div>;
  if (error) return <div className="p-8 text-red-400">{error}</div>;

  return (
    <div className="agent-console-container">
      <div className="agent-header">
        <h1><Headset /> Agent Console</h1>
        <div className="agent-identity">
          <span style={{ fontSize: '13px', color: '#94a3b8' }}>Logged in as:</span>
          <select 
            value={currentAgentId || ''} 
            onChange={(e) => setCurrentAgentId(e.target.value)}
          >
            {agents.map(a => (
              <option key={a.id} value={a.id}>{a.name} ({a.specialization})</option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="console-tabs">
        <button className={activeTab === 'queue' ? 'active' : ''} onClick={() => setActiveTab('queue')}>
          <List size={18} /> Live Queue {queue.length > 0 && <span className="badge">{queue.length}</span>}
        </button>
        <button className={activeTab === 'conversations' ? 'active' : ''} onClick={() => setActiveTab('conversations')}>
          <MessageSquare size={18} /> My Conversations {myConvos.length > 0 && <span className="badge">{myConvos.length}</span>}
        </button>
        <button className={activeTab === 'directory' ? 'active' : ''} onClick={() => setActiveTab('directory')}>
          <Users size={18} /> Agent Directory
        </button>
        <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}>
          <Clock size={18} /> Handoff History
        </button>
      </div>
      
      <div className="console-content">
        {activeTab === 'queue' && <LiveQueue />}
        {activeTab === 'conversations' && <MyConversations />}
        {activeTab === 'directory' && <AgentDirectory />}
        {activeTab === 'history' && (
          <div style={{ color: '#94a3b8' }}>History tracking would appear here showing all resolved handoffs.</div>
        )}
      </div>
    </div>
  );
}
