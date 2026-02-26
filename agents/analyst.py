# agents/analyst.py
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from typing import Dict, Any, List, Optional
import logging
import json

from tools.finance_tools import (
    fetch_stock_data, 
    generate_price_chart, 
    generate_volume_chart,
    calculate_metrics
)
from prompts import ANALYST_PROMPT, ANALYST_SYSTEM

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalystAgent:
    """Agent responsible for financial data analysis"""
    
    def __init__(self, api_key: str = None):
        """Initialize analyst agent with Gemini LLM"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        # Initialize Gemini
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flas",
            google_api_key=self.api_key,
            temperature=0.2,  # Lower temperature for more factual analysis
            convert_system_message_to_human=True
        )
        
        logger.info("AnalystAgent initialized")
    
    def analyze(self, ticker: str) -> Dict[str, Any]:
        """
        Main analysis method - fetches financial data and analyzes it
        """
        try:
            logger.info(f"Analyzing {ticker}")
            
            # Step 1: Fetch financial data
            financial_data = fetch_stock_data(ticker)
            
            if not financial_data:
                logger.error(f"Failed to fetch financial data for {ticker}")
                return {
                    'ticker': ticker,
                    'analysis_summary': f"Failed to fetch financial data for {ticker}",
                    'financial_data': {},
                    'error': 'No financial data available'
                }
            
            # Step 2: Calculate additional metrics
            metrics = calculate_metrics(financial_data)
            
            # Step 3: Generate charts
            chart_paths = []
            price_chart = generate_price_chart(ticker, financial_data)
            # Already good, but you could add:
            if chart_paths:
                logger.info(f"Generated {len(chart_paths)} charts for {ticker}")
            
            volume_chart = generate_volume_chart(ticker, financial_data)
            if volume_chart:
                chart_paths.append(volume_chart)
            
            # Step 4: Use LLM to analyze the data
            analysis = self._analyze_with_llm(ticker, financial_data, metrics)
            
            # Step 5: Compile final analysis output
            analysis_output = {
                'ticker': ticker,
                'company_name': financial_data.get('company_name', ticker),
                'analysis_summary': analysis.get('summary', ''),
                'valuation_analysis': analysis.get('valuation', ''),
                'technical_analysis': analysis.get('technical', ''),
                'strengths': analysis.get('strengths', []),
                'concerns': analysis.get('concerns', []),
                'financial_health': analysis.get('health', ''),
                'metrics': metrics,
                'financial_data': {
                    'current_price': financial_data.get('current_price'),
                    'market_cap': financial_data.get('market_cap'),
                    'pe_ratio': financial_data.get('pe_ratio'),
                    'forward_pe': financial_data.get('forward_pe'),
                    'eps': financial_data.get('eps'),
                    'beta': financial_data.get('beta'),
                    'dividend_yield': financial_data.get('dividend_yield'),
                    'high_52w': financial_data.get('high_52w'),
                    'low_52w': financial_data.get('low_52w'),
                    'volume': financial_data.get('volume'),
                    'avg_volume': financial_data.get('avg_volume'),
                    'ma_50': financial_data.get('ma_50'),
                    'ma_200': financial_data.get('ma_200'),
                    'ytd_change_pct': financial_data.get('ytd_change_pct')
                },
                'chart_paths': chart_paths
            }
            
            logger.info(f"Analysis completed for {ticker}")
            return analysis_output
            
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            return {
                'ticker': ticker,
                'analysis_summary': f"Error during analysis: {str(e)}",
                'financial_data': {},
                'chart_paths': [],
                'error': str(e)
            }
    
    def _analyze_with_llm(self, ticker: str, financial_data: Dict, metrics: Dict) -> Dict[str, Any]:
        """Use LLM to analyze financial data"""
        try:
            # Prepare data summary for LLM
            data_summary = self._prepare_data_summary(financial_data, metrics)
            
            # Create messages
            messages = [
                SystemMessage(content=ANALYST_SYSTEM),
                HumanMessage(content=ANALYST_PROMPT.format(
                    ticker=ticker,
                    company_name=financial_data.get('company_name', ticker),
                    financial_data=data_summary,
                    metrics=json.dumps(metrics, indent=2)
                ))
            ]
            
            # Get LLM response
            response = self.llm.invoke(messages)
            
            # Parse response
            analysis = self._parse_analysis_response(response.content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            return {
                'summary': f"Analysis based on financial data. Current price: ${financial_data.get('current_price', 0):.2f}, P/E: {financial_data.get('pe_ratio', 'N/A')}",
                'valuation': 'See summary',
                'technical': 'See summary',
                'strengths': [],
                'concerns': [],
                'health': 'Unknown'
            }
    
    def _prepare_data_summary(self, financial_data: Dict, metrics: Dict) -> str:
        """Prepare financial data for LLM input"""
        summary = f"""
