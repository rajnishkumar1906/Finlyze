# backend/app.py
from flask import Flask, request, jsonify, send_from_directory, Response
from flask.json.provider import DefaultJSONProvider
import os
import uuid
import json
from threading import Thread
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import io

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Enable global CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Handle pre-flight OPTIONS requests globally
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response

# Ensure output directories are created
from utils.helpers import setup_directories, clean_ticker
setup_directories()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
api_key_configured = bool(GEMINI_API_KEY)

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle NumPy types like int64/float64 and convert them to standard Python types"""
    def default(self, obj):
        if hasattr(obj, 'item') and callable(getattr(obj, 'item')):
            return obj.item()
        elif hasattr(obj, 'tolist') and callable(getattr(obj, 'tolist')):
            return obj.tolist()
        try:
            return super(CustomJSONEncoder, self).default(obj)
        except TypeError:
            return str(obj)

class CustomJSONProvider(DefaultJSONProvider):
    """Custom Flask JSON provider that registers the CustomJSONEncoder globally"""
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)

# Register the custom provider
app.json = CustomJSONProvider(app)

# Global dictionary to track background tasks
tasks = {}

def run_workflow_async(task_id, ticker, company_name):
    """Background task runner to execute the workflow steps and update task status"""
    # If company name is not provided, do a quick lookup via yfinance
    resolved_name = company_name
    if not resolved_name:
        try:
            import yfinance as yf
            ticker_obj = yf.Ticker(ticker)
            resolved_name = ticker_obj.info.get('longName') or ticker_obj.info.get('shortName') or ticker
        except Exception:
            resolved_name = ticker

    tasks[task_id] = {
        "status": "processing",
        "ticker": ticker,
        "company_name": resolved_name,
        "current_step": 0,
        "agent_status": {
            "researcher": "pending",
            "analyst": "pending",
            "writer": "pending"
        },
        "messages": [f"[System] Initializing analysis pipeline for {ticker} ({resolved_name})..."],
        "results": None,
        "error": None
    }
    
    try:
        if not GEMINI_API_KEY:
            raise Exception("GEMINI_API_KEY not found in .env file!")
            
        from graph.workflow import FinlyzeWorkflow
        # Initialize workflow
        workflow = FinlyzeWorkflow(api_key=GEMINI_API_KEY)
        
        # Step 1: Research Agent
        tasks[task_id]["agent_status"]["researcher"] = "working"
        tasks[task_id]["messages"].append(f"[Researcher] Analyzing recent market news and sentiment trends for {resolved_name}...")
        
        research_data = workflow.researcher.research(ticker, resolved_name)
        tasks[task_id]["research_data"] = research_data
        
        news_count = len(research_data.get('news_data', {}).get('news', []))
        sentiment = research_data.get('news_data', {}).get('sentiment', {}).get('overall', 'neutral')
        
        tasks[task_id]["agent_status"]["researcher"] = "completed"
        tasks[task_id]["current_step"] = 1
        tasks[task_id]["messages"].extend([
            "[Researcher] Market news retrieval and sentiment analysis completed.",
            f"[Researcher] Compiled {news_count} relevant articles.",
            f"[Researcher] Calculated overall market sentiment: {sentiment.upper()}"
        ])
        
        # Step 2: Analyst Agent
        tasks[task_id]["agent_status"]["analyst"] = "working"
        tasks[task_id]["messages"].append("[Analyst] Retrieving market pricing data and generating technical charts...")
        
        analysis_data = workflow.analyst.analyze(ticker)
        tasks[task_id]["analysis_data"] = analysis_data
        
        fin = analysis_data.get('financial_data', {})
        current_price = fin.get('current_price')
        pe_ratio = fin.get('pe_ratio')
        price_msg = f"[Analyst] Current market price: ${current_price:.2f}" if current_price else ""
        pe_msg = f"[Analyst] Price-to-Earnings (P/E) Ratio: {pe_ratio:.2f}" if pe_ratio else ""
        
        tasks[task_id]["agent_status"]["analyst"] = "completed"
        tasks[task_id]["current_step"] = 2
        tasks[task_id]["messages"].append("[Analyst] Financial data extraction and charts generation completed.")
        if price_msg: 
            tasks[task_id]["messages"].append(price_msg)
        if pe_msg: 
            tasks[task_id]["messages"].append(pe_msg)
            
        chart_paths = analysis_data.get('chart_paths', [])
        if chart_paths:
            tasks[task_id]["messages"].append(f"[Analyst] Saved {len(chart_paths)} visualization charts.")
            
        # Step 3: Writer Agent
        tasks[task_id]["agent_status"]["writer"] = "working"
        tasks[task_id]["messages"].append("[Writer] Synthesizing news, sentiment, and financial datasets...")
        
        writer_data = workflow.writer.write_report(ticker, research_data, analysis_data)
        tasks[task_id]["writer_data"] = writer_data
        
        recommendation = writer_data.get('recommendation', {})
        rating = recommendation.get('rating', 'HOLD')
        confidence = recommendation.get('confidence', 'Medium')
        
        tasks[task_id]["agent_status"]["writer"] = "completed"
        tasks[task_id]["current_step"] = 3
        tasks[task_id]["messages"].extend([
            "[Writer] Investment thesis synthesis completed.",
            f"[Writer] Recommendation: {rating} ({confidence} confidence)",
            f"[System] Analysis pipeline successfully completed."
        ])
        
        # Save final results
        tasks[task_id]["results"] = {
            "research_data": research_data,
            "analysis_data": analysis_data,
            "writer_data": writer_data,
            "pdf_path": writer_data.get('pdf_path')
        }
        tasks[task_id]["status"] = "completed"
        
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["messages"].append(f"[System] Analysis failed: {str(e)}")

# --- Flask REST API Routes ---

@app.route('/api/config')
def get_config():
    """Returns application status configuration"""
    return jsonify({
        "api_key_configured": api_key_configured
    })

@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    """Trigger the analysis by starting a background thread"""
    # Accept JSON payload or URL Form data
    if request.is_json:
        data = request.json or {}
        ticker = data.get('ticker', '').strip().upper()
        company_name = data.get('company_name', '').strip()
    else:
        ticker = request.form.get('ticker', '').strip().upper()
        company_name = request.form.get('company_name', '').strip()
        
    if not ticker:
        return jsonify({"error": "Ticker is required"}), 400
        
    cleaned_ticker = clean_ticker(ticker)
    task_id = uuid.uuid4().hex
    
    # Start analysis in a separate thread
    thread = Thread(target=run_workflow_async, args=(task_id, cleaned_ticker, company_name))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "task_id": task_id,
        "ticker": cleaned_ticker,
        "company_name": company_name
    })

@app.route('/api/status/<task_id>')
def get_status(task_id):
    """API endpoint for fetching task progress"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({"status": "not_found", "error": "Task not found"}), 404
    return jsonify({
        "status": task["status"],
        "ticker": task["ticker"],
        "company_name": task.get("company_name", ""),
        "current_step": task["current_step"],
        "agent_status": task["agent_status"],
        "messages": task["messages"],
        "error": task["error"],
        "research_data": task.get("research_data"),
        "analysis_data": task.get("analysis_data"),
        "writer_data": task.get("writer_data")
    })

