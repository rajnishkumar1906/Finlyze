// frontend/src/components/ComparePage.jsx
import React, { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || (
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000'
    : window.location.origin
);

export default function ComparePage({ ticker1, ticker2, onReset }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    
    fetch(`${API_BASE}/api/compare?ticker1=${encodeURIComponent(ticker1)}&ticker2=${encodeURIComponent(ticker2)}`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to retrieve comparison statistics from backend");
        return res.json();
      })
      .then(result => {
        setData(result);
        setLoading(false);
      })
      .catch(err => {
        console.error("Comparison fetch error:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [ticker1, ticker2]);

  // Format Helper for large currency numbers
  const formatMarketCap = (num) => {
    if (!num) return 'N/A';
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toLocaleString()}`;
  };

  const formatNumber = (num, decimals = 2, prefix = "", suffix = "") => {
    if (num === null || num === undefined) return 'N/A';
    return `${prefix}${num.toFixed(decimals)}${suffix}`;
  };

  if (loading) {
    return (
      <div className="max-w-4xl w-full mx-auto text-center py-20 animate-pulse">
        <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
        <h2 className="text-white text-lg font-bold font-display">Comparing {ticker1} vs {ticker2}...</h2>
        <p className="text-gray-400 text-xs mt-2">Fetching comparative financials and market capitalization indices</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-xl w-full mx-auto bg-rose-950/10 border border-rose-500/20 rounded-2xl p-8 text-center mt-10">
        <div className="text-red-400 text-3xl mb-3">⚠️</div>
        <h2 className="text-white text-base font-bold font-display">Failed to Load Comparison</h2>
        <p className="text-gray-400 text-xs mt-2 mb-6">{error}</p>
        <button onClick={onReset} className="bg-white/5 hover:bg-white/10 text-white font-bold text-xs px-6 py-2.5 rounded-lg border border-white/5 transition-all cursor-pointer">
          Back to Search
        </button>
      </div>
    );
  }

  const { ticker1: s1, ticker2: s2 } = data;

  const getRecommendationBadge = (rec) => {
    if (!rec || rec === 'N/A') return 'bg-white/5 text-gray-400';
    if (rec.includes('BUY') || rec.includes('OUTPERFORM')) return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/25';
    if (rec.includes('SELL') || rec.includes('UNDERPERFORM')) return 'bg-rose-500/10 text-rose-400 border border-rose-500/25';
    return 'bg-amber-500/10 text-amber-400 border border-amber-500/25';
  };

  return (
    <div className="max-w-6xl w-full mx-auto py-4 animate-fade-in text-left">
      {/* Back Button */}
      <button
        onClick={onReset}
        className="mb-6 flex items-center gap-2 text-xs font-bold text-gray-400 hover:text-white transition-all cursor-pointer bg-white/5 hover:bg-white/10 px-4 py-2 rounded-lg border border-white/5"
      >
        ← Back to Search
      </button>

      {/* Header */}
      <div className="mb-8">
        <h2 className="text-white text-2xl font-black font-display tracking-tight">Stock Comparison</h2>
        <p className="text-gray-400 text-xs mt-1">Side-by-side analysis of key valuation and volatility statistics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Ticker 1 Card */}
        <div className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 hover:border-indigo-500/20 transition-all duration-300">
          <div className="flex justify-between items-start mb-6">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-widest text-indigo-400">Stock A</span>
              <h3 className="text-white text-2xl font-black font-display tracking-tight mt-0.5">{s1.ticker}</h3>
              <p className="text-gray-400 text-xs mt-0.5">{s1.company_name}</p>
            </div>
            <span className={`text-[10px] font-black uppercase px-2.5 py-1 rounded-md tracking-wider ${getRecommendationBadge(s1.recommendation)}`}>
              {s1.recommendation || 'N/A'}
            </span>
          </div>

          {!s1.success ? (
            <div className="p-6 text-center text-xs text-gray-500 italic border border-dashed border-white/5 rounded-xl">
              Failed to load stats for {s1.ticker}: {s1.error}
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Current Price</span>
                <span className="text-sm font-bold text-white font-display">${s1.current_price?.toFixed(2) || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Market Capitalization</span>
                <span className="text-sm font-bold text-white font-display">{formatMarketCap(s1.market_cap)}</span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Price-to-Earnings (P/E)</span>
                <span className={`text-sm font-bold font-display ${s1.pe_ratio < 0 ? 'text-red-400' : 'text-white'}`}>
                  {formatNumber(s1.pe_ratio)}
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Beta (Volatility)</span>
                <span className="text-sm font-bold text-white font-display">{formatNumber(s1.beta)}</span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">52-Week Range</span>
                <span className="text-sm font-bold text-white font-display text-right">
                  ${s1.low_52w?.toFixed(2) || 'N/A'} - ${s1.high_52w?.toFixed(2) || 'N/A'}
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Volume (Avg)</span>
                <span className="text-xs text-gray-300 font-display text-right">
                  {s1.volume?.toLocaleString() || 'N/A'} <span className="text-gray-500">({s1.avg_volume?.toLocaleString() || 'N/A'})</span>
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Dividend Yield</span>
                <span className="text-sm font-bold text-white font-display">{formatNumber(s1.dividend_yield, 2, "", "%")}</span>
              </div>
              <div className="flex justify-between items-center py-2.5">
                <span className="text-xs text-gray-400 font-sans">Sector & Industry</span>
                <span className="text-xs text-gray-300 font-sans text-right max-w-[200px] truncate">
                  {s1.sector} <span className="text-gray-500">|</span> {s1.industry}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Ticker 2 Card */}
        <div className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 hover:border-indigo-500/20 transition-all duration-300">
          <div className="flex justify-between items-start mb-6">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-widest text-indigo-400">Stock B</span>
              <h3 className="text-white text-2xl font-black font-display tracking-tight mt-0.5">{s2.ticker}</h3>
              <p className="text-gray-400 text-xs mt-0.5">{s2.company_name}</p>
            </div>
            <span className={`text-[10px] font-black uppercase px-2.5 py-1 rounded-md tracking-wider ${getRecommendationBadge(s2.recommendation)}`}>
              {s2.recommendation || 'N/A'}
            </span>
          </div>

          {!s2.success ? (
            <div className="p-6 text-center text-xs text-gray-500 italic border border-dashed border-white/5 rounded-xl">
              Failed to load stats for {s2.ticker}: {s2.error}
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Current Price</span>
                <span className="text-sm font-bold text-white font-display">${s2.current_price?.toFixed(2) || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Market Capitalization</span>
                <span className="text-sm font-bold text-white font-display">{formatMarketCap(s2.market_cap)}</span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Price-to-Earnings (P/E)</span>
                <span className={`text-sm font-bold font-display ${s2.pe_ratio < 0 ? 'text-red-400' : 'text-white'}`}>
                  {formatNumber(s2.pe_ratio)}
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Beta (Volatility)</span>
                <span className="text-sm font-bold text-white font-display">{formatNumber(s2.beta)}</span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">52-Week Range</span>
                <span className="text-sm font-bold text-white font-display text-right">
                  ${s2.low_52w?.toFixed(2) || 'N/A'} - ${s2.high_52w?.toFixed(2) || 'N/A'}
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Volume (Avg)</span>
                <span className="text-xs text-gray-300 font-display text-right">
                  {s2.volume?.toLocaleString() || 'N/A'} <span className="text-gray-500">({s2.avg_volume?.toLocaleString() || 'N/A'})</span>
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-white/5">
                <span className="text-xs text-gray-400 font-sans">Dividend Yield</span>
                <span className="text-sm font-bold text-white font-display">{formatNumber(s2.dividend_yield, 2, "", "%")}</span>
              </div>
              <div className="flex justify-between items-center py-2.5">
                <span className="text-xs text-gray-400 font-sans">Sector & Industry</span>
                <span className="text-xs text-gray-300 font-sans text-right max-w-[200px] truncate">
                  {s2.sector} <span className="text-gray-500">|</span> {s2.industry}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Comparison Insights */}
      {s1.success && s2.success && (
        <div className="mt-8 bg-indigo-950/10 border border-indigo-500/10 rounded-2xl p-6">
          <h4 className="text-white font-extrabold text-sm mb-3 font-display flex items-center gap-2">
            <span>📊</span> Quick Valuation Comparison
          </h4>
          <p className="text-gray-300 text-xs leading-relaxed font-sans">
            {s1.ticker} ({s1.company_name}) has a market cap of <strong>{formatMarketCap(s1.market_cap)}</strong> compared to 
            {s2.ticker} ({s2.company_name}) at <strong>{formatMarketCap(s2.market_cap)}</strong>. 
            In terms of valuation metrics, {s1.ticker} is trading at a P/E of <strong>{formatNumber(s1.pe_ratio)}</strong>, while 
            {s2.ticker} trades at <strong>{formatNumber(s2.pe_ratio)}</strong>. 
            From a risk perspective, {s1.ticker} has a Beta of <strong>{formatNumber(s1.beta)}</strong> (market baseline is 1.0) 
            compared to {s2.ticker} at <strong>{formatNumber(s2.beta)}</strong>.
          </p>
        </div>
      )}
    </div>
  );
}
