// frontend/src/components/AnalysisDashboard.jsx
import React, { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';

const API_BASE = import.meta.env.VITE_API_BASE || (
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000'
    : window.location.origin
);

export default function AnalysisDashboard({ taskId, ticker, onReset }) {
  const [taskData, setTaskData] = useState({
    status: "processing",
    ticker: ticker,
    company_name: "",
    current_step: 0,
    agent_status: { researcher: "pending", analyst: "pending", writer: "pending" },
    messages: ["[System] Initializing analysis pipeline..."],
    error: null,
    research_data: null,
    analysis_data: null,
    writer_data: null
  });

  const [activeNewsIdx, setActiveNewsIdx] = useState(null);
  const [jsonExpanded, setJsonExpanded] = useState(false);
  const [reportTab, setReportTab] = useState('thesis');
  const [zoomChartUrl, setZoomChartUrl] = useState(null);
  const logContainerRef = useRef(null);

  const [isSaved, setIsSaved] = useState(false);

  // Check watchlist status on ticker load
  useEffect(() => {
    if (taskData.ticker) {
      fetch(`${API_BASE}/api/watchlist/check/${encodeURIComponent(taskData.ticker)}`)
        .then(res => res.json())
        .then(data => setIsSaved(data.watchlisted))
        .catch(err => console.error("Error checking watchlist:", err));
    }
  }, [taskData.ticker]);

  const toggleWatchlist = () => {
    if (!taskData.ticker) return;
    if (isSaved) {
      fetch(`${API_BASE}/api/watchlist/${encodeURIComponent(taskData.ticker)}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
          if (data.success) setIsSaved(false);
        })
        .catch(err => console.error("Error removing from watchlist:", err));
    } else {
      fetch(`${API_BASE}/api/watchlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: taskData.ticker,
          company_name: taskData.company_name
        })
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) setIsSaved(true);
        })
        .catch(err => console.error("Error adding to watchlist:", err));
    }
  };

  useEffect(() => {
    const pollInterval = setInterval(() => {
      fetch(`${API_BASE}/api/status/${taskId}`)
        .then(res => {
          if (!res.ok) throw new Error("Task status lookup failed");
          return res.json();
        })
        .then(data => {
          setTaskData(data);
          if (data.status === "completed" || data.status === "failed") {
            clearInterval(pollInterval);
          }
        })
        .catch(err => {
          console.error("Error polling task:", err);
        });
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [taskId]);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [taskData.messages]);

  // Convert Matplotlib paths to absolute backend URLs
  const getAbsoluteUrl = (path) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    const cleanPath = path.replace(/\\/g, '/').replace('output/', '/api/output/');
    return `${API_BASE}${cleanPath}`;
  };

  // Helper to format market cap
  const formatMarketCap = (marketCap) => {
    if (!marketCap) return "N/A";
    if (marketCap >= 1e12) return `$${(marketCap/1e12).toFixed(2)}T`;
    if (marketCap >= 1e9) return `$${(marketCap/1e9).toFixed(2)}B`;
    if (marketCap >= 1e6) return `$${(marketCap/1e6).toFixed(2)}M`;
    return `$${marketCap.toLocaleString()}`;
  };

  const getAgentHeaderStyle = (status) => {
    if (status === 'completed') return 'border-emerald-500/25 bg-emerald-950/20';
    if (status === 'working') return 'border-amber-500/40 bg-amber-950/10 animate-pulse-glow';
    return 'border-white/5 bg-slate-900/10 opacity-50';
  };

  const getAgentBadge = (status) => {
    if (status === 'completed') return <span className="bg-emerald-500/20 text-emerald-400 text-xs px-3 py-1 rounded-full font-bold">Completed</span>;
    if (status === 'working') return <span className="bg-amber-500/20 text-amber-400 text-xs px-3 py-1 rounded-full font-bold animate-pulse">Running...</span>;
    return <span className="bg-white/5 text-gray-500 text-xs px-3 py-1 rounded-full font-semibold">Pending</span>;
  };

  const getAgentAvatar = (agentChar, status) => {
    if (status === 'completed') return <div className="w-10 h-10 rounded-lg bg-emerald-500 text-white flex items-center justify-center font-display font-black text-base">✓</div>;
    if (status === 'working') return <div className="w-10 h-10 rounded-lg bg-amber-500 text-black flex items-center justify-center font-display font-black text-base animate-spin">⌛</div>;
    return <div className="w-10 h-10 rounded-lg bg-slate-800 text-gray-500 flex items-center justify-center font-display font-bold text-base">{agentChar}</div>;
  };

  const progressPercent = () => {
    const { researcher, analyst, writer } = taskData.agent_status;
    let percent = 0;
    if (researcher === 'completed') percent += 33;
    if (analyst === 'completed') percent += 33;
    if (writer === 'completed') percent += 34;
    if (percent === 0 && researcher === 'working') percent = 15;
    if (percent === 33 && analyst === 'working') percent = 50;
    if (percent === 66 && writer === 'working') percent = 85;
    return percent;
  };

  const { researcher, analyst, writer } = taskData.agent_status;
  const rec = taskData.writer_data?.recommendation || {};

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col gap-6">
      
      {/* Dashboard Top Header */}
      <div className="bg-brand-card border border-white/5 shadow-2xl rounded-2xl p-6 md:p-8 text-left">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-6">
          <div>
            <h2 className="text-3xl font-black text-white font-display">
              Pipeline: {taskData.ticker}
              {taskData.company_name && (
                <span className="text-gray-400 text-lg font-medium ml-2 font-sans">- {taskData.company_name}</span>
              )}
            </h2>
            <div className="mt-4 w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 to-indigo-600 h-full rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progressPercent()}%` }}
              ></div>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={toggleWatchlist}
              className={`flex items-center justify-center border font-bold py-2.5 px-4 rounded-xl text-sm transition-all cursor-pointer ${
                isSaved
                  ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20'
                  : 'bg-white/4 border-white/5 text-gray-400 hover:text-white hover:bg-white/8'
              }`}
              title={isSaved ? "Remove from Watchlist" : "Add to Watchlist"}
            >
              <span className="text-base mr-1.5 leading-none">{isSaved ? '★' : '☆'}</span>
              Watchlist
            </button>
            <button
              onClick={onReset}
              className="bg-white/4 border border-white/5 hover:bg-white/8 hover:border-gray-400 text-white font-bold py-2.5 px-6 rounded-xl text-sm transition-all cursor-pointer"
            >
              ← Back to Search
            </button>
          </div>
        </div>
      </div>

      {/* AGENT 1: MARKET RESEARCH CARD */}
      <div className={`border rounded-2xl shadow-xl overflow-hidden transition-all duration-500 ${getAgentHeaderStyle(researcher)}`}>
        <div className="p-6 flex items-center justify-between border-b border-white/5">
          <div className="flex items-center gap-4">
            {getAgentAvatar('R', researcher)}
            <div className="text-left">
              <h3 className="text-white font-extrabold text-base md:text-lg font-display">Market Research Agent</h3>
              <p className="text-gray-400 text-xs mt-0.5">Aggregates news feeds and monitors sentiment index</p>
            </div>
          </div>
          {getAgentBadge(researcher)}
        </div>

        {/* Working Logs */}
        {researcher === 'working' && (
          <div className="p-6 bg-slate-950/60 font-mono text-xs text-left text-gray-400 flex flex-col gap-2 max-h-48 overflow-y-auto" ref={logContainerRef}>
            {taskData.messages.filter(m => m.includes('[Researcher]')).map((m, idx) => (
              <div key={idx} className="border-l-2 border-amber-500/50 pl-3 py-1">{m}</div>
            ))}
          </div>
        )}

        {/* Output Area */}
        {researcher === 'completed' && taskData.research_data && (
          <div className="p-6 md:p-8 bg-slate-900/20 text-left border-t border-white/5 animate-fade-in">
            {/* Sentiment Dashboard */}
            {taskData.research_data.news_data?.sentiment && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Overall Sentiment</div>
                  <div className="text-lg font-black text-blue-400 font-display mt-1 uppercase">
                    {taskData.research_data.news_data.sentiment.overall}
                  </div>
                </div>
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Positive Articles</div>
                  <div className="text-lg font-black text-emerald-500 font-display mt-1">
                    {taskData.research_data.news_data.sentiment.positive_count}
                  </div>
                </div>
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Negative Articles</div>
                  <div className="text-lg font-black text-red-500 font-display mt-1">
                    {taskData.research_data.news_data.sentiment.negative_count}
                  </div>
                </div>
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Neutral Articles</div>
                  <div className="text-lg font-black text-amber-500 font-display mt-1">
                    {taskData.research_data.news_data.sentiment.neutral_count}
                  </div>
                </div>
              </div>
            )}

            {/* News Articles */}
            <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Retrieved Market Headings</h4>
            <div className="flex flex-col gap-3">
              {taskData.research_data.news_data?.news?.map((item, idx) => (
                <div key={idx} className="bg-slate-900/30 border border-white/5 rounded-xl overflow-hidden transition-all hover:bg-slate-900/50">
                  <div
                    onClick={() => setActiveNewsIdx(activeNewsIdx === idx ? null : idx)}
                    className="p-4 flex justify-between items-center cursor-pointer select-none gap-4 text-sm"
                  >
                    <span className="font-semibold text-white leading-snug">{item.title}</span>
                    <div className="flex items-center gap-3 text-xs text-gray-500 flex-shrink-0">
                      <strong>{item.source}</strong>
                      {item.date && (
                        <span className="bg-white/5 border border-white/5 text-[10px] text-gray-400 px-2 py-0.5 rounded font-mono">
                          {item.date}
                        </span>
                      )}
                      <svg
                        className={`w-4 h-4 transition-transform duration-300 ${activeNewsIdx === idx ? 'rotate-180 text-blue-400' : ''}`}
                        viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
                      >
                        <polyline points="6 9 12 15 18 9"></polyline>
                      </svg>
                    </div>
                  </div>
                  {activeNewsIdx === idx && (
                    <div className="px-4 pb-4 pt-2 border-t border-white/5 animate-slide-down">
                      <p className="text-xs text-gray-300 leading-relaxed mb-3">{item.snippet}</p>
                      {item.link && (
                        <a href={item.link} target="_blank" rel="noopener noreferrer" className="inline-block bg-white/5 hover:bg-white/10 text-white font-bold text-[10px] px-3.5 py-1.5 rounded-lg transition-all border border-white/5 cursor-pointer">
                          Read Original ↗
                        </a>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* AGENT 2: FINANCIAL ANALYSIS CARD */}
      <div className={`border rounded-2xl shadow-xl overflow-hidden transition-all duration-500 ${getAgentHeaderStyle(analyst)}`}>
        <div className="p-6 flex items-center justify-between border-b border-white/5">
          <div className="flex items-center gap-4">
            {getAgentAvatar('A', analyst)}
            <div className="text-left">
              <h3 className="text-white font-extrabold text-base md:text-lg font-display">Financial Analysis Agent</h3>
              <p className="text-gray-400 text-xs mt-0.5">Fetches fundamental indices and graphs technical trends</p>
            </div>
          </div>
          {getAgentBadge(analyst)}
        </div>

        {/* Working Logs */}
        {analyst === 'working' && (
          <div className="p-6 bg-slate-950/60 font-mono text-xs text-left text-gray-400 flex flex-col gap-2 max-h-48 overflow-y-auto" ref={logContainerRef}>
            {taskData.messages.filter(m => m.includes('[Analyst]')).map((m, idx) => (
              <div key={idx} className="border-l-2 border-amber-500/50 pl-3 py-1">{m}</div>
            ))}
          </div>
        )}

        {/* Output Area */}
        {analyst === 'completed' && taskData.analysis_data && (
          <div className="p-6 md:p-8 bg-slate-900/20 text-left border-t border-white/5 animate-fade-in">
            {/* Ratios Dashboard */}
            {taskData.analysis_data.financial_data && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">P/E Ratio</div>
                  <div className="text-lg font-black text-white font-display mt-1">
                    {taskData.analysis_data.financial_data.pe_ratio ? parseFloat(taskData.analysis_data.financial_data.pe_ratio).toFixed(2) : 'N/A'}
                  </div>
                </div>
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">52w High</div>
                  <div className="text-lg font-black text-emerald-400 font-display mt-1">
                    ${parseFloat(taskData.analysis_data.financial_data.high_52w || 0).toFixed(2)}
                  </div>
                </div>
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Beta (Volatility)</div>
                  <div className="text-lg font-black text-white font-display mt-1">
                    {taskData.analysis_data.financial_data.beta ? parseFloat(taskData.analysis_data.financial_data.beta).toFixed(2) : 'N/A'}
                  </div>
                </div>
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Market Capitalization</div>
                  <div className="text-lg font-black text-white font-display mt-1">
                    {formatMarketCap(taskData.analysis_data.financial_data.market_cap)}
                  </div>
                </div>
              </div>
            )}

            {/* Financial Glossary / Dictionary */}
            <div className="mt-5 border-t border-white/5 pt-5 text-left">
              <details className="group border border-white/5 rounded-xl bg-white/[0.01] overflow-hidden transition-all duration-300">
                <summary className="p-4 flex items-center justify-between text-xs font-bold text-indigo-300 uppercase tracking-widest cursor-pointer hover:bg-white/[0.02] select-none">
                  <span className="flex items-center gap-2">💡 Glossary: Key Terms Explained</span>
                  <span className="text-[10px] text-gray-500 group-open:rotate-180 transition-transform duration-300">▼</span>
                </summary>
                <div className="p-5 border-t border-white/5 bg-slate-950/20 grid grid-cols-1 md:grid-cols-2 gap-5 text-xs text-gray-400 leading-relaxed font-sans">
                  <div className="flex flex-col gap-1">
                    <strong className="text-white font-display text-[11px] uppercase tracking-wider text-purple-400">P/E Ratio (Price-to-Earnings)</strong>
                    <p>
                      Measures the stock price relative to its earnings per share. A high P/E suggests high growth expectations or overvaluation, while a negative P/E indicates the company is reporting net losses.
                    </p>
                  </div>
                  <div className="flex flex-col gap-1">
                    <strong className="text-white font-display text-[11px] uppercase tracking-wider text-purple-400">Beta (Volatility vs. Market)</strong>
                    <p>
                      Measures volatility relative to the overall market (baseline is 1.0). A Beta of 1.5 rises/falls 1.5x as much as the market. A negative Beta (e.g. -0.27) moves in the opposite direction.
                    </p>
                  </div>
                  <div className="flex flex-col gap-1">
                    <strong className="text-white font-display text-[11px] uppercase tracking-wider text-purple-400">Market Capitalization</strong>
                    <p>
                      The total market value of all outstanding shares. It indicates the absolute size of the company (e.g. Large-cap, Mid-cap, or Small-cap) and represents its dollar value.
                    </p>
                  </div>
                  <div className="flex flex-col gap-1">
                    <strong className="text-white font-display text-[11px] uppercase tracking-wider text-purple-400">50-Day & 200-Day Moving Averages (MA)</strong>
                    <p>
                      Technical indicators showing the average closing price over the last 50 and 200 trading days. Prices trading above these averages indicate bullish momentum; trading below indicates a downtrend.
                    </p>
                  </div>
                </div>
              </details>
            </div>

            {/* Charts Visualizations */}
            {taskData.analysis_data.chart_paths && taskData.analysis_data.chart_paths.length > 0 && (
              <div>
                <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-white/5 pb-2">Technical Trend Analysis</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {taskData.analysis_data.chart_paths[0] && (
                    <div className="bg-slate-950/50 border border-white/5 rounded-xl p-4">
                      <div className="relative group cursor-zoom-in overflow-hidden rounded-lg border border-white/5 mb-3">
                        <img
                          src={getAbsoluteUrl(taskData.analysis_data.chart_paths[0])}
                          alt="Price SMA Chart"
                          onClick={() => setZoomChartUrl(getAbsoluteUrl(taskData.analysis_data.chart_paths[0]))}
                          className="w-full object-contain bg-slate-950 max-h-72 transition-transform duration-300 group-hover:scale-[1.02]"
                        />
                        <div 
                          onClick={() => setZoomChartUrl(getAbsoluteUrl(taskData.analysis_data.chart_paths[0]))}
                          className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-355 flex items-center justify-center pointer-events-auto"
                        >
                          <span className="bg-slate-900/90 text-white border border-white/10 px-3.5 py-1.5 rounded-lg text-xs font-bold font-display shadow-xl flex items-center gap-1.5 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
                            🔍 Zoom Chart
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-gray-400 leading-relaxed">
                        <strong className="text-white">Price & Simple Moving Averages:</strong> Traces simple moving averages (50 and 200 days) to flag support lines and trend crossovers.
                      </p>
                    </div>
                  )}
                  {taskData.analysis_data.chart_paths[1] && (
                    <div className="bg-slate-950/50 border border-white/5 rounded-xl p-4">
                      <div className="relative group cursor-zoom-in overflow-hidden rounded-lg border border-white/5 mb-3">
                        <img
                          src={getAbsoluteUrl(taskData.analysis_data.chart_paths[1])}
                          alt="Volume Chart"
                          onClick={() => setZoomChartUrl(getAbsoluteUrl(taskData.analysis_data.chart_paths[1]))}
                          className="w-full object-contain bg-slate-950 max-h-72 transition-transform duration-300 group-hover:scale-[1.02]"
                        />
                        <div 
                          onClick={() => setZoomChartUrl(getAbsoluteUrl(taskData.analysis_data.chart_paths[1]))}
                          className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-355 flex items-center justify-center pointer-events-auto"
                        >
                          <span className="bg-slate-900/90 text-white border border-white/10 px-3.5 py-1.5 rounded-lg text-xs font-bold font-display shadow-xl flex items-center gap-1.5 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
                            🔍 Zoom Chart
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-gray-400 leading-relaxed">
                        <strong className="text-white">Trading Volume:</strong> Captures volume spikes that help qualify the strength behind price breakouts.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* AGENT 3: INVESTMENT DOSSIER CARD */}
      <div className={`border rounded-2xl shadow-xl overflow-hidden transition-all duration-500 ${getAgentHeaderStyle(writer)}`}>
        <div className="p-6 flex items-center justify-between border-b border-white/5">
          <div className="flex items-center gap-4">
            {getAgentAvatar('W', writer)}
            <div className="text-left">
              <h3 className="text-white font-extrabold text-base md:text-lg font-display">Reporting Agent</h3>
              <p className="text-gray-400 text-xs mt-0.5">Synthesizes reports and compiles PDF investment files</p>
            </div>
          </div>
          {getAgentBadge(writer)}
        </div>

        {/* Working Logs */}
        {writer === 'working' && (
          <div className="p-6 bg-slate-950/60 font-mono text-xs text-left text-gray-400 flex flex-col gap-2 max-h-48 overflow-y-auto" ref={logContainerRef}>
            {taskData.messages.filter(m => m.includes('[Writer]') || m.includes('[System]')).map((m, idx) => (
              <div key={idx} className="border-l-2 border-amber-500/50 pl-3 py-1">{m}</div>
            ))}
          </div>
        )}

        {/* Output Area */}
        {writer === 'completed' && taskData.writer_data && (
          <div className="p-6 md:p-8 bg-slate-900/20 text-left border-t border-white/5 animate-fade-in">
            
            {/* 1. Executive Ratings Header Bar */}
            <div className="flex flex-col md:flex-row items-stretch md:items-center gap-6 border border-indigo-500/25 bg-indigo-950/10 rounded-xl p-5 mb-6">
              <div className={`text-xl font-black px-6 py-4 rounded-lg text-center tracking-tight shadow-md select-none bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-blue-500/25 font-display flex flex-col justify-center`}>
                <span className="text-[10px] uppercase font-bold tracking-wider opacity-60">Rating</span>
                <span className="text-2xl mt-0.5 leading-none">{rec.rating || 'HOLD'}</span>
              </div>
              <div className="flex-grow flex flex-col justify-center">
                <h4 className="text-white font-extrabold text-sm mb-1 font-display">Executive Investment Recommendation</h4>
                <p className="text-gray-300 leading-relaxed text-xs">{rec.summary}</p>
              </div>
              <div className="flex flex-wrap gap-2 justify-end self-center">
                {taskData.writer_data.pdf_path && (
                  <a
                    href={getAbsoluteUrl(taskData.writer_data.pdf_path)}
                    download
                    className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white font-bold text-xs px-4 py-2.5 rounded-lg transition-all shadow-md shadow-red-500/10 cursor-pointer animate-pulse-glow"
                  >
                    PDF Dossier
                  </a>
                )}
                <a
                  href={`${API_BASE}/api/download/txt/${taskId}`}
                  download
                  className="bg-white/5 hover:bg-white/10 border border-white/5 text-white font-bold text-xs px-4 py-2.5 rounded-lg transition-all cursor-pointer"
                >
                  TXT Brief
                </a>
                <a
                  href={`${API_BASE}/api/download/csv/${taskId}`}
                  download
                  className="bg-white/5 hover:bg-white/10 border border-white/5 text-white font-bold text-xs px-4 py-2.5 rounded-lg transition-all cursor-pointer"
                >
                  CSV Financials
                </a>
              </div>
            </div>

            {/* 2. Target Price/Confidence Info Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Target price</div>
                <div className="text-lg font-black text-white font-display mt-0.5">
                  {rec.target_price ? `$${parseFloat(rec.target_price).toFixed(2)}` : 'N/A'}
                </div>
              </div>
              <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Confidence</div>
                <div className="text-lg font-black text-indigo-400 font-display mt-0.5">{rec.confidence || 'Medium'}</div>
              </div>
              <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 text-center">
                <div className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Horizon</div>
                <div className="text-lg font-black text-indigo-400 font-display mt-0.5">{rec.time_horizon || 'Medium'}</div>
              </div>
            </div>

            {/* 3. Interactive Report Navigation */}
            <div className="flex bg-slate-950/40 border border-white/5 rounded-lg p-1 gap-1 mb-6">
              {[
                { id: 'thesis', label: 'Thesis & Summary' },
                { id: 'scenarios', label: 'Scenario Analysis' },
                { id: 'catalysts', label: 'Catalysts & Risks' },
                { id: 'full', label: 'Raw Briefing Report' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setReportTab(tab.id)}
                  className={`flex-grow py-2 px-4 rounded-md text-xs font-bold font-display transition-all cursor-pointer text-center ${
                    reportTab === tab.id
                      ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/20 shadow-inner font-extrabold'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* 4. Interactive Report Content Panels */}
            <div className="animate-fade-in min-h-[220px]">
              
              {/* PANEL: THESIS & SUMMARY */}
              {reportTab === 'thesis' && (
                <div className="flex flex-col gap-6 animate-fade-in">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white/[0.01] border border-white/5 rounded-xl p-5 text-left">
                      <h4 className="text-xs font-extrabold text-blue-400 uppercase tracking-wider mb-2 font-display">Executive Brief</h4>
                      <div className="text-xs text-gray-300 leading-relaxed font-sans prose prose-sm prose-invert" dangerouslySetInnerHTML={{ __html: marked.parse(taskData.writer_data.executive_summary || taskData.writer_data.report_summary || "") }} />
                    </div>
                    <div className="bg-white/[0.01] border border-white/5 rounded-xl p-5 text-left">
                      <h4 className="text-xs font-extrabold text-indigo-400 uppercase tracking-wider mb-2 font-display">Investment Core Thesis</h4>
                      <div className="text-xs text-gray-300 leading-relaxed font-sans prose prose-sm prose-invert" dangerouslySetInnerHTML={{ __html: marked.parse(taskData.writer_data.investment_thesis || "") }} />
                    </div>
                  </div>
                  
                  {/* Bulleted Findings */}
                  <div className="bg-white/[0.01] border border-white/5 rounded-xl p-5 text-left">
                    <h4 className="text-xs font-extrabold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-1.5 font-display">
                      <span>✓</span> Primary Findings Summary
                    </h4>
                    <ul className="flex flex-col gap-2">
                      {taskData.writer_data.key_findings?.map((f, i) => (
                        <li 
                          key={i} 
                          className="text-xs text-gray-300 leading-relaxed relative pl-4 before:content-['•'] before:absolute before:left-0 before:text-emerald-500"
                          dangerouslySetInnerHTML={{ __html: marked.parseInline(f) }}
                        />
                      )) || <li className="text-gray-500 text-xs italic">No findings available.</li>}
                    </ul>
                  </div>
                </div>
              )}

              {/* PANEL: SCENARIO ANALYSIS */}
              {reportTab === 'scenarios' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
                  <div className="bg-emerald-950/5 border border-emerald-500/15 rounded-xl p-5 text-left hover:border-emerald-500/30 transition-all duration-300">
                    <h4 className="text-xs font-extrabold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2 font-display">
                      <span className="text-base font-black">📈</span> Bull Case Scenario (Upside Driver)
                    </h4>
                    {Array.isArray(taskData.writer_data.bull_case) ? (
                      <ul className="flex flex-col gap-2">
                        {taskData.writer_data.bull_case.map((f, i) => (
                          <li 
                            key={i} 
                            className="text-xs text-gray-300 leading-relaxed relative pl-4 before:content-['•'] before:absolute before:left-0 before:text-emerald-500"
                            dangerouslySetInnerHTML={{ __html: marked.parseInline(f) }}
                          />
                        ))}
                      </ul>
                    ) : (
                      <div className="text-xs text-gray-300 leading-relaxed font-sans prose prose-sm prose-invert" dangerouslySetInnerHTML={{ __html: marked.parse(taskData.writer_data.bull_case || "") }} />
                    )}
                  </div>
                  <div className="bg-rose-950/5 border border-rose-500/15 rounded-xl p-5 text-left hover:border-rose-500/30 transition-all duration-300">
                    <h4 className="text-xs font-extrabold text-red-400 uppercase tracking-wider mb-3 flex items-center gap-2 font-display">
                      <span className="text-base font-black">📉</span> Bear Case Scenario (Downside Risk)
                    </h4>
                    {Array.isArray(taskData.writer_data.bear_case) ? (
                      <ul className="flex flex-col gap-2">
                        {taskData.writer_data.bear_case.map((f, i) => (
                          <li 
                            key={i} 
                            className="text-xs text-gray-300 leading-relaxed relative pl-4 before:content-['•'] before:absolute before:left-0 before:text-red-500"
                            dangerouslySetInnerHTML={{ __html: marked.parseInline(f) }}
                          />
                        ))}
                      </ul>
                    ) : (
                      <div className="text-xs text-gray-300 leading-relaxed font-sans prose prose-sm prose-invert" dangerouslySetInnerHTML={{ __html: marked.parse(taskData.writer_data.bear_case || "") }} />
                    )}
                  </div>
                </div>
              )}

              {/* PANEL: CATALYSTS & RISKS */}
              {reportTab === 'catalysts' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
                  <div className="bg-white/[0.01] border border-white/5 rounded-xl p-5 text-left">
                    <h4 className="text-xs font-extrabold text-indigo-400 uppercase tracking-wider mb-3 flex items-center gap-2 font-display">
                      <span>✦</span> Future Drivers & Catalysts
                    </h4>
                    <ul className="flex flex-col gap-2">
                      {taskData.writer_data.catalysts?.map((f, i) => (
                        <li 
                          key={i} 
                          className="text-xs text-gray-300 leading-relaxed relative pl-4 before:content-['•'] before:absolute before:left-0 before:text-indigo-500"
                          dangerouslySetInnerHTML={{ __html: marked.parseInline(f) }}
                        />
                      )) || (
                        <div className="text-xs text-gray-400 leading-relaxed font-sans" dangerouslySetInnerHTML={{ __html: marked.parse(taskData.writer_data.catalysts || "No catalysts specified.") }} />
                      )}
                    </ul>
                  </div>
                  <div className="bg-white/[0.01] border border-white/5 rounded-xl p-5 text-left">
                    <h4 className="text-xs font-extrabold text-red-400 uppercase tracking-wider mb-3 flex items-center gap-2 font-display">
                      <span>⚠</span> Risk Factors
                    </h4>
                    <ul className="flex flex-col gap-2">
                      {taskData.writer_data.risk_factors?.map((f, i) => (
                        <li 
                          key={i} 
                          className="text-xs text-gray-300 leading-relaxed relative pl-4 before:content-['•'] before:absolute before:left-0 before:text-red-500"
                          dangerouslySetInnerHTML={{ __html: marked.parseInline(f) }}
                        />
                      )) || <li className="text-gray-500 text-xs italic">No risk factors available.</li>}
                    </ul>
                  </div>
                </div>
              )}

              {/* PANEL: RAW DOSSIER */}
              {reportTab === 'full' && (
                <div className="bg-slate-950/40 border border-white/5 rounded-xl p-6 overflow-y-auto max-h-[450px] text-left animate-fade-in font-sans prose prose-invert max-w-none prose-sm prose-headings:font-display prose-headings:text-white prose-a:text-blue-400">
                  <div dangerouslySetInnerHTML={{ __html: marked.parse(taskData.writer_data.full_report || "") }} />
                </div>
              )}
            </div>

          </div>
        )}
      </div>

      {/* Raw JSON Inspections */}
      {taskData.status === 'completed' && (
        <div className="bg-brand-card border border-white/5 rounded-2xl p-6 text-left mb-6">
          <div
            onClick={() => setJsonExpanded(!jsonExpanded)}
            className="flex justify-between items-center cursor-pointer select-none"
          >
            <h4 className="text-xs font-bold uppercase tracking-wider text-purple-400">Inspect Consolidated Pipeline Data JSON</h4>
            <svg
              className={`w-4 h-4 transition-transform duration-300 ${jsonExpanded ? 'rotate-180 text-blue-400' : ''}`}
              viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
            >
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>
          {jsonExpanded && (
            <div className="mt-4 bg-[#030712] border border-white/5 rounded-xl p-4 overflow-x-auto max-h-[300px]">
              <pre className="font-mono text-[10px] text-blue-400 leading-relaxed">
                {JSON.stringify({
                  ticker: taskData.ticker,
                  company_name: taskData.company_name,
                  research_data: taskData.research_data,
                  analysis_data: taskData.analysis_data,
                  writer_data: taskData.writer_data
                }, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Lightbox Modal for Chart Zoom */}
      {zoomChartUrl && (
        <div
          onClick={() => setZoomChartUrl(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4 animate-fade-in"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="relative max-w-5xl w-full bg-[#0d1321]/95 border border-white/10 rounded-2xl p-6 md:p-8 flex flex-col items-center shadow-2xl animate-scale-in text-center"
          >
            <button
              onClick={() => setZoomChartUrl(null)}
              className="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/5 border border-white/10 text-gray-400 hover:text-white flex items-center justify-center font-bold text-sm transition-all hover:bg-white/10 cursor-pointer"
            >
              ✕
            </button>
            <img
              src={zoomChartUrl}
              alt="Chart Zoomed"
              className="max-w-full max-h-[72vh] object-contain rounded-lg border border-white/5 bg-slate-950"
            />
            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mt-4">
              Click outside or press ✕ to close preview
            </p>
          </div>
        </div>
      )}

    </div>
  );
}