Company: {financial_data.get('company_name', 'Unknown')}
Sector: {financial_data.get('sector', 'Unknown')}
Industry: {financial_data.get('industry', 'Unknown')}

PRICE DATA:
- Current Price: ${financial_data.get('current_price', 0):.2f}
- Day Change: ${financial_data.get('day_change', 0):.2f} ({financial_data.get('day_change_pct', 0):.2f}%)
- 52-Week High: ${financial_data.get('high_52w', 0):.2f}
- 52-Week Low: ${financial_data.get('low_52w', 0):.2f}
- 50-Day MA: ${financial_data.get('ma_50', 0):.2f}
- 200-Day MA: ${financial_data.get('ma_200', 0):.2f}
- YTD Change: {financial_data.get('ytd_change_pct', 0):.2f}%

VALUATION METRICS:
- Market Cap: ${financial_data.get('market_cap', 0):,.0f}
- P/E Ratio: {financial_data.get('pe_ratio', 'N/A')}
- Forward P/E: {financial_data.get('forward_pe', 'N/A')}
- EPS: ${financial_data.get('eps', 0):.2f}
- PEG Ratio: {financial_data.get('peg_ratio', 'N/A')}

OTHER METRICS:
- Beta: {financial_data.get('beta', 'N/A')}
- Dividend Yield: {financial_data.get('dividend_yield', 0):.2f}%
- Volume: {financial_data.get('volume', 0):,.0f}
- Avg Volume: {financial_data.get('avg_volume', 0):,.0f}
- Target Price (Mean): ${financial_data.get('target_mean', 0):.2f}
- Recommendation: {financial_data.get('recommendation', 'N/A')}
"""
        return summary
    
    def _parse_analysis_response(self, text: str) -> Dict[str, Any]:
        """Parse LLM response into structured analysis"""
        analysis = {
            'summary': '',
            'valuation': '',
            'technical': '',
            'strengths': [],
            'concerns': [],
            'health': ''
        }
        
        lines = text.split('\n')
        current_section = 'summary'
        
        for line in lines:
            line_lower = line.lower()
            
            # Detect sections
            if 'valuation' in line_lower or 'p/e' in line_lower:
                current_section = 'valuation'
                if line.strip() and len(line) > 10:
                    analysis['valuation'] += line + '\n'
            elif 'technical' in line_lower or 'trend' in line_lower or 'moving average' in line_lower:
                current_section = 'technical'
                if line.strip() and len(line) > 10:
                    analysis['technical'] += line + '\n'
            elif 'strength' in line_lower or 'bull' in line_lower or 'positive' in line_lower:
                current_section = 'strengths'
                if line.strip() and line[0] in ['-', '•', '*']:
                    analysis['strengths'].append(line.strip())
            elif 'concern' in line_lower or 'risk' in line_lower or 'bear' in line_lower or 'negative' in line_lower:
                current_section = 'concerns'
                if line.strip() and line[0] in ['-', '•', '*']:
                    analysis['concerns'].append(line.strip())
            elif 'health' in line_lower or 'financial health' in line_lower:
                current_section = 'health'
                if line.strip() and len(line) > 10:
                    analysis['health'] += line + '\n'
            else:
                # Add to current section
                if current_section == 'summary':
                    analysis['summary'] += line + ' '
                elif current_section == 'valuation':
                    analysis['valuation'] += line + '\n'
                elif current_section == 'technical':
                    analysis['technical'] += line + '\n'
                elif current_section == 'health':
                    analysis['health'] += line + '\n'
                elif current_section in ['strengths', 'concerns'] and line.strip() and line[0] in ['-', '•', '*']:
                    analysis[current_section].append(line.strip())
        
        # Clean up
        for key in ['summary', 'valuation', 'technical', 'health']:
            analysis[key] = analysis[key].strip()
        
        return analysis
    
    def calculate_target_price(self, financial_data: Dict) -> Optional[float]:
        """Calculate a simple target price based on fundamentals"""
        try:
            current_price = financial_data.get('current_price')
            pe = financial_data.get('pe_ratio')
            eps = financial_data.get('eps')
            
            if current_price and pe and eps:
                # Simple DCF-like estimate
                industry_pe = 20  # Default industry average
                fair_price = eps * industry_pe
                return fair_price
            
            return financial_data.get('target_mean')
            
        except Exception as e:
            logger.error(f"Error calculating target price: {str(e)}")
            return None