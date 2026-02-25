# app.py
import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
import time
import pandas as pd
import zipfile
from io import BytesIO

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    st.error("🚨 CRITICAL ERROR: GEMINI_API_KEY not found in .env file!")
    st.code("""
    Please create a .env file in the root directory with:
    GEMINI_API_KEY=your-gemini-api-key-here
    
    Current working directory: """ + os.getcwd())
    st.stop()

from graph.workflow import FinlyzeWorkflow
from utils.helpers import setup_directories, clean_ticker

# Page configuration
st.set_page_config(
    page_title="Finlyze - AI Stock Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize ALL session state variables at the start
if 'workflow' not in st.session_state:
    st.session_state.workflow = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'api_key_configured' not in st.session_state:
    st.session_state.api_key_configured = bool(os.getenv("GEMINI_API_KEY"))
if 'agent_status' not in st.session_state:
    st.session_state.agent_status = {
        'researcher': 'pending',
        'analyst': 'pending',
        'writer': 'pending'
    }
if 'research_preview' not in st.session_state:
    st.session_state.research_preview = None
if 'analysis_preview' not in st.session_state:
    st.session_state.analysis_preview = None

# Initialize expander states
if 'expander_states' not in st.session_state:
    st.session_state.expander_states = {
        'view_all_metrics': False,         #Stored the metrics used to evaluate the analysis
        'view_raw_json': False,            #News data scrapped from financial news platfomrs like yahoo
        'view_agent_messages': False,      #Agents response message
        'additional_charts': False,
        'view_news_items': {}  # Will store state for each news item
    }

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ECFDF5;
        border-left: 0.5rem solid #10B981;
        margin-bottom: 1rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #EFF6FF;
        border-left: 0.5rem solid #3B82F6;
        margin-bottom: 1rem;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FEF3C7;
        border-left: 0.5rem solid #F59E0B;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F9FAFB;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6B7280;
    }
    .stButton button {
        background-color: #1E3A8A;
        color: white;
        font-weight: 600;
        border-radius: 0.5rem;
        padding: 0.5rem 2rem;
        border: none;
    }
    .stButton button:hover {
        background-color: #2563EB;
    }
    .agent-complete {
        padding: 0.5rem;
        border-radius: 0.5rem;
        background-color: #10B981;
        color: white;
        font-weight: 600;
        text-align: center;
        margin: 0.5rem 0;
    }
    .agent-working {
        padding: 0.5rem;
        border-radius: 0.5rem;
        background-color: #F59E0B;
        color: white;
        font-weight: 600;
        text-align: center;
        margin: 0.5rem 0;
    }
    .data-preview {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E5E7EB;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

setup_directories()

# Sidebar
with st.sidebar:
    st.image("./image.png", width=80)
    st.markdown("## Finlyze Settings")
    
    # Show API status from .env only
    if GEMINI_API_KEY:
        st.success("✅ Gemini API: Connected")
        st.session_state.api_key_configured = True
    else:
        st.error("❌ Gemini API: Not configured")
        st.session_state.api_key_configured = False
        st.info("Please add GEMINI_API_KEY to .env file and restart")
    
    st.markdown("---")
    
    # Agent Status Panel
    st.markdown("### 🤖 Agent Status")
    
    # Researcher status
    if st.session_state.agent_status['researcher'] == 'completed':
        st.markdown("🟢 **Researcher:** ✅ Complete")
    elif st.session_state.agent_status['researcher'] == 'working':
        st.markdown("🟡 **Researcher:** ⏳ Working...")
    else:
        st.markdown("⚪ **Researcher:** ⏳ Pending")
    
    # Analyst status
    if st.session_state.agent_status['analyst'] == 'completed':
        st.markdown("🟢 **Analyst:** ✅ Complete")
    elif st.session_state.agent_status['analyst'] == 'working':
        st.markdown("🟡 **Analyst:** ⏳ Working...")
    else:
        st.markdown("⚪ **Analyst:** ⏳ Pending")
    
    # Writer status
    if st.session_state.agent_status['writer'] == 'completed':
        st.markdown("🟢 **Writer:** ✅ Complete")
    elif st.session_state.agent_status['writer'] == 'working':
        st.markdown("🟡 **Writer:** ⏳ Working...")
    else:
        st.markdown("⚪ **Writer:** ⏳ Pending")
    
    st.markdown("---")
    
    # About section
    st.markdown("### About Finlyze")
    st.markdown("""
    **Finlyze** is an AI-powered stock analysis platform that uses multiple AI agents to:
    
    1. 📰 **Research** latest news and sentiment
    2. 📊 **Analyze** financial data and metrics
    3. ✍️ **Write** professional reports with recommendations
    
    Built with LangGraph, Gemini AI, and Streamlit.
    """)
    
    st.markdown("---")
    st.markdown("© 2026 Finlyze | Not financial advice")

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<p class="main-header">Finlyze</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Multi-Agent Stock Analysis</p>', unsafe_allow_html=True)

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)

