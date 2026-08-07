import React, { useRef, useEffect, useState } from 'react';
import {
  PanelLeft, ChevronLeft, ChevronRight, Monitor, RotateCw,
  Share, Plus, Copy, Grid, MessageSquare, Ticket, Users,
  BarChart3, Sparkles
} from 'lucide-react';
import Logo from './Logo';

/* ─────────────────────────────────────────────
   ScaledDashboard – renders at fixed 896px width
   and CSS-scales to fit its container
   ───────────────────────────────────────────── */
function ScaledDashboard({ children }) {
  const outerRef = useRef(null);
  const innerRef = useRef(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const outer = outerRef.current;
    if (!outer) return;

    const observer = new ResizeObserver(([entry]) => {
      const containerWidth = entry.contentRect.width;
      const newScale = Math.min(containerWidth / 896, 1);
      setScale(newScale);
    });

    observer.observe(outer);
    return () => observer.disconnect();
  }, []);

  const innerHeight = innerRef.current?.offsetHeight || 520;

  return (
    <div ref={outerRef} className="w-full overflow-hidden" style={{ height: innerHeight * scale }}>
      <div
        ref={innerRef}
        style={{
          width: 896,
          transform: `scale(${scale})`,
          transformOrigin: 'top left',
        }}
      >
        {children}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SVG Area Chart – sentiment wave
   ───────────────────────────────────────────── */
function SentimentChart() {
  const points = [0.55, 0.62, 0.48, 0.71, 0.35, 0.58, 0.73, 0.42, 0.68, 0.78, 0.52, 0.65, 0.45, 0.72, 0.60, 0.38, 0.67, 0.75, 0.50, 0.63];
  const w = 580, h = 120, pad = 8;
  const usableW = w - pad * 2;
  const usableH = h - pad * 2;

  const pts = points.map((v, i) => ({
    x: pad + (i / (points.length - 1)) * usableW,
    y: pad + (1 - v) * usableH,
  }));

  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ');
  const area = `${line} L${pts[pts.length - 1].x},${h} L${pts[0].x},${h} Z`;

  const escalateY = pad + (1 - 0.3) * usableH;
  const upsellY = pad + (1 - 0.7) * usableH;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full">
      <defs>
        <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#5b8bf7" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#5b8bf7" stopOpacity="0.02" />
        </linearGradient>
      </defs>
      {/* Reference lines */}
      <line x1={pad} y1={escalateY} x2={w - pad} y2={escalateY} stroke="#ff5f57" strokeWidth="0.5" strokeDasharray="4 4" opacity="0.4" />
      <line x1={pad} y1={upsellY} x2={w - pad} y2={upsellY} stroke="#28c840" strokeWidth="0.5" strokeDasharray="4 4" opacity="0.4" />
      <text x={w - pad - 2} y={escalateY - 4} textAnchor="end" fill="#ff5f57" fontSize="7" opacity="0.5">Escalate</text>
      <text x={w - pad - 2} y={upsellY - 4} textAnchor="end" fill="#28c840" fontSize="7" opacity="0.5">Upsell</text>
      {/* Area */}
      <path d={area} fill="url(#chartFill)" />
      {/* Line */}
      <path d={line} fill="none" stroke="#5b8bf7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      {/* Dots */}
      {pts.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="2.5" fill="#5b8bf7" opacity="0.7" />
      ))}
    </svg>
  );
}

/* ─────────────────────────────────────────────
   Message Row
   ───────────────────────────────────────────── */
const MESSAGES = [
  { text: "Your service is absolutely terrible! I want a refund NOW!", score: 0.12, emotion: "angry", action: "ESCALATE" },
  { text: "Can you tell me the status of order #4521?", score: 0.58, emotion: "neutral", action: "NORMAL" },
  { text: "Wow, the new features are amazing. Love the upgrade!", score: 0.91, emotion: "happy", action: "UPSELL" },
];

