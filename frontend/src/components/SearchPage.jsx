// frontend/src/components/SearchPage.jsx
import React, { useState } from 'react';

export default function SearchPage({ onStartAnalysis }) {
  const [ticker, setTicker] = useState('');
  const [companyName, setCompanyName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!ticker.trim()) return;
    onStartAnalysis(ticker.trim().toUpperCase(), companyName.trim());
  };

  const handleQuickSelect = (selTicker, selName) => {
    setTicker(selTicker);
    setCompanyName(selName);
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center mt-6">
      
      {/* LEFT COLUMN: HERO INTRO & SEARCH PANEL */}
      <div className="lg:col-span-7 flex flex-col gap-6 text-left">
        
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
      </div>

      {/* RIGHT COLUMN: PIPELINE & AGENTS DEFINITION */}
      <div className="lg:col-span-5 flex flex-col gap-4 text-left bg-slate-900/15 border border-white/5 rounded-2xl p-6 md:p-8 backdrop-blur-sm self-stretch justify-center">
        <div>
          <h3 className="text-xs font-black text-indigo-400 font-display uppercase tracking-widest mb-1">Pipeline Workflow</h3>
        </div>
        
        <div className="flex flex-col gap-3">
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
  );
}
