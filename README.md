# Finlyze: Multi-Agent Stock Analysis Platform

Finlyze is an advanced, institutional-grade stock analysis dashboard that orchestrates specialized AI agents to conduct news research, sentiment indexing, fundamental valuation, technical charting, and investment dossier compilation.

The project is structured as a decoupled application with a **Flask API Backend** and a modern **React JS Frontend**.

---

## Architecture Overview

```
finlyze/
├── backend/                  # Flask REST API & Agent Workflow
│   ├── agents/               # AI Agents (Researcher, Analyst, Writer)
│   ├── tools/                # Financial and News scrapers/charting
│   ├── utils/                # Formatting and SQLite database helpers
│   ├── data/                 # SQLite database storage (finlyze.db)
│   ├── output/               # Generated reports (PDFs, charts)
│   ├── .env                  # Configuration variables
│   ├── requirements.txt      # Python dependencies
│   ├── app.py                # Server routes & configurations
│   └── run.py                # Dedicated server execution entry point
│
└── frontend/                 # React (Vite) Single Page Application
    ├── src/
    │   ├── components/       # UI Components (Search, Dashboard, Compare)
    │   ├── App.jsx           # App state & layout wrapper
    │   └── index.css         # Styling system & animations
    ├── index.html            # Web template
    ├── .env.example          # Environment variable template
    └── package.json          # Node dependencies
```

---

## Key Features

1. **Multi-Agent Orchestration:**
   * **Market Research Agent:** Scrapes real-time market headings, checks sentiment keyword weights, and runs news aggregators.
   * **Financial Analysis Agent:** Queries financial metrics, computes 50-day and 200-day Simple Moving Averages, and plots price and volume trends.
   * **Reporting Agent:** Synthesizes analysis data into executive recommendations (BUY/HOLD/SELL), bull/bear case scenarios, and publishes PDF, TXT, and CSV formats.
2. **Server-Side Watchlist & History:**
   * **Watchlist Manager:** Add/remove stocks from a persistent list directly from the report view using the Star toggle.
   * **Analysis History Log:** Re-load previous analyses instantly from a history list. Tasks are cached locally in SQLite and recovered dynamically even if the backend server restarts.
3. **Side-by-Side Stock Comparison:** Compare key financial metrics (P/E ratio, Market Cap, Beta, Volume, etc.) for two tickers in a comparative table.
4. **Premium Dark Dashboard:** Fully customized user interface using Tailwind CSS v4.0 with Outfit and Plus Jakarta typography, glow animations, and glassmorphic card elements.
5. **Interactive Chart Zoom:** Clicking any generated price or volume chart opens a full-screen spring-bounce lightbox modal to inspect moving averages and volume breakouts.
6. **Collapsible Financial Glossary:** An on-page accordion helper explaining financial jargon (P/E Ratio, Beta, Market Cap, Moving Averages) to assist users.

---

## Local Installation & Setup

### 1. Prerequisites
* Python 3.10 or higher
* Node.js 18.0 or higher
* A Gemini API Key

---

### 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on `.env.example` and set your variables:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash
   ```
5. Run the Flask server:
   ```bash
   python run.py
   ```
   *The server runs locally at `http://localhost:5000`.*

---

### 3. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   *Access the web interface in your browser at `http://localhost:5173`.*

---

## Production Deployment (Vercel + Render)

Finlyze is designed with dual-environment support to be easily deployable in production.

### 1. Backend Deployment (Render Web Service)
* **Root Directory:** `backend`
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `python run.py`
* **Environment Variables:**
  * `GEMINI_API_KEY`: Your Gemini API key
  * `GEMINI_MODEL`: `gemini-2.0-flash`

### 2. Frontend Deployment (Vercel)
* **Root Directory:** `frontend`
* **Framework Preset:** `Vite`
* **Build Command:** `npm run build`
* **Output Directory:** `dist`
* **Environment Variables:**
  * `VITE_API_BASE`: `https://your-backend-api.onrender.com` (Your Render deployment URL without a trailing slash)

---

## Core Technologies
* **Frontend:** React JS, Vite, Tailwind CSS v4.0, Marked (Markdown compiler)
* **Backend:** Flask, SQLite3, LangChain, Google Gemini API, YFinance, DuckDuckGo Search API, Matplotlib
