# tools/finance_tools.py
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
import logging

from utils.helpers import save_chart, format_currency, format_percentage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_stock_data(ticker: str, period: str = "6mo") -> Optional[Dict[str, Any]]:
    """
    Fetch stock data using yfinance
    """
    try:
        logger.info(f"Fetching data for {ticker}")
        stock = yf.Ticker(ticker)
        
        # Get historical data
        hist = stock.history(period=period)
        if hist.empty:
            logger.error(f"No historical data found for {ticker}")
            return None
        
        # Get info
        info = stock.info
        
        # Get financials
        financials = stock.financials
        quarterly_financials = stock.quarterly_financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        # Get recommendations
        recommendations = stock.recommendations
        
        # Get major holders
        major_holders = stock.major_holders
        
        # Calculate key metrics
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        day_change = current_price - prev_close
        day_change_pct = (day_change / prev_close) * 100
        
        # Calculate moving averages
        ma_50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else None
        ma_200 = hist['Close'].rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else None
        
        # Calculate YTD change
        year_start = datetime.now().replace(month=1, day=1)
        year_start_str = year_start.strftime("%Y-%m-%d")
        if year_start_str in hist.index.strftime("%Y-%m-%d"):
            year_start_price = hist.loc[hist.index.strftime("%Y-%m-%d") == year_start_str, 'Close'].iloc[0]
            ytd_change_pct = ((current_price - year_start_price) / year_start_price) * 100
        else:
            ytd_change_pct = None
        
        # Compile data
        data = {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', None),
            'current_price': current_price,
            'day_change': day_change,
            'day_change_pct': day_change_pct,
            'volume': hist['Volume'].iloc[-1],
            'avg_volume': hist['Volume'].mean(),
            'high_52w': info.get('fiftyTwoWeekHigh', None),
            'low_52w': info.get('fiftyTwoWeekLow', None),
            'pe_ratio': info.get('trailingPE', None),
            'forward_pe': info.get('forwardPE', None),
            'peg_ratio': info.get('pegRatio', None),
            'eps': info.get('trailingEps', None),
            'beta': info.get('beta', None),
            'dividend_yield': info.get('dividendYield', None) * 100 if info.get('dividendYield') else None,
            'ex_dividend_date': info.get('exDividendDate', None),
            'target_mean': info.get('targetMeanPrice', None),
            'target_high': info.get('targetHighPrice', None),
            'target_low': info.get('targetLowPrice', None),
            'recommendation': info.get('recommendationKey', 'N/A'),
            'ma_50': ma_50,
            'ma_200': ma_200,
            'ytd_change_pct': ytd_change_pct,
            'historical_data': hist.to_dict(),
            'last_updated': datetime.now().isoformat()
        }
        
        logger.info(f"Successfully fetched data for {ticker}")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        return None

