// frontend/src/App.jsx
import React, { useState } from 'react';
import SearchPage from './components/SearchPage';
import AnalysisDashboard from './components/AnalysisDashboard';
import ComparePage from './components/ComparePage';

export default function App() {
  const [activePage, setActivePage] = useState('search'); // 'search' | 'dashboard' | 'compare'
  const [taskId, setTaskId] = useState('');
  const [ticker, setTicker] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [compareTickers, setCompareTickers] = useState({ ticker1: '', ticker2: '' });

  const handleStartAnalysis = (searchTicker, searchCompanyName) => {
    setTicker(searchTicker);
    setCompanyName(searchCompanyName);
    setTaskId('');
    setActivePage('dashboard');
  };

  const handleLoadHistory = (historyTaskId, historyTicker, historyCompanyName) => {
    setTaskId(historyTaskId);
    setTicker(historyTicker);
    setCompanyName(historyCompanyName || '');
    setActivePage('dashboard');
  };

  const handleStartComparison = (t1, t2) => {
    setCompareTickers({ ticker1: t1, ticker2: t2 });
    setActivePage('compare');
  };

  const handleReset = () => {
    setTaskId('');
    setTicker('');
    setCompanyName('');
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
            initialTaskId={taskId}
            ticker={ticker}
            companyName={companyName}
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
