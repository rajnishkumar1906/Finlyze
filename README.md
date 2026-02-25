# Finlyze 📊🤖

**AI-Powered Multi-Agent Stock Analysis Platform**
# Agent path ->https://finlyze.onrender.com/


[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38%2B-red)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0%2B-green)](https://langchain.ai)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-orange)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
---

## 🎯 **One-Liner Description**

Finlyze is an AI-powered multi-agent platform that analyzes any stock ticker using three specialized agents - Researcher, Analyst, and Writer - to deliver comprehensive investment reports with real-time data, sentiment analysis, and PDF downloads.

---

## ✨ **Features**

### 🤖 **Three Specialized AI Agents**
| Agent | Role | Tools Used |
|-------|------|------------|
| **Researcher** | News gathering & sentiment analysis | DuckDuckGo Search |
| **Analyst** | Financial data & chart generation | yfinance, Matplotlib |
| **Writer** | Report synthesis & PDF creation | Gemini AI, fpdf2 |

### 📊 **Key Capabilities**
- **Real-time stock data** - Prices, fundamentals, ratios from Yahoo Finance
- **Live news aggregation** - Latest headlines with sentiment scoring
- **Professional charts** - Price trends with 50/200-day moving averages
- **Sentiment analysis** - Positive/negative/neutral classification
- **PDF reports** - Downloadable professional reports with embedded charts
- **Multi-format export** - PDF, TXT, Markdown, CSV downloads

### 🎨 **User Experience**
- Clean, modern Streamlit interface
- Real-time agent status tracking
- Tabbed results view (Summary, News, Financials, Data, Report)
- Persistent expanders (stay open after downloads)
- Mobile-responsive design

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                      USER INPUT                          │
│                    (Stock Ticker)                        │
└─────────────────────────┬───────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  LANGGRAPH WORKFLOW                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ RESEARCHER  │───▶│   ANALYST   │───▶│   WRITER    │  │
│  │   Agent     │    │   Agent     │    │   Agent     │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│       │                  │                   │           │
│       ▼                  ▼                   ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  DuckDuckGo │    │  yfinance   │    │   Gemini    │  │
│  │    News     │    │    Data     │    │     AI      │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│                            │                   │         │
│                            ▼                   ▼         │
│                       ┌─────────────┐    ┌─────────────┐ │
│                       │  Matplotlib │    │    fpdf2    │ │
│                       │   Charts    │    │     PDF     │ │
│                       └─────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   STREAMLIT UI                           │
│              (Tabs: Summary, News, Financials,           │
│                     Data Export, Report)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ **Tech Stack**

| Category | Technology | Purpose |
|----------|------------|---------|
| **Frontend** | Streamlit | Web interface |
| **Orchestration** | LangGraph | Agent workflow management |
| **AI/LLM** | Google Gemini | Intelligence & report writing |
| **Stock Data** | yfinance | Real-time financial data |
| **News Data** | duckduckgo-search | Live news aggregation |
| **Charts** | Matplotlib, Pandas | Data visualization |
| **PDF Generation** | fpdf2 | Professional report creation |
| **Data Processing** | Pandas, NumPy | Financial calculations |
| **Environment** | python-dotenv | API key management |

---

## 📁 **Project Structure**

```
finlyze/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (API keys)
├── .env.example          # Template for environment variables
├── prompts.py            # LLM prompt templates
│
├── agents/               # AI Agents
│   ├── researcher.py     # News & sentiment agent
│   ├── analyst.py        # Financial analysis agent
│   └── writer.py         # Report generation agent
│
├── graph/                # LangGraph workflow
│   └── workflow.py       # State graph & node definitions
│
├── tools/                # Utility tools
│   ├── news_tools.py     # DuckDuckGo news search
│   ├── finance_tools.py  # yfinance data fetching
│   └── report_tools.py   # PDF generation
│
├── utils/                # Helper functions
│   └── helpers.py        # Formatting, directories, etc.
│
└── output/               # Generated reports & charts
    └── .gitkeep
```

---

## 🚀 **Installation & Setup**

### **Prerequisites**
- Python 3.8 or higher
- Google Gemini API key (get it [here](https://makersuite.google.com/app/apikey))

### **Step 1: Clone the Repository**
```bash
git clone https://github.com/yourusername/finlyze.git
cd finlyze
```

### **Step 2: Create Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 4: Set Up Environment Variables**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your-actual-api-key-here
```

### **Step 5: Run the Application**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📊 **Usage Guide**

### **Quick Start**
1. Enter a stock ticker (e.g., `AAPL`, `MSFT`, `TSLA`, `RELIANCE.NS`)
2. (Optional) Add company name for better news search
3. Click **"Analyze Stock"**
4. Watch the three agents work in sequence
5. Explore results in the tabs

### **Navigation Tabs**
| Tab | Content |
|-----|---------|
| **Summary** | Executive summary, recommendation, key findings, risks |
| **News** | Sentiment metrics, recent headlines with expandable details |
| **Financials** | Key metrics, price/volume charts, detailed financial data |
| **Data Export** | CSV download of all financial metrics |
| **Report** | Full text report with PDF, TXT, Markdown downloads |

### **Sample Tickers to Try**
| Ticker | Company | Why Test |
|--------|---------|----------|
| `AAPL` | Apple Inc. | Most reliable, balanced news |
| `TSLA` | Tesla Inc. | High volatility, lots of news |
| `MSFT` | Microsoft | Strong fundamentals |
| `RELIANCE.NS` | Reliance Industries | Indian market test |
| `TCS.NS` | Tata Consultancy | Another Indian stock |

---

## 🔍 **How It Works - Step by Step**

### **Step 1: Researcher Agent 🔍**
- Searches DuckDuckGo for latest news about the ticker
- Analyzes sentiment (positive/negative/neutral)
- Extracts key developments and risks
- **Output:** News articles with sentiment scores

### **Step 2: Analyst Agent 📊**
- Fetches real-time data from Yahoo Finance
- Calculates key metrics (P/E, EPS, Market Cap, etc.)
- Generates price charts with 50/200-day moving averages
- Creates volume charts
- **Output:** Financial metrics + PNG charts

### **Step 3: Writer Agent ✍️**
- Synthesizes research and analysis
- Generates BUY/HOLD/SELL recommendation with confidence
- Creates comprehensive investment thesis
- Produces PDF report with embedded charts
- **Output:** Text report + downloadable PDF

---
<!-- 
## 💡 **Why This Project Stands Out** -->

### **For Recruiters**
### **Production-Grade Agentic AI** - Demonstrates expertise in multi-agent systems with LangGraph
### **Full-Stack Development** - Covers frontend (Streamlit), backend (Python), and AI integration
### **Real-World Application** - Solves actual investment research problems
### **Robust Error Handling** - Graceful degradation when data is unavailable
### **State Management** - Persistent UI state across interactions
### **Modular Design** - Easy to extend with new features

### **Technical Achievements**
- Complex state management across multiple agents
- Real-time UI updates during agent execution
- Integration of multiple data sources (Yahoo Finance, DuckDuckGo)
- Professional report generation with embedded graphics
- Persistent expander states across re-renders

---

## 🔧 **Configuration**

### **Environment Variables**
```env
GEMINI_API_KEY=your-gemini-api-key-here
```

### **Customizing Search Parameters**
In `tools/news_tools.py`, you can adjust:
```python
timelimit="7d"  # Change to "d" (day), "w" (week), "m" (month), "y" (year)
max_results=10  # Number of news articles to fetch
```

### **Adjusting Chart Periods**
In `tools/finance_tools.py`:
```python
period="6mo"  # Change to "1mo", "3mo", "1y", "5y", "max"
```

---

## 🚀 **Deployment**

### **Deploy on Render.com**
1. Push code to GitHub
2. Create new Web Service on Render
3. Connect your repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `streamlit run app.py --server.port $PORT`
6. Add environment variable: `GEMINI_API_KEY`
7. Deploy!


---

## 🙏 **Acknowledgments**

- [LangChain](https://langchain.ai) for the amazing agent framework
- [Google Gemini](https://deepmind.google/technologies/gemini/) for the AI capabilities
- [Streamlit](https://streamlit.io) for the incredible UI framework
- [Yahoo Finance](https://finance.yahoo.com) for the financial data
- [DuckDuckGo](https://duckduckgo.com) for the privacy-focused search

---
