# utils/helpers.py
import os
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Streamlit

def setup_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs("output", exist_ok=True)
    os.makedirs("output/charts", exist_ok=True)
    if os.path.exists("output"):
        print("✅ Output directory ready")

def clean_ticker(ticker: str) -> str:
    """Clean and validate ticker symbol, stripping exchange prefixes like NASDAQ- META or NASDAQ:META"""
    t = ticker.strip().upper()
    
    # Common exchange identifiers to strip
    exchanges = ["NASDAQ", "NYSE", "AMEX", "NSE", "BSE", "LSE", "TSX", "ASX"]
    
    # Check if there is a separator like '-', ':', '/', or space ' '
    for sep in [':', '-', '/', ' ']:
        if sep in t:
            parts = [p.strip() for p in t.split(sep) if p.strip()]
            if len(parts) >= 2:
                # If first part is a known exchange, return the second part (e.g. NASDAQ-META -> META)
                if parts[0] in exchanges:
                    return parts[1]
                # If the second part is a known exchange, return the first part (e.g. META NYSE -> META)
                if parts[1] in exchanges:
                    return parts[0]
                
    return t

def format_currency(value: float) -> str:
    """Format number as currency"""
    if pd.isna(value) or value is None:
        return "N/A"
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    else:
        return f"${value:,.2f}"

def format_percentage(value: float) -> str:
    """Format as percentage"""
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:.2f}%"

def format_large_number(value: float) -> str:
    """Format large numbers with K/M/B suffixes"""
    if pd.isna(value) or value is None:
        return "N/A"
    if value >= 1e9:
        return f"{value/1e9:.2f}B"
    elif value >= 1e6:
        return f"{value/1e6:.2f}M"
    elif value >= 1e3:
        return f"{value/1e3:.2f}K"
    else:
        return f"{value:.2f}"

def save_chart(fig, ticker: str, chart_type: str) -> str:
    """Save matplotlib figure to file and return path"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/charts/{ticker}_{chart_type}_{timestamp}.png"
    fig.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close(fig)
    return filename

def parse_date(date_str: str) -> str:
    """Parse various date formats to standard string"""
    try:
        # Handle different date formats
        if isinstance(date_str, datetime):
            return date_str.strftime("%Y-%m-%d")
        # Add more parsing logic as needed
        return str(date_str)
    except:
        return str(date_str)

def safe_get(data: Dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    try:
        return data.get(key, default)
    except:
        return default