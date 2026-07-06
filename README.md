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
│   ├── utils/                # Formatting and data encoders
│   ├── output/               # Generated reports (PDFs, charts)
│   ├── .env                  # Configuration variables
│   ├── requirements.txt      # Python dependencies
│   └── app.py                # Server entry point
│
└── frontend/                 # React (Vite) Single Page Application
    ├── src/
    │   ├── components/       # UI Components (Search, Dashboard)
    │   ├── App.jsx           # App state & layout wrapper
    │   └── index.css         # Styling system & animations
    ├── index.html            # Web template
    └── package.json          # Node dependencies
```

---

## Key Features

1. **Multi-Agent Orchestration:**
   * **Market Research Agent:** Scrapes real-time market headings, checks sentiment keyword weights, and runs news aggregators.
   * **Financial Analysis Agent:** Queries financial metrics, computes 50-day and 200-day Simple Moving Averages, and plots price and volume trends.
   * **Reporting Agent:** Synthesizes analysis data into executive recommendations (BUY/HOLD/SELL), bull/bear case scenarios, and publishes PDF, TXT, and CSV formats.
2. **Premium Dark Dashboard:** Fully customized user interface using Tailwind CSS v4.0 with Outfit and Plus Jakarta typography, glow animations, and glassmorphic card elements.
3. **Interactive Chart Zoom:** Clicking any generated price or volume chart opens a full-screen spring-bounce lightbox modal to inspect moving averages and volume breakouts.
4. **collapsible Financial Glossary:** An on-page accordion helper explaining financial jargon (P/E Ratio, Beta, Market Cap, Moving Averages) to assist users.
5. **Robust Data Fallbacks:** Integrated standard web-text search fallbacks if search engine news endpoints are blocked or rate-limited.
6. **Smart Ticker Cleaning:** Automatically strips exchange prefixes/suffixes (e.g. `NASDAQ- Meta` or `NASDAQ:META` resolves directly to `META`).

---

## Installation & Setup

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
   GEMINI_MODEL=gemini-2.5-flash
   ```
5. Run the Flask server:
   ```bash
   python app.py
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

## Core Technologies
* **Frontend:** React JS, Vite, Tailwind CSS v4.0, Marked (Markdown compiler)
* **Backend:** Flask, LangChain, Google Gemini API, YFinance, DuckDuckGo Search API, Matplotlib
