// frontend/src/App.jsx
import React, { useState } from 'react';
import SearchPage from './components/SearchPage';
import AnalysisDashboard from './components/AnalysisDashboard';
import ComparePage from './components/ComparePage';

const API_BASE = import.meta.env.VITE_API_BASE || (
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000'
    : window.location.origin
);

export default function App() {
  const [activePage, setActivePage] = useState('search'); // 'search' | 'dashboard' | 'compare'
  const [taskId, setTaskId] = useState('');
  const [ticker, setTicker] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [error, setError] = useState(null);
  const [compareTickers, setCompareTickers] = useState({ ticker1: '', ticker2: '' });

  const handleStartAnalysis = (searchTicker, searchCompanyName) => {
    setTicker(searchTicker);
    setCompanyName(searchCompanyName);
    setActivePage('dashboard');
    setError(null);

    // Call backend API to initiate workflow
    fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ticker: searchTicker,
        company_name: searchCompanyName
      })
    })
      .then(res => {
        if (!res.ok) throw new Error("Failed to initialize analysis pipeline on backend");
        return res.json();
      })
      .then(data => {
        if (data.task_id) {
          setTaskId(data.task_id);
          if (data.company_name) {
            setCompanyName(data.company_name);
          }
        } else {
          throw new Error("No task ID received from backend");
        }
      })
      .catch(err => {
        console.error("Pipeline start error:", err);
        setError(err.message);
        setActivePage('search');
        alert(`Failed to start analysis: ${err.message}`);
      });
  };

  const handleLoadHistory = (historyTaskId, historyTicker, historyCompanyName) => {
    setTaskId(historyTaskId);
    setTicker(historyTicker);
    setCompanyName(historyCompanyName || '');
    setError(null);
    setActivePage('dashboard');
  };

  const handleStartComparison = (t1, t2) => {
    setCompareTickers({ ticker1: t1, ticker2: t2 });
    setActivePage('compare');
    setError(null);
  };

  const handleReset = () => {
    setTaskId('');
    setTicker('');
    setCompanyName('');
    setError(null);
    setCompareTickers({ ticker1: '', ticker2: '' });
    setActivePage('search');
  };

  return (
    <div className="min-h-screen flex flex-col justify-between">
      {/* Top Navbar */}
      <header className="max-w-7xl w-full mx-auto px-6 py-8 flex justify-between items-center z-10">
        <div>
          <h1 className="text-3xl font-black tracking-tight font-display text-gradient cursor-pointer" onClick={handleReset}>
            Finlyze
          </h1>
          <p className="text-xs text-gray-500 font-medium tracking-wide mt-1">
            Multi-Agent Stock Analysis Platform
          </p>
        </div>
      </header>

      {/* Main Page Area */}
      <main className="max-w-7xl w-full mx-auto px-6 flex-grow flex flex-col justify-center pb-12">
        {activePage === 'search' ? (
          <SearchPage 
            onStartAnalysis={handleStartAnalysis} 
            onLoadHistory={handleLoadHistory}
            onStartComparison={handleStartComparison}
          />
        ) : activePage === 'dashboard' ? (
          <AnalysisDashboard
            taskId={taskId}
            ticker={ticker}
            onReset={handleReset}
          />
        ) : (
          <ComparePage
            ticker1={compareTickers.ticker1}
            ticker2={compareTickers.ticker2}
            onReset={handleReset}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="text-center py-6 px-6 border-t border-white/5 bg-brand-dark/80 backdrop-blur-md mt-auto">
        <p className="text-[10px] text-gray-500 leading-relaxed">
          Finlyze is for educational purposes only and does not constitute investment advice.
        </p>
        <p className="text-[10px] text-gray-500 font-medium mt-1">
          © 2026 Finlyze | Advanced Stock Analysis Platform
        </p>
      </footer>
    </div>
  );
}