@app.route('/api/results/<task_id>')
def results_page(task_id):
    """Display final analysis results once completed"""
    task = tasks.get(task_id)
    if not task or task["status"] != "completed":
        return jsonify({"error": "Analysis not found or in-progress"}), 404
        
    results = task["results"]
    research_data = results["research_data"]
    analysis_data = results["analysis_data"]
    writer_data = results["writer_data"]
    
    # Process financial data
    fin = analysis_data.get('financial_data', {})
    
    # Format Market Cap
    market_cap = fin.get('market_cap')
    if market_cap:
        if market_cap >= 1e12:
            market_cap_formatted = f"${market_cap/1e12:.2f}T"
        elif market_cap >= 1e9:
            market_cap_formatted = f"${market_cap/1e9:.2f}B"
        elif market_cap >= 1e6:
            market_cap_formatted = f"${market_cap/1e6:.2f}M"
        else:
            market_cap_formatted = f"${market_cap:,.0f}"
    else:
        market_cap_formatted = "N/A"
        
    # Compile flat metrics list for data export table
    flat_metrics = [
        ("Company Name", analysis_data.get('company_name', 'N/A')),
        ("Sector", fin.get('sector', 'N/A')),
        ("Industry", fin.get('industry', 'N/A')),
        ("Current Price", f"${fin.get('current_price', 0):.2f}" if fin.get('current_price') else 'N/A'),
        ("Day Change", f"{fin.get('day_change_pct', 0):+.2f}%" if fin.get('day_change_pct') else 'N/A'),
        ("52-Week High", f"${fin.get('high_52w', 0):.2f}" if fin.get('high_52w') else 'N/A'),
        ("52-Week Low", f"${fin.get('low_52w', 0):.2f}" if fin.get('low_52w') else 'N/A'),
        ("50-Day MA", f"${fin.get('ma_50', 0):.2f}" if fin.get('ma_50') else 'N/A'),
        ("200-Day MA", f"${fin.get('ma_200', 0):.2f}" if fin.get('ma_200') else 'N/A'),
        ("YTD Change", f"{fin.get('ytd_change_pct', 0):.2f}%" if fin.get('ytd_change_pct') else 'N/A'),
        ("Volume", f"{fin.get('volume', 0):,.0f}" if fin.get('volume') else 'N/A'),
        ("Avg Volume", f"{fin.get('avg_volume', 0):,.0f}" if fin.get('avg_volume') else 'N/A'),
        ("Market Cap", f"${fin.get('market_cap', 0):,.0f}" if fin.get('market_cap') else 'N/A'),
        ("P/E Ratio", f"{fin.get('pe_ratio', 0):.2f}" if fin.get('pe_ratio') else 'N/A'),
        ("Forward P/E", f"{fin.get('forward_pe', 0):.2f}" if fin.get('forward_pe') else 'N/A'),
        ("PEG Ratio", f"{fin.get('peg_ratio', 0):.2f}" if fin.get('peg_ratio') else 'N/A'),
        ("EPS", f"${fin.get('eps', 0):.2f}" if fin.get('eps') else 'N/A'),
        ("Beta", f"{fin.get('beta', 0):.2f}" if fin.get('beta') else 'N/A'),
        ("Dividend Yield", f"{fin.get('dividend_yield', 0):.2f}%" if fin.get('dividend_yield') else 'N/A'),
        ("Target Mean", f"${fin.get('target_mean', 0):.2f}" if fin.get('target_mean') else 'N/A'),
        ("Target High", f"${fin.get('target_high', 0):.2f}" if fin.get('target_high') else 'N/A'),
        ("Target Low", f"${fin.get('target_low', 0):.2f}" if fin.get('target_low') else 'N/A'),
        ("Recommendation", fin.get('recommendation', 'N/A').upper() if fin.get('recommendation') else 'N/A')
    ]
    
    # Process chart paths for web serving (convert output/... to /api/output/...)
    chart_paths = analysis_data.get('chart_paths', [])
    web_chart_paths = []
    for path in chart_paths:
        web_path = path.replace('\\', '/').replace('output/', '/api/output/')
        web_chart_paths.append(web_path)
        
    pdf_path = results.get('pdf_path')
    web_pdf_path = pdf_path.replace('\\', '/').replace('output/', '/api/output/') if pdf_path else None
    
    # Prepare raw JSON representation
    raw_json_str = json.dumps({
        "ticker": task["ticker"],
        "company_name": analysis_data.get('company_name', 'N/A'),
        "financial_data": fin,
        "metrics": analysis_data.get('metrics', {}),
        "analysis_summary": analysis_data.get('analysis_summary', '')
    }, indent=4, cls=CustomJSONEncoder)
    
    return jsonify({
        "task_id": task_id,
        "ticker": task["ticker"],
        "company_name": analysis_data.get('company_name'),
        "research_data": research_data,
        "analysis_data": analysis_data,
        "writer_data": writer_data,
        "market_cap_formatted": market_cap_formatted,
        "flat_metrics": flat_metrics,
        "web_chart_paths": web_chart_paths,
        "web_pdf_path": web_pdf_path,
        "raw_json_str": raw_json_str,
        "date_str": datetime.now().strftime('%Y-%m-%d')
    })