def generate_price_chart(ticker: str, data: Dict[str, Any]) -> Optional[str]:
    """
    Generate price chart with moving averages
    """
    try:
        # Extract historical data
        hist_dict = data.get('historical_data', {})
        if not hist_dict:
            return None
        
        # Convert back to DataFrame
        dates = list(hist_dict.get('Close', {}).keys())
        prices = list(hist_dict.get('Close', {}).values())
        
        if not dates or not prices:
            return None
        
        df = pd.DataFrame({
            'Date': pd.to_datetime(dates),
            'Close': prices
        }).set_index('Date').sort_index()
        
        # Calculate MAs
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['MA200'] = df['Close'].rolling(window=200).mean()
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(df.index, df['Close'], label='Close Price', linewidth=2, color='blue')
        ax.plot(df.index, df['MA50'], label='50-day MA', linewidth=1.5, linestyle='--', color='orange')
        ax.plot(df.index, df['MA200'], label='200-day MA', linewidth=1.5, linestyle='--', color='red')
        
        ax.set_title(f'{ticker} - Stock Price with Moving Averages', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save chart
        chart_path = save_chart(fig, ticker, 'price_ma')
        return chart_path
        
    except Exception as e:
        logger.error(f"Error generating price chart: {str(e)}")
        return None

def generate_volume_chart(ticker: str, data: Dict[str, Any]) -> Optional[str]:
    """
    Generate volume chart
    """
    try:
        # Extract historical data
        hist_dict = data.get('historical_data', {})
        if not hist_dict:
            return None
        
        dates = list(hist_dict.get('Volume', {}).keys())
        volumes = list(hist_dict.get('Volume', {}).values())
        
        if not dates or not volumes:
            return None
        
        df = pd.DataFrame({
            'Date': pd.to_datetime(dates),
            'Volume': volumes
        }).set_index('Date').sort_index()
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 4))
        
        ax.bar(df.index, df['Volume'], color='green', alpha=0.6, width=0.8)
        ax.set_title(f'{ticker} - Trading Volume', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Volume', fontsize=12)
        
        # Format y-axis with K/M/B
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_large_number(x)))
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save chart
        chart_path = save_chart(fig, ticker, 'volume')
        return chart_path
        
    except Exception as e:
        logger.error(f"Error generating volume chart: {str(e)}")
        return None

def calculate_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate additional financial metrics
    """
    metrics = {}
    
    try:
        # P/E ratio analysis
        if data.get('pe_ratio'):
            pe = data['pe_ratio']
            if pe < 15:
                metrics['pe_analysis'] = 'Below market average (potentially undervalued)'
            elif pe < 25:
                metrics['pe_analysis'] = 'Within normal range'
            else:
                metrics['pe_analysis'] = 'Above market average (potentially overvalued)'
        
        # PEG ratio analysis
        if data.get('peg_ratio'):
            peg = data['peg_ratio']
            if peg < 1:
                metrics['peg_analysis'] = 'Good value (PEG < 1)'
            elif peg < 2:
                metrics['peg_analysis'] = 'Fair value'
            else:
                metrics['peg_analysis'] = 'Expensive (PEG > 2)'
        
        # Moving average signals
        current_price = data.get('current_price')
        ma_50 = data.get('ma_50')
        ma_200 = data.get('ma_200')
        
        if current_price and ma_50 and ma_200:
            if current_price > ma_50 > ma_200:
                metrics['ma_signal'] = 'Strong uptrend (price > 50-day > 200-day)'
            elif current_price < ma_50 < ma_200:
                metrics['ma_signal'] = 'Strong downtrend (price < 50-day < 200-day)'
            elif current_price > ma_50 and current_price < ma_200:
                metrics['ma_signal'] = 'Mixed signals (price > 50-day but < 200-day)'
            elif current_price < ma_50 and current_price > ma_200:
                metrics['ma_signal'] = 'Mixed signals (price < 50-day but > 200-day)'
        
        # Calculate volatility
        hist_dict = data.get('historical_data', {})
        if hist_dict and 'Close' in hist_dict:
            prices = list(hist_dict['Close'].values())
            if len(prices) > 1:
                returns = [(prices[i] - prices[i-1])/prices[i-1] for i in range(1, len(prices))]
                volatility = np.std(returns) * np.sqrt(252)  # Annualized
                metrics['volatility'] = volatility
                if volatility < 0.2:
                    metrics['volatility_analysis'] = 'Low volatility'
                elif volatility < 0.4:
                    metrics['volatility_analysis'] = 'Moderate volatility'
                else:
                    metrics['volatility_analysis'] = 'High volatility'
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
    
    return metrics

# Helper function for large number formatting
def format_large_number(x):
    if x >= 1e9:
        return f'{x/1e9:.1f}B'
    elif x >= 1e6:
        return f'{x/1e6:.1f}M'
    elif x >= 1e3:
        return f'{x/1e3:.1f}K'
    else:
        return f'{x:.0f}'