const ACTION_STYLES = {
  ESCALATE: { bg: "bg-red-500/10", text: "text-red-400", border: "border-l-red-500" },
  NORMAL: { bg: "bg-white/5", text: "text-gray-400", border: "border-l-gray-500" },
  UPSELL: { bg: "bg-green-500/10", text: "text-green-400", border: "border-l-green-500" },
};

/* ─────────────────────────────────────────────
   Sidebar conversations
   ───────────────────────────────────────────── */
const CONVERSATIONS = [
  { name: "Sarah M.", preview: "Need help with billing...", sentiment: "negative" },
  { name: "James K.", preview: "Thanks for the quick fix!", sentiment: "positive" },
  { name: "Priya R.", preview: "When will my order arrive?", sentiment: "neutral" },
  { name: "Alex T.", preview: "This is the worst...", sentiment: "negative" },
  { name: "Maria L.", preview: "Great experience overall", sentiment: "positive" },
];

/* ═══════════════════════════════════════════════
   MAIN DASHBOARD MOCKUP
   ═══════════════════════════════════════════════ */
export default function DashboardMockup() {
  return (
    <div className="animate-hero-rise [animation-delay:620ms] relative z-0 w-[92%] sm:w-[84%] lg:w-[72%] max-w-4xl mx-auto shrink-0 -mb-10 sm:-mb-20 lg:-mb-32">
      <ScaledDashboard>
        <div className="rounded-t-2xl overflow-hidden bg-[#1a1a1c] shadow-[0_-20px_80px_rgba(0,0,0,0.35)] ring-1 ring-white/10 text-left">

          {/* ── Title Bar ── */}
          <div className="bg-[#242427] border-b border-white/5 px-4 py-2.5">
            <div className="flex items-center gap-3">
              {/* Traffic lights */}
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#ff5f57' }} />
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#febc2e' }} />
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#28c840' }} />
              </div>

              {/* Left icons */}
              <div className="flex items-center gap-2 ml-2">
                <PanelLeft className="w-3.5 h-3.5 text-white/40" />
                <ChevronLeft className="w-3.5 h-3.5 text-white/25" />
                <ChevronRight className="w-3.5 h-3.5 text-white/25" />
              </div>

              {/* URL bar */}
              <div className="flex-1 flex justify-center">
                <div className="flex items-center gap-2 bg-[#1a1a1c] rounded-md px-6 py-1">
                  <Monitor className="w-3 h-3 text-white/40" />
                  <span className="text-[10px] text-white/60">sentimentai.live/dashboard</span>
                </div>
              </div>

              {/* Right icons */}
              <div className="flex items-center gap-2">
                <RotateCw className="w-3.5 h-3.5 text-white/40" />
                <Share className="w-3.5 h-3.5 text-white/40" />
                <Plus className="w-3.5 h-3.5 text-white/40" />
                <Copy className="w-3.5 h-3.5 text-white/40" />
              </div>
            </div>
          </div>

          {/* ── App Body ── */}
          <div className="flex" style={{ minHeight: 440 }}>

            {/* ── Sidebar (22%) ── */}
            <div className="border-r border-white/5 bg-[#1e1e21] px-3 py-3.5" style={{ width: '22%' }}>
              {/* Logo + grid */}
              <div className="flex items-center justify-between mb-4">
                <Logo className="w-4 h-4 text-white/70" />
                <Grid className="w-3.5 h-3.5 text-white/30" />
              </div>

              {/* Workspace badge */}
              <div className="flex items-center gap-2 mb-4">
                <div className="w-4 h-4 rounded bg-[#5b8bf7] flex items-center justify-center text-[8px] font-bold text-white">S</div>
                <span className="text-[10px] text-white/80 font-medium">SmartCare</span>
              </div>

              {/* Nav items */}
              <div className="space-y-0.5">
                {[
                  { icon: MessageSquare, label: 'Live Chat', active: true },
                  { icon: Ticket, label: 'Tickets' },
                  { icon: Users, label: 'CRM' },
                  { icon: BarChart3, label: 'Analytics' },
                ].map(({ icon: Icon, label, active }) => (
                  <div
                    key={label}
                    className={`flex items-center gap-2 px-2 py-1.5 rounded-md text-[10px] ${active ? 'bg-white/10 text-white/90' : 'text-white/50 hover:text-white/70'}`}
                  >
                    <Icon className="w-3 h-3" />
                    {label}
                  </div>
                ))}
              </div>

              {/* Recent conversations */}
              <div className="mt-5 pt-3 border-t border-white/5">
                <div className="text-[8px] tracking-widest text-white/30 uppercase mb-2">Recent</div>
                {CONVERSATIONS.map((c, i) => (
                  <div key={i} className="flex items-start gap-2 py-1.5">
                    <span
                      className={`w-1.5 h-1.5 rounded-full mt-1 shrink-0 ${c.sentiment === 'positive' ? 'bg-[#28c840]/70' : c.sentiment === 'negative' ? 'bg-[#ff5f57]/70' : 'bg-white/30'}`}
                    />
                    <div className="min-w-0">
                      <div className="text-[9px] text-white/70 font-medium truncate">{c.name}</div>
                      <div className="text-[8px] text-white/35 truncate">{c.preview}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Main Content (78%) ── */}
            <div className="flex-1 p-4 space-y-3 overflow-hidden">

              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-[#5b8bf7] flex items-center justify-center text-sm font-bold text-white">S</div>
                  <div>
                    <div className="text-sm font-medium text-white">SmartCare</div>
                    <div className="text-[10px] text-white/45">Real-time emotion intelligence</div>
                  </div>
                </div>
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#5b8bf7] text-[10px] text-white font-medium hover:bg-[#4a7af0] transition-colors">
                  <Sparkles className="w-3 h-3" />
                  Run Analysis
                </button>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-4 divide-x divide-white/5 rounded-xl bg-white/[0.03] ring-1 ring-white/5">
                {[
                  { label: 'TOTAL', value: '1,842', sub: 'Messages analyzed' },
                  { label: 'ESCALATED', value: '128', sub: 'Auto-flagged for agents' },
                  { label: 'UPSELLS', value: '94', sub: 'Offers triggered' },
                  { label: 'AVG SCORE', value: '0.68', sub: 'Sentiment index' },
                ].map((stat) => (
                  <div key={stat.label} className="px-4 py-3 text-center">
                    <div className="text-[8px] tracking-wider text-white/35 uppercase">{stat.label}</div>
                    <div className="text-xl font-medium text-white mt-1">{stat.value}</div>
                    <div className="text-[8px] text-white/35 mt-0.5">{stat.sub}</div>
                  </div>
                ))}
              </div>

              {/* Sentiment Chart */}
              <div className="rounded-lg bg-white/[0.03] ring-1 ring-white/5 p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-[10px] text-white/60 font-medium">Live Sentiment Feed</div>
                  <div className="text-[8px] text-white/30">Last 20 messages</div>
                </div>
                <div style={{ height: 120 }}>
                  <SentimentChart />
                </div>
              </div>

              {/* Message Cards */}
              <div className="space-y-1.5">
                {MESSAGES.map((m, i) => {
                  const style = ACTION_STYLES[m.action];
                  return (
                    <div
                      key={i}
                      className={`flex items-center gap-3 rounded-lg ${style.bg} ring-1 ring-white/5 px-3 py-2.5 border-l-2 ${style.border}`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-[11px] text-white/80 truncate">{m.text}</div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="text-[10px] text-white/50 font-mono">{m.score.toFixed(2)}</span>
                        <span className="text-[9px] text-white/40 capitalize">{m.emotion}</span>
                        <span className={`text-[9px] font-medium px-2 py-0.5 rounded-full ${style.bg} ${style.text}`}>
                          {m.action}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

            </div>
          </div>
        </div>
      </ScaledDashboard>
    </div>
  );
}