# Input section
st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    ticker = st.text_input(
        "Enter Stock Ticker",
        placeholder="e.g., AAPL, MSFT, TSLA, RELIANCE.NS",
        help="Enter the stock ticker symbol (e.g., AAPL for Apple)"
    ).strip().upper()

with col2:
    company_name = st.text_input(
        "Company Name (optional)",
        placeholder="e.g., Apple Inc.",
        help="Optional: Enter company name for better news search"
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_button = st.button("🔍 Analyze Stock", type="primary", width='stretch')

# Reset agent status when new analysis starts
if analyze_button:
    st.session_state.agent_status = {
        'researcher': 'pending',
        'analyst': 'pending',
        'writer': 'pending'
    }
    st.session_state.research_preview = None
    st.session_state.analysis_preview = None

# Main analysis section
if analyze_button and ticker:
    if not GEMINI_API_KEY:
        st.error("⚠️ Gemini API key not configured in .env file")
    else:
        # Clean ticker
        clean_ticker_symbol = clean_ticker(ticker)
        
        # Create progress container
        progress_container = st.container()
        
        with progress_container:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown(f"### 🚀 Starting analysis for {clean_ticker_symbol}")
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Initialize workflow
            if 'workflow' not in st.session_state or st.session_state.workflow is None:
                with st.spinner("Initializing AI agents..."):
                    st.session_state.workflow = FinlyzeWorkflow()
                    time.sleep(1)
            
            # Create placeholders for real-time updates
            researcher_placeholder = st.empty()
            analyst_placeholder = st.empty()
            writer_placeholder = st.empty()
            data_preview_placeholder = st.empty()
            
            # Run workflow
            try:
                # Step 1: Researcher
                status_text.text("Step 1/3: Researching news and sentiment...")
                progress_bar.progress(20)
                st.session_state.agent_status['researcher'] = 'working'
                researcher_placeholder.markdown('<div class="agent-working">🔍 Researcher Agent: Gathering news & sentiment...</div>', unsafe_allow_html=True)
                
                # Run the workflow
                results = st.session_state.workflow.run(clean_ticker_symbol, company_name)
                
                # Update based on results
                messages = results.get('messages', [])
                
                for msg in messages:
                    if "research" in msg.lower() and "complete" in msg.lower():
                        st.session_state.agent_status['researcher'] = 'completed'
                        researcher_placeholder.markdown('<div class="agent-complete">✅ Researcher Agent: News & Sentiment Analysis Complete!</div>', unsafe_allow_html=True)
                        
                        # Show research preview
                        research_data = results.get('research_data', {})
                        news_data = research_data.get('news_data', {})
                        sentiment = news_data.get('sentiment', {})
                        
                        with data_preview_placeholder.container():
                            st.markdown('<div class="data-preview">', unsafe_allow_html=True)
                            st.markdown("### 📰 Research Findings")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("News Articles", len(news_data.get('news', [])))
                            with col2:
                                st.metric("Sentiment", sentiment.get('overall', 'neutral').upper())
                            with col3:
                                pos = sentiment.get('positive_count', 0)
                                neg = sentiment.get('negative_count', 0)
                                st.metric("Pos/Neg", f"{pos}/{neg}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        status_text.text("Step 2/3: Analyzing financial data...")
                        progress_bar.progress(50)
                        
                    elif "analysis" in msg.lower() and "complete" in msg.lower():
                        st.session_state.agent_status['analyst'] = 'completed'
                        analyst_placeholder.markdown('<div class="agent-complete">📊 Analyst Agent: Financial Analysis Complete!</div>', unsafe_allow_html=True)
                        
                        # Show analysis preview
                        analysis_data = results.get('analysis_data', {})
                        financial_data = analysis_data.get('financial_data', {})
                        
                        with data_preview_placeholder.container():
                            st.markdown('<div class="data-preview">', unsafe_allow_html=True)
                            st.markdown("### 📈 Analysis Findings")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                price = financial_data.get('current_price', 0)
                                st.metric("Current Price", f"${price:.2f}" if price else "N/A")
                            with col2:
                                market_cap = financial_data.get('market_cap', 0)
                                if market_cap:
                                    if market_cap >= 1e9:
                                        cap_str = f"${market_cap/1e9:.2f}B"
                                    else:
                                        cap_str = f"${market_cap/1e6:.2f}M"
                                    st.metric("Market Cap", cap_str)
                                else:
                                    st.metric("Market Cap", "N/A")
                            with col3:
                                pe = financial_data.get('pe_ratio')
                                st.metric("P/E Ratio", f"{pe:.2f}" if pe else "N/A")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        status_text.text("Step 3/3: Writing final report...")
                        progress_bar.progress(80)
                        
                    elif "report" in msg.lower() and "complete" in msg.lower():
                        st.session_state.agent_status['writer'] = 'completed'
                        writer_placeholder.markdown('<div class="agent-complete">✍️ Writer Agent: Report Generation Complete!</div>', unsafe_allow_html=True)
                        status_text.text("✅ Analysis complete!")
                        progress_bar.progress(100)
                        
                        # Show final preview
                        writer_data = results.get('writer_data', {})
                        recommendation = writer_data.get('recommendation', {})
                        
                        with data_preview_placeholder.container():
                            st.markdown('<div class="data-preview">', unsafe_allow_html=True)
                            st.markdown("### 📋 Final Recommendation")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Rating", recommendation.get('rating', 'HOLD'))
                            with col2:
                                st.metric("Confidence", recommendation.get('confidence', 'Medium'))
                            with col3:
                                target = recommendation.get('target_price')
                                if target:
                                    st.metric("Target Price", f"${target:.2f}")
                                else:
                                    st.metric("Target Price", "N/A")
                            st.markdown('</div>', unsafe_allow_html=True)
                
                st.session_state.results = results
                
                # ✅ FIXED: Agent Messages Expander with state persistence
                messages_expanded = st.session_state.expander_states.get('view_agent_messages', False)
                view_messages = st.expander("View Agent Messages", expanded=messages_expanded)
                
                with view_messages:
                    for msg in messages:
                        st.markdown(f"- {msg}")
                
                # Save expander state AFTER
                st.session_state.expander_states['view_agent_messages'] = view_messages.expanded
                
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                st.session_state.results = None
        
        # Display full results in tabs if available
        if st.session_state.results and st.session_state.results.get('writer_status') == 'completed':
            results = st.session_state.results
            
            # Create tabs for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Summary", "📰 News", "📈 Financials", "📊 Data Export", "📄 Report"])
            
            with tab1:
                st.markdown("## Executive Summary")
                
                writer_data = results.get('writer_data', {})
                recommendation = writer_data.get('recommendation', {})
                rating = recommendation.get('rating', 'HOLD')
                confidence = recommendation.get('confidence', 'Medium')
                
                # Color code recommendation
                if rating == 'BUY':
                    box_class = 'success-box'
                elif rating == 'SELL':
                    box_class = 'warning-box'
                else:
                    box_class = 'info-box'
                
                st.markdown(f'<div class="{box_class}">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Recommendation", rating)
                with col2:
                    st.metric("Confidence", confidence)
                with col3:
                    target = recommendation.get('target_price')
                    if target:
                        st.metric("Target Price", f"${target:.2f}")
                    else:
                        st.metric("Target Price", "N/A")
                
                st.markdown(f"**Summary:** {recommendation.get('summary', '')}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Key findings
                st.markdown("### Key Findings")
                findings = writer_data.get('key_findings', [])
                for finding in findings:
                    st.markdown(f"- {finding}")
                
                # Risk factors
                st.markdown("### Risk Factors")
                risks = writer_data.get('risk_factors', [])
                for risk in risks:
                    st.markdown(f"- {risk}")
            
            with tab2:
                st.markdown("## News & Sentiment Analysis")
                
                research_data = results.get('research_data', {})
                news_data = research_data.get('news_data', {})
                sentiment = news_data.get('sentiment', {})
                
                # Sentiment metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    overall = sentiment.get('overall', 'neutral').upper()
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<p class="metric-value">{overall}</p>', unsafe_allow_html=True)
                    st.markdown('<p class="metric-label">Overall Sentiment</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    pos = sentiment.get('positive_count', 0)
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<p class="metric-value">{pos}</p>', unsafe_allow_html=True)
                    st.markdown('<p class="metric-label">Positive Articles</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    neg = sentiment.get('negative_count', 0)
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<p class="metric-value">{neg}</p>', unsafe_allow_html=True)
                    st.markdown('<p class="metric-label">Negative Articles</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    neu = sentiment.get('neutral_count', 0)
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<p class="metric-value">{neu}</p>', unsafe_allow_html=True)
                    st.markdown('<p class="metric-label">Neutral Articles</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # ✅ FIXED: News list with persistent expanders
                st.markdown("### Recent News")
                news_items = news_data.get('news', [])
                
                for idx, item in enumerate(news_items[:5]):
                    # Create unique key for each news item
                    news_key = f"news_{idx}"
                    if news_key not in st.session_state.expander_states['view_news_items']:
                        st.session_state.expander_states['view_news_items'][news_key] = False
                    
                    # Get state FIRST
                    news_expanded = st.session_state.expander_states['view_news_items'][news_key]
                    
                    # News expander with state persistence
                    news_expander = st.expander(
                        f"{item.get('title', 'No title')}", 
                        expanded=news_expanded
                    )
                    
                    with news_expander:
                        st.markdown(f"**Source:** {item.get('source', 'Unknown')}")
                        st.markdown(f"**Date:** {item.get('date', 'Unknown')}")
                        st.markdown(f"**Summary:** {item.get('snippet', 'No summary available')}")
                        if item.get('link'):
                            st.markdown(f"[Read more]({item.get('link')})")
                    
                    # Save expander state AFTER
                    st.session_state.expander_states['view_news_items'][news_key] = news_expander.expanded
            
            with tab3:
                st.markdown("## Financial Analysis")
                
                analysis_data = results.get('analysis_data', {})
                financial_data = analysis_data.get('financial_data', {})
                
                # Key metrics in columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    price = financial_data.get('current_price', 0)
                    change = financial_data.get('day_change_pct', 0)
                    change_color = "🔴" if change and change < 0 else "🟢"
                    st.markdown(f'<p class="metric-value">${price:.2f}</p>' if price else '<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="metric-label">Current Price {change_color} {change:+.2f}%</p>' if change else '<p class="metric-label">Current Price</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    market_cap = financial_data.get('market_cap')
                    if market_cap:
                        if market_cap >= 1e12:
                            cap_str = f"${market_cap/1e12:.2f}T"
                        elif market_cap >= 1e9:
                            cap_str = f"${market_cap/1e9:.2f}B"
                        elif market_cap >= 1e6:
                            cap_str = f"${market_cap/1e6:.2f}M"
                        else:
                            cap_str = f"${market_cap:,.0f}"
                        st.markdown(f'<p class="metric-value">{cap_str}</p>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                    st.markdown('<p class="metric-label">Market Cap</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    pe = financial_data.get('pe_ratio')
                    if pe:
                        st.markdown(f'<p class="metric-value">{pe:.2f}</p>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                    st.markdown('<p class="metric-label">P/E Ratio</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    volume = financial_data.get('volume', 0)
                    if volume:
                        if volume >= 1e9:
                            vol_str = f"{volume/1e9:.2f}B"
                        elif volume >= 1e6:
                            vol_str = f"{volume/1e6:.2f}M"
                        else:
                            vol_str = f"{volume:,.0f}"
                        st.markdown(f'<p class="metric-value">{vol_str}</p>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                    st.markdown('<p class="metric-label">Volume</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # 📊 GRAPHS SECTION
                st.markdown("### 📈 Price & Volume Charts")
                
                chart_paths = analysis_data.get('chart_paths', [])
                
                if chart_paths:
                    # Create tabs for different chart views
                    chart_tab1, chart_tab2 = st.tabs(["📊 Price Chart", "📊 Volume Chart"])
                    
                    with chart_tab1:
                        if len(chart_paths) > 0 and os.path.exists(chart_paths[0]):
                            st.image(chart_paths[0], width='stretch')
                            
                            st.markdown("""
                            <div style='background-color: #F3F4F6; padding: 0.5rem; border-radius: 0.5rem; font-size: 0.9rem;'>
                            <b>📊 Price Chart with Moving Averages:</b><br>
                            • Blue line: Daily closing price<br>
                            • Orange dashed: 50-day moving average<br>
                            • Red dashed: 200-day moving average
                            </div>
                            """, unsafe_allow_html=True)
                            
                            with open(chart_paths[0], "rb") as chart_file:
                                st.download_button(
                                    label="📥 Download Price Chart",
                                    data=chart_file,
                                    file_name=os.path.basename(chart_paths[0]),
                                    mime="image/png",
                                    width='stretch'
                                )
                        else:
                            st.info("Price chart not available")
                    
                    with chart_tab2:
                        if len(chart_paths) > 1 and os.path.exists(chart_paths[1]):
                            st.image(chart_paths[1], width='stretch')
                            
                            st.markdown("""
                            <div style='background-color: #F3F4F6; padding: 0.5rem; border-radius: 0.5rem; font-size: 0.9rem;'>
                            <b>📊 Trading Volume Chart:</b><br>
                            • Green bars: Daily trading volume<br>
                            • Higher volume indicates stronger interest
                            </div>
                            """, unsafe_allow_html=True)
                            
                            with open(chart_paths[1], "rb") as chart_file:
                                st.download_button(
                                    label="📥 Download Volume Chart",
                                    data=chart_file,
                                    file_name=os.path.basename(chart_paths[1]),
                                    mime="image/png",
                                    width='stretch'
                                )
                        else:
                            st.info("Volume chart not available")
                    
                    # ✅ FIXED: Additional Charts expander with state persistence
                    if len(chart_paths) > 2:
                        additional_expanded = st.session_state.expander_states.get('additional_charts', False)
                        additional_charts = st.expander("📊 Additional Charts", expanded=additional_expanded)
                        
                        with additional_charts:
                            for i, chart_path in enumerate(chart_paths[2:], 3):
                                if os.path.exists(chart_path):
                                    st.image(chart_path, width='stretch')
                                    with open(chart_path, "rb") as chart_file:
                                        st.download_button(
                                            label=f"📥 Download Chart {i}",
                                            data=chart_file,
                                            file_name=os.path.basename(chart_path),
                                            mime="image/png",
                                            width='stretch'
                                        )
                        
                        # Save expander state AFTER
                        st.session_state.expander_states['additional_charts'] = additional_charts.expanded
                else:
                    st.warning("No charts available for this ticker")
                
                st.markdown("---")
                
                # ✅ FIXED: View All Financial Metrics expander with state persistence
                metrics_expanded = st.session_state.expander_states.get('view_all_metrics', False)
                view_metrics = st.expander("View All Financial Metrics", expanded=metrics_expanded)
                
                with view_metrics:
                    # Create metrics in a clean format
                    metrics_list = [
                        ("Company Name", analysis_data.get('company_name', 'N/A')),
                        ("Sector", financial_data.get('sector', 'N/A')),
                        ("Industry", financial_data.get('industry', 'N/A')),
                        ("---", "---"),
                        ("Current Price", f"${financial_data.get('current_price', 0):.2f}" if financial_data.get('current_price') else 'N/A'),
                        ("Day Change", f"{financial_data.get('day_change_pct', 0):+.2f}%" if financial_data.get('day_change_pct') else 'N/A'),
                        ("52-Week High", f"${financial_data.get('high_52w', 0):.2f}" if financial_data.get('high_52w') else 'N/A'),
                        ("52-Week Low", f"${financial_data.get('low_52w', 0):.2f}" if financial_data.get('low_52w') else 'N/A'),
                        ("50-Day MA", f"${financial_data.get('ma_50', 0):.2f}" if financial_data.get('ma_50') else 'N/A'),
                        ("200-Day MA", f"${financial_data.get('ma_200', 0):.2f}" if financial_data.get('ma_200') else 'N/A'),
                        ("YTD Change", f"{financial_data.get('ytd_change_pct', 0):.2f}%" if financial_data.get('ytd_change_pct') else 'N/A'),
                        ("---", "---"),
                        ("Volume", f"{financial_data.get('volume', 0):,.0f}" if financial_data.get('volume') else 'N/A'),
                        ("Avg Volume", f"{financial_data.get('avg_volume', 0):,.0f}" if financial_data.get('avg_volume') else 'N/A'),
                        ("---", "---"),
                        ("Market Cap", f"${financial_data.get('market_cap', 0):,.0f}" if financial_data.get('market_cap') else 'N/A'),
                        ("P/E Ratio", f"{financial_data.get('pe_ratio', 0):.2f}" if financial_data.get('pe_ratio') else 'N/A'),
                        ("Forward P/E", f"{financial_data.get('forward_pe', 0):.2f}" if financial_data.get('forward_pe') else 'N/A'),
                        ("PEG Ratio", f"{financial_data.get('peg_ratio', 0):.2f}" if financial_data.get('peg_ratio') else 'N/A'),
                        ("EPS", f"${financial_data.get('eps', 0):.2f}" if financial_data.get('eps') else 'N/A'),
                        ("Beta", f"{financial_data.get('beta', 0):.2f}" if financial_data.get('beta') else 'N/A'),
                        ("Dividend Yield", f"{financial_data.get('dividend_yield', 0):.2f}%" if financial_data.get('dividend_yield') else 'N/A'),
                        ("---", "---"),
                        ("Target Mean", f"${financial_data.get('target_mean', 0):.2f}" if financial_data.get('target_mean') else 'N/A'),
                        ("Target High", f"${financial_data.get('target_high', 0):.2f}" if financial_data.get('target_high') else 'N/A'),
                        ("Target Low", f"${financial_data.get('target_low', 0):.2f}" if financial_data.get('target_low') else 'N/A'),
                        ("Recommendation", financial_data.get('recommendation', 'N/A').upper() if financial_data.get('recommendation') else 'N/A')
                    ]
                    
                    # Display in two columns
                    for i in range(0, len(metrics_list), 2):
                        col1, col2 = st.columns(2)
                        with col1:
                            metric, value = metrics_list[i]
                            if metric != "---":
                                st.markdown(f"**{metric}:** `{value}`")
                            else:
                                st.markdown("---")
                        
                        if i + 1 < len(metrics_list):
                            with col2:
                                metric, value = metrics_list[i + 1]
                                if metric != "---":
                                    st.markdown(f"**{metric}:** `{value}`")
                                else:
                                    st.markdown("---")
                
                # Save expander state AFTER
                st.session_state.expander_states['view_all_metrics'] = view_metrics.expanded
                
                # Download all charts as ZIP option
                if chart_paths:
                    # Create ZIP file in memory
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                        for i, chart_path in enumerate(chart_paths):
                            if os.path.exists(chart_path):
                                chart_name = f"{clean_ticker_symbol}_chart_{i+1}.png"
                                zip_file.write(chart_path, chart_name)
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        label="📦 Download All Charts (ZIP)",
                        data=zip_buffer,
                        file_name=f"{clean_ticker_symbol}_charts.zip",
                        mime="application/zip",
                        width='stretch'
                    )
            
            with tab4:
                st.markdown("## Financial Data Export")
                
                analysis_data = results.get('analysis_data', {})
                financial_data = analysis_data.get('financial_data', {})
                
                # Prepare data for DataFrame
                data_rows = []
                
                # Basic Info
                data_rows.append(["Company Name", analysis_data.get('company_name', 'N/A')])
                data_rows.append(["Ticker", clean_ticker_symbol])
                data_rows.append(["Sector", financial_data.get('sector', 'N/A')])
                data_rows.append(["Industry", financial_data.get('industry', 'N/A')])
                
                # Price Data
                data_rows.append(["Current Price", f"${financial_data.get('current_price', 0):.2f}" if financial_data.get('current_price') else 'N/A'])
                data_rows.append(["Day Change", f"{financial_data.get('day_change_pct', 0):.2f}%" if financial_data.get('day_change_pct') else 'N/A'])
                data_rows.append(["52-Week High", f"${financial_data.get('high_52w', 0):.2f}" if financial_data.get('high_52w') else 'N/A'])
                data_rows.append(["52-Week Low", f"${financial_data.get('low_52w', 0):.2f}" if financial_data.get('low_52w') else 'N/A'])
                data_rows.append(["50-Day MA", f"${financial_data.get('ma_50', 0):.2f}" if financial_data.get('ma_50') else 'N/A'])
                data_rows.append(["200-Day MA", f"${financial_data.get('ma_200', 0):.2f}" if financial_data.get('ma_200') else 'N/A'])
                data_rows.append(["YTD Change", f"{financial_data.get('ytd_change_pct', 0):.2f}%" if financial_data.get('ytd_change_pct') else 'N/A'])
                
                # Volume Data
                data_rows.append(["Volume", f"{financial_data.get('volume', 0):,.0f}" if financial_data.get('volume') else 'N/A'])
                data_rows.append(["Avg Volume", f"{financial_data.get('avg_volume', 0):,.0f}" if financial_data.get('avg_volume') else 'N/A'])
                
                # Valuation Metrics
                data_rows.append(["Market Cap", f"${financial_data.get('market_cap', 0):,.0f}" if financial_data.get('market_cap') else 'N/A'])
                data_rows.append(["P/E Ratio", f"{financial_data.get('pe_ratio', 0):.2f}" if financial_data.get('pe_ratio') else 'N/A'])
                data_rows.append(["Forward P/E", f"{financial_data.get('forward_pe', 0):.2f}" if financial_data.get('forward_pe') else 'N/A'])
                data_rows.append(["EPS", f"${financial_data.get('eps', 0):.2f}" if financial_data.get('eps') else 'N/A'])
                data_rows.append(["Beta", f"{financial_data.get('beta', 0):.2f}" if financial_data.get('beta') else 'N/A'])
                data_rows.append(["Dividend Yield", f"{financial_data.get('dividend_yield', 0):.2f}%" if financial_data.get('dividend_yield') else 'N/A'])
                
                # Analyst Targets
                data_rows.append(["Target Mean", f"${financial_data.get('target_mean', 0):.2f}" if financial_data.get('target_mean') else 'N/A'])
                data_rows.append(["Target High", f"${financial_data.get('target_high', 0):.2f}" if financial_data.get('target_high') else 'N/A'])
                data_rows.append(["Target Low", f"${financial_data.get('target_low', 0):.2f}" if financial_data.get('target_low') else 'N/A'])
                data_rows.append(["Recommendation", financial_data.get('recommendation', 'N/A').upper() if financial_data.get('recommendation') else 'N/A'])
                
                # Create DataFrame
                df = pd.DataFrame(data_rows, columns=["Metric", "Value"])
                
                # Display DataFrame in a container
                with st.container():
                    st.markdown('<div class="info-box">', unsafe_allow_html=True)
                    st.markdown("### 📋 Financial Data Summary")
                    
                    # Show the DataFrame
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Metric": st.column_config.TextColumn("Metric", width="medium"),
                            "Value": st.column_config.TextColumn("Value", width="medium")
                        }
                    )
                    
                    # Add download button for DataFrame
                    csv = df.to_csv(index=False).encode('utf-8')
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.download_button(
                            label="📥 Download Data as CSV",
                            data=csv,
                            file_name=f"{clean_ticker_symbol}_financial_data.csv",
                            mime="text/csv",
                            width='stretch',
                            type="primary"
                        )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # ✅ FIXED: Raw JSON Data expander with state persistence
                json_expanded = st.session_state.expander_states.get('view_raw_json', False)
                view_json = st.expander("View Raw JSON Data", expanded=json_expanded)
                
                with view_json:
                    st.json({
                        "ticker": clean_ticker_symbol,
                        "company_name": analysis_data.get('company_name', 'N/A'),
                        "financial_data": financial_data,
                        "metrics": analysis_data.get('metrics', {}),
                        "analysis_summary": analysis_data.get('analysis_summary', '')
                    })
                
                # Save expander state AFTER
                st.session_state.expander_states['view_raw_json'] = view_json.expanded
            
            with tab5:
                st.markdown("## Full Analysis Report")
                
                writer_data = results.get('writer_data', {})
                
                # Create a container for the report
                with st.container():
                    st.markdown('<div class="info-box">', unsafe_allow_html=True)
                    
                    # Report header
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### 📄 {clean_ticker_symbol} - Investment Analysis Report")
                    with col2:
                        st.markdown(f"*{datetime.now().strftime('%Y-%m-%d')}*")
                    
                    st.markdown("---")
                    
                    # Display full report
                    report_text = writer_data.get('full_report', 'No report available')
                    
                    # Show report in an expander (this one can stay expanded=True always)
                    with st.expander("📖 Read Full Report", expanded=True):
                        st.markdown(report_text)
                    
                    # Key metrics summary
                    st.markdown("### 📊 Report Highlights")
                    
                    recommendation = writer_data.get('recommendation', {})
                    rating = recommendation.get('rating', 'HOLD')
                    confidence = recommendation.get('confidence', 'Medium')
                    
                    # Metrics in columns
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f'<p class="metric-value">{rating}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">Recommendation</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f'<p class="metric-value">{confidence}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">Confidence</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        target = recommendation.get('target_price')
                        if target:
                            st.markdown(f'<p class="metric-value">${target:.2f}</p>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<p class="metric-value">N/A</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">Target Price</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        horizon = recommendation.get('time_horizon', 'Medium')
                        st.markdown(f'<p class="metric-value">{horizon}</p>', unsafe_allow_html=True)
                        st.markdown('<p class="metric-label">Time Horizon</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Download buttons section
                    st.markdown("### 📥 Download Options")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # PDF Download
                        pdf_path = results.get('pdf_path')
                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pdf_file:
                                st.download_button(
                                    label="📕 Download PDF Report",
                                    data=pdf_file,
                                    file_name=os.path.basename(pdf_path),
                                    mime="application/pdf",
                                    width='stretch',
                                    type="primary"
                                )
                        else:
                            st.button("📕 PDF Unavailable", disabled=True, width='stretch')
                    
                    with col2:
                        # Text Report Download
                        st.download_button(
                            label="📄 Download Text Report",
                            data=report_text,
                            file_name=f"{clean_ticker_symbol}_report.txt",
                            mime="text/plain",
                            width='stretch'
                        )
                    
                    with col3:
                        # Markdown Download
                        markdown_text = f"""# {clean_ticker_symbol} Investment Analysis Report
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*

{report_text}

---
*Report generated by Finlyze AI - Not financial advice*
"""
                        st.download_button(
                            label="📝 Download Markdown",
                            data=markdown_text,
                            file_name=f"{clean_ticker_symbol}_report.md",
                            mime="text/markdown",
                            width='stretch'
                        )
                    
                    st.markdown('</div>', unsafe_allow_html=True)

elif analyze_button and not ticker:
    st.warning("Please enter a stock ticker symbol")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6B7280; font-size: 0.8rem;'>
        <p>Disclaimer: Finlyze is an AI-powered tool for educational purposes only. 
        The information provided is not financial advice. Always conduct your own research 
        and consult with a qualified financial advisor before making investment decisions.</p>
    </div>
    """,
    unsafe_allow_html=True
)