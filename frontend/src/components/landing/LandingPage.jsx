import React from 'react';
import {
  Waves, ChevronDown, LayoutDashboard, Share2, Users, Headset, CheckSquare,
  BarChart3, Crosshair, Mail, BookOpen, MessageSquare, ArrowUp
} from 'lucide-react';

/* ───────────────────────────────────────────────────────────────────
   Helper Components for Inline Charts & UI Elements
   ─────────────────────────────────────────────────────────────────── */

const MiniLineChart = ({ color, points }) => {
  const w = 100;
  const h = 30;
  const step = w / (points.length - 1);
  const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${i * step} ${h - p * h}`).join(' ');
  const areaPath = `${path} L ${w} ${h} L 0 ${h} Z`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-8 mt-2 overflow-visible">
      <defs>
        <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0.0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#grad-${color.replace('#', '')})`} />
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

const MiniBarChart = () => {
  const bars = [0.5, 0.7, 0.4, 0.9, 0.6, 0.8, 0.5, 0.7];
  return (
    <div className="flex items-end justify-between h-8 mt-2 gap-1 px-1">
      {bars.map((h, i) => (
        <div
          key={i}
          className={`flex-1 rounded-t-sm ${i === 3 || i === 5 ? 'bg-indigo-400' : 'bg-emerald-400'}`}
          style={{ height: `${h * 100}%` }}
        />
      ))}
    </div>
  );
};

const TrafficLights = () => (
  <div className="flex items-center gap-1.5 shrink-0">
    <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
    <div className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
    <div className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
  </div>
);

const AlertCard = ({ title, desc, time, type }) => {
  const borderColors = {
    danger: 'border-l-red-500',
    success: 'border-l-emerald-500',
    info: 'border-l-blue-500'
  };
  const textColors = {
    danger: 'text-red-400',
    success: 'text-emerald-400',
    info: 'text-blue-400'
  };

  return (
    <div className={`bg-white/5 rounded-lg border-l-2 ${borderColors[type]} p-2.5 mb-2 relative`}>
      <div className={`text-[10px] font-semibold ${textColors[type]} mb-1`}>{title}</div>
      <div className="text-[9px] text-gray-400 leading-tight pr-6">{desc}</div>
      <div className="absolute top-2.5 right-2.5 text-[8px] text-gray-500">{time}</div>
    </div>
  );
};

/* ───────────────────────────────────────────────────────────────────
   Main Landing Page Component
   ─────────────────────────────────────────────────────────────────── */

