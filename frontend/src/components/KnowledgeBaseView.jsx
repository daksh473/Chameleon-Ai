import { useState, useEffect } from "react";
import { Search, Database, Plus, CheckCircle2, Bot } from "lucide-react";

export default function KnowledgeBaseView() {
  const [faqs, setFaqs] = useState([]);
  const [query, setQuery] = useState("");
  const [searchResult, setSearchResult] = useState(null);
  const [searching, setSearching] = useState(false);
  const [filterLang, setFilterLang] = useState("all");

  // Form state
  const [newQ, setNewQ] = useState("");
  const [newA, setNewA] = useState("");
  const [newCat, setNewCat] = useState("general");
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFaqs();
  }, []);

  const fetchFaqs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/knowledge");
      if (res.ok) {
        setFaqs(await res.json());
      } else {
        throw new Error("Failed to fetch FAQs");
      }
    } catch (err) {
      console.error("Error fetching FAQs:", err);
      setError("Failed to load Knowledge Base");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setSearchResult(null);
    try {
      const res = await fetch("http://localhost:8000/knowledge/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      setSearchResult(data);
      if (data.is_kb) fetchFaqs(); // Refresh usage counts
    } catch (err) {
      console.error("Error searching KB:", err);
    } finally {
      setSearching(false);
    }
  };

  const handleAddFaq = async (e) => {
    e.preventDefault();
    if (!newQ.trim() || !newA.trim()) return;
    try {
      await fetch("http://localhost:8000/knowledge/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: newQ, answer: newA, category: newCat })
      });
      setNewQ(""); setNewA(""); setShowForm(false);
      fetchFaqs();
    } catch (err) {
      console.error("Error adding FAQ:", err);
    }
  };

  if (loading) return <div className="w-full h-full p-6 bg-[#1a1b1f] text-gray-400">Loading Knowledge Base...</div>;
  if (error) return <div className="w-full h-full p-6 bg-[#1a1b1f] text-red-400">Error: {error}</div>;

  return (
    <div className="w-full h-full flex flex-col p-6 bg-[#1a1b1f] overflow-y-auto text-white">
      
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Database size={20} /> Knowledge Base
          </h2>
          <p className="text-xs text-gray-500 mt-1">AI-powered FAQ search and management</p>
        </div>
        <button 
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-3 py-2 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded-lg text-sm transition-colors"
        >
          <Plus size={16} /> Add New FAQ
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAddFaq} className="mb-8 p-4 bg-[#232323] border border-gray-800 rounded-xl flex flex-col gap-4 animate-in fade-in">
          <h3 className="font-bold text-sm text-gray-300">Add New FAQ</h3>
          <input 
            value={newQ} onChange={e => setNewQ(e.target.value)} 
            placeholder="Question" className="p-2 bg-[#191919] border border-gray-700 rounded text-sm text-white outline-none focus:border-blue-500/50"
          />
          <textarea 
            value={newA} onChange={e => setNewA(e.target.value)} 
            placeholder="Answer" className="p-2 bg-[#191919] border border-gray-700 rounded text-sm text-white outline-none focus:border-blue-500/50 min-h-[80px]"
          />
          <div className="flex gap-4 items-center">
            <select 
              value={newCat} onChange={e => setNewCat(e.target.value)}
              className="p-2 bg-[#191919] border border-gray-700 rounded text-sm text-white outline-none"
            >
              <option value="general">General</option>
              <option value="shipping">Shipping</option>
              <option value="refund">Refund</option>
              <option value="account">Account</option>
              <option value="product">Product</option>
              <option value="payment">Payment</option>
            </select>
            <button type="submit" className="px-4 py-2 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 rounded text-sm font-semibold transition-colors">
              Save FAQ
            </button>
          </div>
        </form>
      )}

      {/* AI Search Engine */}
      <div className="mb-8">
        <div className="flex items-center bg-[#232323] border border-gray-800 rounded-lg p-2 focus-within:border-blue-500/50 transition-colors shadow-lg">
          <Search size={18} className="text-gray-500 ml-2" />
          <input 
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            placeholder="Ask a question to search the KB or get an AI answer..."
            className="flex-1 bg-transparent border-none outline-none text-white p-2 text-sm ml-2"
          />
          <button 
            onClick={handleSearch} disabled={searching || !query.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded font-semibold text-sm disabled:opacity-50"
          >
            {searching ? "Searching..." : "Search"}
          </button>
        </div>

        {searchResult && (
          <div className="mt-4 p-4 border rounded-xl animate-in fade-in slide-in-from-top-2 flex flex-col gap-2 
              bg-[#232323] border-gray-700 shadow-xl relative overflow-hidden">
            
            {/* Top Indicator Badge */}
            <div className="absolute top-0 left-0 w-full h-1" style={{ background: searchResult.is_kb ? '#30A46C' : '#3B82F6' }} />
            
            <div className="flex items-center gap-2 mb-2">
              {searchResult.is_kb ? (
                <span className="flex items-center gap-1 text-xs font-bold text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded border border-emerald-400/20">
                  <CheckCircle2 size={14} /> FOUND IN KNOWLEDGE BASE
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs font-bold text-blue-400 bg-blue-400/10 px-2 py-1 rounded border border-blue-400/20">
                  <Bot size={14} /> AI GENERATED ANSWER
                </span>
              )}
            </div>
            
            <div className="text-gray-300 text-sm leading-relaxed">
              {searchResult.answer}
            </div>
            
            {searchResult.is_kb && (
              <div className="text-[10px] text-gray-500 mt-2 uppercase tracking-wide">
                Source KB ID: {searchResult.kb_id}
              </div>
            )}
          </div>
        )}
      </div>

      {/* KB List */}
      <div>
        <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
          <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">All FAQ Entries</h3>
          <select 
            value={filterLang} 
            onChange={e => setFilterLang(e.target.value)}
            className="p-1 px-2 bg-[#232323] border border-gray-700 rounded text-xs text-white outline-none"
          >
            <option value="all">All Languages</option>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="hin">Hinglish</option>
            <option value="bn">Bengali</option>
            <option value="ta">Tamil</option>
            <option value="te">Telugu</option>
          </select>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(Array.isArray(faqs) ? faqs : []).filter(f => filterLang === "all" || f.language === filterLang).map(faq => (
            <div key={faq.id} className="bg-[#232323] border border-gray-800 rounded-xl p-4 flex flex-col hover:border-gray-600 transition-colors relative overflow-hidden group">
              <div className="text-[10px] uppercase font-bold text-gray-500 mb-2 flex justify-between">
                <span>{faq.category}</span>
                <span className="flex gap-2">
                  {faq.language && faq.language !== "en" && (
                    <span className="text-orange-400 bg-orange-400/10 px-1.5 py-0.5 rounded">🇮🇳 {faq.language.toUpperCase()}</span>
                  )}
                  <span className="text-blue-400 bg-blue-400/10 px-1.5 py-0.5 rounded">ID: {faq.id}</span>
                </span>
              </div>
              <h4 className="font-semibold text-sm mb-2 text-gray-200">{faq.question}</h4>
              <p className="text-xs text-gray-400 flex-1">{faq.answer}</p>
              
              <div className="mt-4 pt-3 border-t border-gray-800 flex justify-between items-center text-[10px] text-gray-500">
                <span>Used {faq.usage_count} times</span>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
