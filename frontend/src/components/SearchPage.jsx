// frontend/src/components/SearchPage.jsx
import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || (
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000'
    : window.location.origin
);

export default function SearchPage({ onStartAnalysis, onLoadHistory, onStartComparison }) {
  const [ticker, setTicker] = useState('');
  const [companyName, setCompanyName] = useState('');
  
  // Watchlist & History states
  const [watchlist, setWatchlist] = useState([]);
  const [history, setHistory] = useState([]);
  
  // Comparison inputs
  const [compA, setCompA] = useState('');
  const [compB, setCompB] = useState('');

  // Fetch watchlist and history on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/watchlist`)
      .then(res => res.json())
      .then(data => setWatchlist(data || []))
      .catch(err => console.error("Error loading watchlist:", err));

    fetch(`${API_BASE}/api/history`)
      .then(res => res.json())
      .then(data => setHistory(data || []))
      .catch(err => console.error("Error loading history:", err));
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!ticker.trim()) return;
    onStartAnalysis(ticker.trim().toUpperCase(), companyName.trim());
  };

  const handleQuickSelect = (selTicker, selName) => {
    setTicker(selTicker);
    setCompanyName(selName || '');
  };

  const handleRemoveWatchlist = (e, tick) => {
    e.stopPropagation(); // prevent search selection trigger
    fetch(`${API_BASE}/api/watchlist/${tick}`, { method: 'DELETE' })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setWatchlist(prev => prev.filter(item => item.ticker !== tick));
        }
      })
      .catch(err => console.error("Error removing from watchlist:", err));
  };

  const handleCompareSubmit = (e) => {
    e.preventDefault();
    if (!compA.trim() || !compB.trim()) return;
    onStartComparison(compA.trim().toUpperCase(), compB.trim().toUpperCase());
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start mt-6">
      
      {/* LEFT COLUMN: HERO INTRO, SEARCH PANEL, WATCHLIST, COMPARE */}
      <div className="lg:col-span-7 flex flex-col gap-8 text-left">
        
        {/* Left Hero description */}
        <section className="flex flex-col gap-2">
          <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight font-display">
            Multi-Agent Stock Analysis
          </h2>
          <p className="text-gray-400 text-sm md:text-base">
            Enter a ticker below to trigger our automated research, valuation, and sentiment pipeline.
          </p>
        </section>

        {/* Search glass card */}
        <div className="bg-brand-card backdrop-blur-md border border-white/5 shadow-2xl rounded-2xl p-6 md:p-8 hover:border-blue-500/20 transition-all duration-300">
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-5">
              <div className="flex flex-col gap-2 sm:col-span-3">
                <label htmlFor="ticker-input" className="text-[10px] font-bold tracking-wider uppercase text-purple-400">
                  Stock Ticker
                </label>
                <input
                  type="text"
                  id="ticker-input"
                  className="bg-slate-900/60 border border-white/5 rounded-xl px-4 py-3 text-white font-sans text-sm focus:border-blue-500 focus:ring-3 focus:ring-blue-500/25 outline-none transition-all"
                  placeholder="e.g. AAPL, MSFT, TSLA"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value)}
                  required
                  autoComplete="off"
                />
              </div>
              <div className="flex flex-col gap-2 sm:col-span-2">
                <label htmlFor="company-input" className="text-[10px] font-bold tracking-wider uppercase text-purple-400">
                  Company Name (Optional)
                </label>
                <input
                  type="text"
                  id="company-input"
                  className="bg-slate-900/60 border border-white/5 rounded-xl px-4 py-3 text-white font-sans text-sm focus:border-blue-500 focus:ring-3 focus:ring-blue-500/25 outline-none transition-all"
                  placeholder="e.g. Apple Inc."
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  autoComplete="off"
                />
              </div>
            </div>
            
            <div className="flex justify-center mt-1">
              <button
                type="submit"
                className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-bold py-3 px-8 rounded-xl font-display text-sm transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/25 hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
              >
                Launch Analysis Pipeline
              </button>
            </div>
          </form>

          {/* Quick selects */}
          <div className="mt-5 flex flex-wrap gap-2 items-center justify-start border-t border-white/5 pt-3">
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mr-1">Quick Select:</span>
            {[
              { t: 'AAPL', n: 'Apple Inc.' },
              { t: 'MSFT', n: 'Microsoft Corporation' },
              { t: 'TSLA', n: 'Tesla Inc.' },
              { t: 'RELIANCE.NS', n: 'Reliance Industries' },
              { t: 'TCS.NS', n: 'Tata Consultancy Services' }
            ].map((item) => (
              <button
                key={item.t}
                onClick={() => handleQuickSelect(item.t, item.n)}
                className="bg-indigo-500/5 border border-indigo-500/15 text-indigo-300 px-2.5 py-0.5 rounded-full font-semibold text-[10px] transition-all hover:bg-indigo-500/20 hover:border-indigo-500 hover:text-white cursor-pointer"
              >
                {item.t}
              </button>
            ))}
          </div>
        </div>

        {/* Watchlist card */}
        <div className="bg-brand-card backdrop-blur-md border border-white/5 shadow-xl rounded-2xl p-6 hover:border-indigo-500/10 transition-all duration-300">
          <h3 className="text-xs font-black text-indigo-400 font-display uppercase tracking-widest mb-3">Your Watchlist</h3>
          {watchlist.length === 0 ? (
            <p className="text-gray-500 text-xs italic">No stocks watchlisted yet. Start an analysis and toggle the star to save.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {watchlist.map((item) => (
                <div 
                  key={item.ticker} 
                  onClick={() => handleQuickSelect(item.ticker, item.company_name)}
                  className="flex justify-between items-center bg-white/[0.02] border border-white/5 rounded-xl px-4 py-2.5 hover:border-white/10 transition-all cursor-pointer"
                >
                  <div className="flex flex-col text-left">
                    <span className="text-xs font-bold text-white font-display">{item.ticker}</span>
                    <span className="text-[10px] text-gray-400 truncate max-w-[150px]">{item.company_name || 'Stock'}</span>
                  </div>
                  <button 
                    onClick={(e) => handleRemoveWatchlist(e, item.ticker)}
                    className="text-gray-500 hover:text-red-400 text-xs font-black p-1 transition-all cursor-pointer select-none"
                    title="Remove from Watchlist"
                  >
                    🗑
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Comparison card */}
        <div className="bg-brand-card backdrop-blur-md border border-white/5 shadow-xl rounded-2xl p-6 hover:border-indigo-500/10 transition-all duration-300">
          <h3 className="text-xs font-black text-indigo-400 font-display uppercase tracking-widest mb-3">Compare Stocks</h3>
          <form onSubmit={handleCompareSubmit} className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5 text-left">
                <label className="text-[9px] font-bold uppercase tracking-wider text-purple-400">Ticker A</label>
                <input 
                  type="text"
                  placeholder="e.g. ZOMATO.NS"
                  value={compA}
                  onChange={(e) => setCompA(e.target.value)}
                  className="bg-slate-900/60 border border-white/5 rounded-xl px-3 py-2.5 text-white font-sans text-xs outline-none focus:border-indigo-500 transition-all"
                  required
                />
              </div>
              <div className="flex flex-col gap-1.5 text-left">
                <label className="text-[9px] font-bold uppercase tracking-wider text-purple-400">Ticker B</label>
                <input 
                  type="text"
                  placeholder="e.g. SWIGGY.NS"
                  value={compB}
                  onChange={(e) => setCompB(e.target.value)}
                  className="bg-slate-900/60 border border-white/5 rounded-xl px-3 py-2.5 text-white font-sans text-xs outline-none focus:border-indigo-500 transition-all"
                  required
                />
              </div>
            </div>
            <button 
              type="submit"
              className="w-full bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-indigo-300 font-bold py-2.5 rounded-xl text-xs font-display transition-all cursor-pointer"
            >
              Compare Side-by-Side
            </button>
          </form>
        </div>

      </div>

      {/* RIGHT COLUMN: PIPELINE & RECENT REPORTS */}
      <div className="lg:col-span-5 flex flex-col gap-6 text-left self-stretch justify-start">
        
        {/* Recent Reports History Log */}
        <div className="bg-slate-900/15 border border-white/5 rounded-2xl p-6 backdrop-blur-sm">
          <h3 className="text-xs font-black text-indigo-400 font-display uppercase tracking-widest mb-3">Recent Reports</h3>
          {history.length === 0 ? (
            <p className="text-gray-500 text-xs italic">No analysis history found.</p>
          ) : (
            <div className="flex flex-col gap-2.5 max-h-60 overflow-y-auto pr-1">
              {history.map((run) => (
                <div 
                  key={run.task_id}
                  onClick={() => onLoadHistory(run.task_id, run.ticker, run.company_name)}
                  className="flex items-center justify-between p-3 bg-white/[0.01] border border-white/5 rounded-xl hover:border-indigo-500/25 hover:bg-white/[0.02] cursor-pointer transition-all"
                >
                  <div className="flex flex-col text-left">
                    <span className="text-xs font-bold text-white font-display">{run.ticker}</span>
                    <span className="text-[9px] text-gray-500 font-sans truncate max-w-[150px]">{run.company_name || 'Stock'}</span>
                  </div>
                  <div className="flex flex-col items-end gap-1 select-none">
                    <span className={`text-[8px] font-black uppercase px-2 py-0.5 rounded ${
                      run.rating === 'BUY' ? 'bg-emerald-500/10 text-emerald-400' :
                      run.rating === 'SELL' ? 'bg-rose-500/10 text-rose-400' :
                      'bg-amber-500/10 text-amber-400'
                    }`}>
                      {run.rating || 'HOLD'}
                    </span>
                    <span className="text-[8px] text-gray-600 font-mono font-medium">
                      {new Date(run.generated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pipeline workflows card */}
        <div className="bg-slate-900/15 border border-white/5 rounded-2xl p-6 backdrop-blur-sm">
          <div>
            <h3 className="text-xs font-black text-indigo-400 font-display uppercase tracking-widest mb-1">Pipeline Workflow</h3>
          </div>
          
          <div className="flex flex-col gap-3 mt-3">
            <div className="border border-white/5 bg-white/[0.01] rounded-xl p-4">
              <h5 className="text-xs font-bold text-white font-display">1. Market Research</h5>
              <p className="text-gray-400 text-xs leading-relaxed mt-0.5">
                Aggregates global financial news and tracks sentiment index metrics.
              </p>
            </div>
            <div className="border border-white/5 bg-white/[0.01] rounded-xl p-4">
              <h5 className="text-xs font-bold text-white font-display">2. Financial Analysis</h5>
              <p className="text-gray-400 text-xs leading-relaxed mt-0.5">
                Extracts fundamental ratios and plots technical trend lines and charts.
              </p>
            </div>
            <div className="border border-white/5 bg-white/[0.01] rounded-xl p-4">
              <h5 className="text-xs font-bold text-white font-display">3. Report Compilation</h5>
              <p className="text-gray-400 text-xs leading-relaxed mt-0.5">
                Formulates an investment thesis, rating recommendations, and output reports.
              </p>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