export default function LandingPage({ onStart }) {
  return (
    <div className="min-h-[100svh] bg-[#0a0a0f] text-gray-200 font-sans overflow-x-hidden relative selection:bg-emerald-500/30 selection:text-emerald-100 flex flex-col">
      
      {/* ── Ambient Background Blobs ── */}
      <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] bg-emerald-900/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-[20%] left-[-10%] w-[500px] h-[500px] bg-indigo-900/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute top-[60%] right-[10%] w-[400px] h-[400px] bg-purple-900/10 rounded-full blur-[100px] pointer-events-none" />

      {/* ── Navbar ── */}
      <nav className="relative z-20 flex items-center justify-between px-6 py-5 max-w-7xl mx-auto w-full">
        {/* Logo */}
        <div className="flex items-center gap-2 cursor-pointer">
          <Waves className="w-6 h-6 text-emerald-400" />
          <span className="text-lg font-bold tracking-tight text-white">SentimentAI</span>
        </div>

        {/* Desktop Links */}
        <div className="hidden md:flex items-center gap-8">
          <button className="flex items-center gap-1.5 text-sm text-gray-300 hover:text-white transition-colors">
            Features <ChevronDown className="w-3.5 h-3.5" />
          </button>
          <button className="text-sm text-gray-300 hover:text-white transition-colors">How It Works</button>
          <button className="text-sm text-gray-300 hover:text-white transition-colors">Pricing</button>
        </div>

        {/* CTA */}
        <div>
          <button 
            onClick={onStart}
            className="bg-white text-gray-950 text-sm font-semibold px-5 py-2 rounded-full hover:bg-gray-200 transition-colors"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* ── Hero Content ── */}
      <main className="relative z-20 flex flex-col items-center justify-center flex-1 w-full max-w-5xl mx-auto px-4 mt-16 sm:mt-24 text-center">
        
        <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[80px] font-bold text-white leading-[1.05] tracking-tight">
          Understand emotion.<br/>
          Act in real time.
        </h1>
        
        <form 
          className="mt-10 sm:mt-12 w-full max-w-[600px] relative"
          onSubmit={(e) => { e.preventDefault(); if (onStart) onStart(); }}
        >
          <div className="flex items-center bg-[#1a1a22]/80 backdrop-blur-md rounded-full ring-1 ring-white/10 pl-6 pr-2 py-2 shadow-xl focus-within:ring-emerald-500/50 transition-shadow">
            <input 
              type="text" 
              placeholder="Type a customer message to analyze..." 
              className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none text-base"
            />
            <button 
              type="submit"
              className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors shrink-0"
            >
              <ArrowUp className="w-5 h-5" />
            </button>
          </div>
        </form>

        <p className="mt-8 text-sm sm:text-base text-gray-400 max-w-2xl leading-relaxed">
          Detect sentiment, auto-escalate frustration, and trigger upsells — <br className="hidden sm:block"/>
          powered by AI that responds in under 1 second.
        </p>

        <div className="flex items-center gap-6 mt-6">
          <button onClick={onStart} className="text-sm text-gray-400 hover:text-white underline decoration-gray-600 underline-offset-4 transition-colors">
            See live demo
          </button>
          <a href="https://github.com/daksh473/Chameleon-Ai" target="_blank" rel="noreferrer" className="text-sm text-gray-400 hover:text-white underline decoration-gray-600 underline-offset-4 transition-colors">
            View on GitHub
          </a>
        </div>

        <div className="mt-10 sm:mt-12 mb-20 sm:mb-32">
          <button 
            onClick={onStart}
            className="bg-gradient-to-r from-emerald-600 to-teal-500 text-white text-base font-bold px-8 py-3.5 rounded-full shadow-[0_0_30px_rgba(16,185,129,0.25)] hover:shadow-[0_0_40px_rgba(16,185,129,0.4)] hover:scale-105 transition-all active:scale-95"
          >
            See Live Demo
          </button>
        </div>

      </main>

      {/* ── Mockup Windows Section ── */}
      <section className="relative z-20 w-full max-w-[1400px] mx-auto px-4 pb-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 items-start">

          {/* ────────────────────────────────────────────────────────
              WINDOW 1: Live Chat
              ──────────────────────────────────────────────────────── */}
          <div className="w-full rounded-2xl overflow-hidden bg-[#1a1a22]/95 backdrop-blur-xl shadow-2xl ring-1 ring-white/10 flex flex-col h-[500px]">
            {/* Header */}
            <div className="bg-emerald-900/20 border-b border-white/5 px-4 py-3 flex items-center justify-between shrink-0">
              <TrafficLights />
              <div className="text-[11px] font-semibold text-emerald-100/70 tracking-wide">Sentiment AI | Live Chat</div>
              <div className="w-10"></div>
            </div>

            {/* Body */}
            <div className="flex flex-1 overflow-hidden">
              {/* Sidebar */}
              <div className="w-16 border-r border-white/5 bg-black/20 flex flex-col items-center py-4 gap-6 shrink-0">
                <LayoutDashboard className="w-4 h-4 text-gray-500" />
                <Share2 className="w-4 h-4 text-gray-500" />
                <Users className="w-4 h-4 text-gray-500" />
                <Headset className="w-4 h-4 text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.5)]" />
                <CheckSquare className="w-4 h-4 text-gray-500" />
                <BarChart3 className="w-4 h-4 text-gray-500" />
                <Crosshair className="w-4 h-4 text-gray-500" />
                <Mail className="w-4 h-4 text-gray-500" />
                <BookOpen className="w-4 h-4 text-gray-500" />
              </div>

              {/* Chat Area (Empty State) */}
              <div className="flex-1 flex flex-col relative bg-black/10">
                <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-emerald-500/20 to-teal-900/40 flex items-center justify-center mb-6 ring-1 ring-emerald-500/30">
                    {/* Abstract Chameleon / Mascot rep */}
                    <div className="relative">
                      <Waves className="w-12 h-12 text-emerald-400" />
                      <div className="absolute -top-1 -right-2 w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-md">
                        <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />
                      </div>
                    </div>
                  </div>
                  <h3 className="text-xl font-medium text-white mb-2">Welcome to Sentiment AI</h3>
                  <p className="text-[11px] text-gray-400 max-w-[200px] leading-relaxed">
                    Analyze sentiment, auto-escalate, and resolve cases intelligently.
                  </p>
                </div>
                
                {/* Input Bar */}
                <div className="p-4 border-t border-white/5 bg-black/20 shrink-0">
                  <div className="bg-white/5 rounded-full px-4 py-2.5 flex items-center gap-3">
                    <div className="w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400"></div>
                    </div>
                    <div className="text-[11px] text-gray-500 flex-1">Simulating a customer interaction...</div>
                  </div>
                </div>
              </div>

              {/* Right Panel: Mood Level & Alerts */}
              <div className="w-64 border-l border-white/5 bg-black/20 p-4 shrink-0 flex flex-col">
                <div className="text-[10px] font-bold tracking-wider text-gray-500 mb-4">LIVE AGENT MOOD LEVEL</div>
                
                {/* Mood Slider Graphic */}
                <div className="bg-white/5 rounded-lg p-3 mb-6 ring-1 ring-white/5 flex items-center gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-500"></div>
                      <span className="text-[10px] text-gray-300 font-medium">95%</span>
                    </div>
                    <div className="text-[8px] text-gray-500 leading-tight">Extreme frustration detected in thread ID-8942</div>
                  </div>
                  {/* Vertical Gradient Bar */}
                  <div className="w-2 h-16 rounded-full bg-gradient-to-b from-red-500 via-yellow-500 to-emerald-500 relative">
                    {/* Indicator */}
                    <div className="absolute -left-1 top-2 w-4 h-1 bg-white rounded-sm shadow-sm"></div>
                  </div>
                </div>

                {/* Alerts List */}
                <div className="flex-1 overflow-hidden flex flex-col">
                  <div className="text-[10px] font-bold tracking-wider text-gray-500 mb-3">RECENT ALERTS</div>
                  <div className="flex-1 overflow-y-auto pr-1">
                    <AlertCard 
                      title="High Frustration (0.12)" 
                      desc="Message: 'I've been waiting for 3 weeks...'" 
                      time="10:24 AM" 
                      type="danger" 
                    />
                    <AlertCard 
                      title="Joy / Gratitude (0.91)" 
                      desc="Message: 'Thank you so much, works perfectly!'" 
                      time="10:15 AM" 
                      type="success" 
                    />
                    <AlertCard 
                      title="Neutral Inquiry (0.55)" 
                      desc="Message: 'Can I check my order status?'" 
                      time="10:02 AM" 
                      type="info" 
                    />
                    <AlertCard 
                      title="Escalation Risk (0.28)" 
                      desc="Message: 'This isn't what I ordered...'" 
                      time="09:45 AM" 
                      type="danger" 
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ────────────────────────────────────────────────────────
              WINDOW 2: Agent Performance
              ──────────────────────────────────────────────────────── */}
          <div className="w-full rounded-2xl overflow-hidden bg-[#1a1a22]/95 backdrop-blur-xl shadow-2xl ring-1 ring-white/10 flex flex-col h-[500px]">
            {/* Header */}
            <div className="bg-blue-900/20 border-b border-white/5 px-4 py-3 flex items-center justify-between shrink-0">
              <TrafficLights />
              <div className="text-[11px] font-semibold text-blue-100/70 tracking-wide">Agent Performance | Real Time</div>
              <div className="w-10"></div>
            </div>

            {/* Body */}
            <div className="flex flex-1 overflow-hidden">
              {/* Sidebar */}
              <div className="w-48 border-r border-white/5 bg-black/20 p-3 shrink-0 hidden sm:block">
                <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-white/10 text-white">
                  <BarChart3 className="w-4 h-4 text-blue-400" />
                  <span className="text-[11px] font-medium">Agent Performance</span>
                </div>
              </div>

              {/* Main Content Area */}
              <div className="flex-1 p-5 bg-black/10 overflow-y-auto">
                
                {/* Top Stat Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
                  {/* Card 1 */}
                  <div className="bg-white/5 rounded-lg p-3 ring-1 ring-white/5">
                    <div className="flex justify-between items-start">
                      <div className="text-[10px] text-gray-400 font-medium">Tickets Closed</div>
                      <div className="text-[10px] text-emerald-400 font-bold">37 items</div>
                    </div>
                    <MiniLineChart color="#34d399" points={[0.2, 0.4, 0.3, 0.8, 0.6, 0.9, 0.7]} />
                  </div>
                  {/* Card 2 */}
                  <div className="bg-white/5 rounded-lg p-3 ring-1 ring-white/5">
                    <div className="flex justify-between items-start">
                      <div className="text-[10px] text-gray-400 font-medium">Avg Resolution</div>
                      <div className="text-[10px] text-blue-400 font-bold">24 mins</div>
                    </div>
                    <MiniLineChart color="#60a5fa" points={[0.6, 0.5, 0.7, 0.4, 0.6, 0.3, 0.5]} />
                  </div>
                  {/* Card 3 */}
                  <div className="bg-white/5 rounded-lg p-3 ring-1 ring-white/5">
                    <div className="flex justify-between items-start">
                      <div className="text-[10px] text-gray-400 font-medium">Customer Sat Score</div>
                      <div className="text-[10px] text-indigo-400 font-bold">96/100</div>
                    </div>
                    <MiniBarChart />
                  </div>
                </div>

                {/* Table Section */}
                <div className="text-[12px] font-semibold text-white mb-3">Agent Performance</div>
                <div className="bg-white/5 rounded-lg ring-1 ring-white/5 overflow-hidden">
                  
                  {/* Table Header */}
                  <div className="grid grid-cols-4 md:grid-cols-5 gap-4 px-4 py-2 border-b border-white/5 text-[9px] font-bold text-gray-500 uppercase tracking-wider">
                    <div className="col-span-2 md:col-span-2">Agent Name</div>
                    <div>Closed</div>
                    <div className="hidden md:block">Avg Time</div>
                    <div>CSAT</div>
                  </div>
                  
                  {/* Table Rows */}
                  {[
                    { name: 'James K.', closed: 21, time: '16m', csat: 98, avatar: 'J', color: 'bg-orange-500' },
                    { name: 'Alex T.', closed: 19, time: '20m', csat: 93, avatar: 'A', color: 'bg-purple-500' },
                    { name: 'Maria L.', closed: 20, time: '18m', csat: 92, avatar: 'M', color: 'bg-pink-500' },
                    { name: 'David R.', closed: 15, time: '22m', csat: 89, avatar: 'D', color: 'bg-teal-500' },
                  ].map((agent, i) => (
                    <div key={i} className="grid grid-cols-4 md:grid-cols-5 gap-4 px-4 py-3 border-b border-white/5 last:border-0 items-center hover:bg-white/[0.02] transition-colors">
                      <div className="col-span-2 md:col-span-2 flex items-center gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white shadow-inner ${agent.color}`}>
                          {agent.avatar}
                        </div>
                        <span className="text-[11px] text-white font-medium">{agent.name}</span>
                      </div>
                      <div className="text-[11px] text-gray-300">{agent.closed}</div>
                      <div className="hidden md:block text-[11px] text-gray-300">{agent.time}</div>
                      <div className="flex items-center justify-between pr-2">
                        <span className="text-[12px] font-bold text-white">{agent.csat}</span>
                        <div className="px-2 py-0.5 rounded text-[8px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                          Real Time
                        </div>
                      </div>
                    </div>
                  ))}

                </div>
              </div>
            </div>
          </div>

        </div>
      </section>

    </div>
  );
}