@app.route('/api/output/<path:filename>')
def serve_output(filename):
    """Serve dynamically generated charts & PDFs from output/ folder"""
    return send_from_directory('output', filename)

@app.route('/api/download/csv/<task_id>')
def download_csv(task_id):
    """Generate and return CSV file containing the financial data"""
    task = tasks.get(task_id)
    if not task or task["status"] != "completed":
        return "Task not found", 404
        
    analysis_data = task["results"]["analysis_data"]
    fin = analysis_data.get('financial_data', {})
    
    data_rows = [
        ["Company Name", analysis_data.get('company_name', 'N/A')],
        ["Ticker", task["ticker"]],
        ["Sector", fin.get('sector', 'N/A')],
        ["Industry", fin.get('industry', 'N/A')],
        ["Current Price", fin.get('current_price', 'N/A')],
        ["Day Change %", fin.get('day_change_pct', 'N/A')],
        ["52-Week High", fin.get('high_52w', 'N/A')],
        ["52-Week Low", fin.get('low_52w', 'N/A')],
        ["50-Day MA", fin.get('ma_50', 'N/A')],
        ["200-Day MA", fin.get('ma_200', 'N/A')],
        ["YTD Change %", fin.get('ytd_change_pct', 'N/A')],
        ["Volume", fin.get('volume', 'N/A')],
        ["Avg Volume", fin.get('avg_volume', 'N/A')],
        ["Market Cap", fin.get('market_cap', 'N/A')],
        ["P/E Ratio", fin.get('pe_ratio', 'N/A')],
        ["Forward P/E", fin.get('forward_pe', 'N/A')],
        ["PEG Ratio", fin.get('peg_ratio', 'N/A')],
        ["EPS", fin.get('eps', 'N/A')],
        ["Beta", fin.get('beta', 'N/A')],
        ["Dividend Yield %", fin.get('dividend_yield', 'N/A')],
        ["Target Mean", fin.get('target_mean', 'N/A')],
        ["Target High", fin.get('target_high', 'N/A')],
        ["Target Low", fin.get('target_low', 'N/A')],
        ["Recommendation", fin.get('recommendation', 'N/A')]
    ]
    
    df = pd.DataFrame(data_rows, columns=["Metric", "Value"])
    
    proxy = io.StringIO()
    df.to_csv(proxy, index=False)
    
    return Response(
        proxy.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={task['ticker']}_financial_data.csv"}
    )

@app.route('/api/download/txt/<task_id>')
def download_txt(task_id):
    """Download plain text version of the generated report"""
    task = tasks.get(task_id)
    if not task or task["status"] != "completed":
        return "Task not found", 404
        
    writer_data = task["results"]["writer_data"]
    report_text = writer_data.get('full_report', 'No report content generated.')
    
    # Decorate output text report
    full_text = f"""==================================================
FINLYZE INVESTMENT ANALYSIS REPORT: {task['ticker']}
Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}
==================================================

{report_text}

--------------------------------------------------
Disclaimer: Generated by Finlyze AI. Not financial advice.
"""
    return Response(
        full_text,
        mimetype="text/plain",
        headers={"Content-disposition": f"attachment; filename={task['ticker']}_report.txt"}
    )

if __name__ == '__main__':
    # Start the Flask REST API server
    app.run(debug=True, port=5000)