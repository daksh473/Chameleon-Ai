import React, { useState } from 'react';
import { User, Image as ImageIcon, Globe, Palette, Type, Shield, Trash2 } from 'lucide-react';

export default function SettingsView({ lang, setLang }) {
  const [username, setUsername] = useState('Agent_47');
  const [theme, setTheme] = useState('emerald-dark');
  const [fontSize, setFontSize] = useState(50); // 0 to 100
  const [retention, setRetention] = useState(3); // 0: 24h, 1: 1w, 2: 1m, 3: all

  const retentionLabels = ['24 Hours', '1 Week', '1 Month', 'All Data'];

  // Support Email Config
  const [emailHost, setEmailHost] = useState(localStorage.getItem("emailHost") || "");
  const [emailPort, setEmailPort] = useState(localStorage.getItem("emailPort") || "587");
  const [emailUser, setEmailUser] = useState(localStorage.getItem("emailUser") || "");
  const [emailPass, setEmailPass] = useState(localStorage.getItem("emailPass") || "");

  const handleSave = () => {
    localStorage.setItem("theme", theme);
    localStorage.setItem("language", lang);
    localStorage.setItem("emailHost", emailHost);
    localStorage.setItem("emailPort", emailPort);
    localStorage.setItem("emailUser", emailUser);
    localStorage.setItem("emailPass", emailPass);
    alert("Settings saved!");
  };

  const testEmailConnection = () => {
    alert("Testing IMAP/SMTP connection... (Mock success)\nConnected successfully to " + emailHost);
  };

  const handleWipe = () => {
    // Mock wipe action
    alert(`Data wipe executed for retention level: ${retentionLabels[retention]}`);
  };

  return (
    <div className="flex-1 w-full h-full min-h-[80vh] flex flex-col items-center justify-center overflow-y-auto bg-[#111214] text-gray-200 p-8 md:p-12 animate-in fade-in duration-300">
      <div className="w-full max-w-xl mx-auto shadow-2xl">
        {/* Header Zone */}
        <header className="mb-10 border-b border-[#2a2b2f] pb-6">
          <h1 className="text-3xl font-serif font-bold text-white tracking-wide">
            Chameleon AI Settings
          </h1>
          <p className="text-gray-400 mt-2 text-sm">Manage your workspace preferences and data retention.</p>
        </header>

        <div className="space-y-10 block pb-16">
          
          {/* Panel 1: Profile & Account Settings */}
          <div style={{ marginBottom: '36px', display: 'block' }}>
            <section className="bg-[#18191c] border border-[#2a2b2f] rounded-xl p-6 shadow-xl">
              <div className="flex items-center gap-3 border-b border-[#2a2b2f] pb-4" style={{ marginBottom: '16px', display: 'flex' }}>
              <User className="text-[#10b981]" size={20} />
              <h2 className="text-lg font-semibold text-white">Profile & Account</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Profile Picture */}
              <div className="flex flex-col gap-3">
                <label className="text-sm text-gray-400 font-medium">Profile Picture</label>
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-full border-2 border-[#10b981] bg-[#111214] overflow-hidden flex items-center justify-center relative group cursor-pointer">
                    <img src="/brand-eye-icon.png" alt="Profile" className="w-10 h-10 object-contain filter invert-[48%] sepia-[79%] saturate-[2476%] hue-rotate-[86deg] brightness-[118%] contrast-[119%]" />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                      <ImageIcon size={16} className="text-white" />
                    </div>
                  </div>
                  <button className="text-xs text-gray-400 hover:text-white transition-colors border border-[#2a2b2f] rounded-md px-3 py-1.5 bg-[#111214]">
                    Change Avatar
                  </button>
                </div>
              </div>

              {/* Username & Language */}
              <div className="flex flex-col gap-5">
                <div className="flex flex-col gap-2">
                  <label className="text-sm text-gray-400 font-medium">Username</label>
                  <input 
                    type="text" 
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="bg-[#111214] border border-[#2a2b2f] text-white rounded-md px-4 py-2.5 text-sm focus:outline-none focus:border-[#10b981] focus:ring-1 focus:ring-[#10b981] transition-all w-full"
                    placeholder="Enter username"
                  />
                </div>
                
                <div className="flex flex-col gap-2">
                  <label className="text-sm text-gray-400 font-medium">Language Settings</label>
                  <div className="relative">
                    <select 
                      value={lang || 'en'}
                      onChange={(e) => setLang(e.target.value)}
                      className="bg-[#111214] border border-[#2a2b2f] text-white rounded-md px-4 py-2.5 text-sm focus:outline-none focus:border-[#10b981] focus:ring-1 focus:ring-[#10b981] transition-all w-full appearance-none cursor-pointer"
                    >
                      <option value="en">English (US)</option>
                      <option value="hi">Hindi (IN)</option>
                      <option value="es">Spanish (ES)</option>
                      <option value="fr">French (FR)</option>
                    </select>
                    <Globe className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" size={16} />
                  </div>
                </div>
              </div>
            </div>
          </section>
          </div>

          {/* Panel 1.5: Support Email Config */}
          <div style={{ marginBottom: '36px', display: 'block' }}>
            <section className="bg-[#18191c] border border-[#2a2b2f] rounded-xl p-6 shadow-xl">
              <div className="flex items-center gap-3 border-b border-[#2a2b2f] pb-4" style={{ marginBottom: '16px', display: 'flex' }}>
              <h2 className="text-lg font-semibold text-white">Support Email Configuration</h2>
            </div>
            
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex flex-col gap-2">
                  <label className="text-sm text-gray-400 font-medium">SMTP/IMAP Host</label>
                  <input 
                    type="text" 
                    className="bg-[#111214] border border-[#2a2b2f] text-white rounded-md px-4 py-2.5 text-sm focus:outline-none focus:border-[#10b981] transition-all"
                    placeholder="e.g. smtp.gmail.com" 
                    value={emailHost} 
                    onChange={e => setEmailHost(e.target.value)} 
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-sm text-gray-400 font-medium">Port</label>
                  <input 
                    type="text" 
                    className="bg-[#111214] border border-[#2a2b2f] text-white rounded-md px-4 py-2.5 text-sm focus:outline-none focus:border-[#10b981] transition-all"
                    placeholder="e.g. 587" 
                    value={emailPort} 
                    onChange={e => setEmailPort(e.target.value)} 
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex flex-col gap-2">
                  <label className="text-sm text-gray-400 font-medium">Email Address</label>
                  <input 
                    type="email" 
                    className="bg-[#111214] border border-[#2a2b2f] text-white rounded-md px-4 py-2.5 text-sm focus:outline-none focus:border-[#10b981] transition-all"
                    placeholder="support@company.com" 
                    value={emailUser} 
                    onChange={e => setEmailUser(e.target.value)} 
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-sm text-gray-400 font-medium">App Password</label>
                  <input 
                    type="password" 
                    className="bg-[#111214] border border-[#2a2b2f] text-white rounded-md px-4 py-2.5 text-sm focus:outline-none focus:border-[#10b981] transition-all"
                    placeholder="••••••••••••" 
                    value={emailPass} 
                    onChange={e => setEmailPass(e.target.value)} 
                  />
                </div>
              </div>
              <div className="flex items-center gap-4 pt-2">
                <button 
                  onClick={testEmailConnection}
                  className="bg-[#2a2b2f] hover:bg-[#3f4045] text-white px-4 py-2 rounded-md text-sm font-semibold transition-all"
                >
                  Test Connection
                </button>
                <button 
                  onClick={handleSave}
                  className="bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/50 hover:bg-[#10b981] hover:text-white px-4 py-2 rounded-md text-sm font-semibold transition-all"
                >
                  Save Settings
                </button>
              </div>
            </div>
          </section>
          </div>

          {/* Panel 2: Appearance Configuration */}
          <div style={{ marginBottom: '36px', display: 'block' }}>
            <section className="bg-[#18191c] border border-[#2a2b2f] rounded-xl p-6 shadow-xl">
              <div className="flex items-center gap-3 border-b border-[#2a2b2f] pb-4" style={{ marginBottom: '16px', display: 'flex' }}>
              <Palette className="text-[#10b981]" size={20} />
              <h2 className="text-lg font-semibold text-white">Appearance Configuration</h2>
            </div>
            
            <div className="space-y-8">
              {/* Theme Selector */}
              <div className="flex flex-col gap-3">
                <label className="text-sm text-gray-400 font-medium">Dashboard Theme</label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {[
                    { id: 'emerald-dark', label: 'Emerald Dark' },
                    { id: 'pure-void', label: 'Pure Void' },
                    { id: 'classic-light', label: 'Classic Light' }
                  ].map(t => (
                    <button
                      key={t.id}
                      onClick={() => setTheme(t.id)}
                      className={`py-3 px-4 rounded-md text-sm font-medium transition-all ${
                        theme === t.id 
                          ? 'bg-[#10b981]/10 border-2 border-[#10b981] text-[#10b981]' 
                          : 'bg-[#111214] border-2 border-[#2a2b2f] text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Font Size */}
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-2">
                  <Type className="text-gray-400" size={16} />
                  <label className="text-sm text-gray-400 font-medium">Font Size Controller</label>
                </div>
                <div className="px-2">
                  <input 
                    type="range" 
                    min="0" max="100" 
                    value={fontSize}
                    onChange={(e) => setFontSize(e.target.value)}
                    className="w-full h-1.5 bg-[#2a2b2f] rounded-lg appearance-none cursor-pointer accent-[#10b981]"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-2 font-mono">
                    <span>Small</span>
                    <span>Medium</span>
                    <span>Large</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
          </div>

          {/* Panel 3: Privacy & Data */}
          <div style={{ marginBottom: '36px', display: 'block' }}>
            <section className="bg-[#18191c] border border-[#2a2b2f] rounded-xl p-6 shadow-xl">
              <div className="flex items-center gap-3 border-b border-[#2a2b2f] pb-4" style={{ marginBottom: '16px', display: 'flex' }}>
              <Shield className="text-[#10b981]" size={20} />
              <h2 className="text-lg font-semibold text-white">Privacy & Data Compliance</h2>
            </div>
            
            <div className="space-y-8">
              {/* Retention Slider */}
              <div className="flex flex-col gap-4">
                <label className="text-sm text-gray-400 font-medium">Select Data Retention Limit</label>
                <div className="px-2">
                  <input 
                    type="range" 
                    min="0" max="3" step="1"
                    value={retention}
                    onChange={(e) => setRetention(parseInt(e.target.value))}
                    className="w-full h-1.5 bg-[#2a2b2f] rounded-lg appearance-none cursor-pointer accent-[#10b981]"
                  />
                  <div className="flex justify-between text-xs text-gray-400 mt-3 font-mono">
                    {retentionLabels.map((lbl, i) => (
                      <span key={i} className={retention === i ? "text-[#10b981] font-bold" : ""}>
                        {lbl}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Data Wipe */}
              <div className="pt-4 border-t border-[#2a2b2f] flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-sm text-gray-400">
                  Executing a log clearance will permanently delete analytics older than the selected retention period.
                </div>
                <button 
                  onClick={handleWipe}
                  className="whitespace-nowrap flex items-center gap-2 bg-red-500/10 text-red-500 border border-red-500/50 hover:bg-red-500 hover:text-white px-5 py-2.5 rounded-md text-sm font-semibold transition-all shadow-[0_0_15px_rgba(239,68,68,0.1)] hover:shadow-[0_0_20px_rgba(239,68,68,0.4)]"
                >
                  <Trash2 size={16} />
                  Clear Database Logs
                </button>
              </div>
            </div>
          </section>
          </div>

        </div>
      </div>
    </div>
  );
}
