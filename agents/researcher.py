# agents/researcher.py
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from typing import Dict, Any
import logging
import json

from dotenv import load_dotenv
load_dotenv()

from tools.news_tools import get_ticker_news_with_sentiment
from prompts import RESEARCHER_PROMPT, RESEARCHER_SYSTEM

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearcherAgent:
    """Agent responsible for news research and sentiment analysis"""
    
    def __init__(self, api_key: str = None):
        """Initialize researcher agent with Gemini LLM"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        # Initialize Gemini
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.3,
            convert_system_message_to_human=True
        )
        
        logger.info("ResearcherAgent initialized")
    
    def research(self, ticker: str, company_name: str = "") -> Dict[str, Any]:
        """
        Main research method - gathers news and analyzes sentiment
        """
        try:
            logger.info(f"Researching {ticker} - {company_name if company_name else 'No company name'}")
            
            # Step 1: Gather news data
            news_data = get_ticker_news_with_sentiment(ticker, company_name)
            
            if not news_data or not news_data.get('news'):
                logger.warning(f"No news found for {ticker}")
                return {
                    'ticker': ticker,
                    'research_summary': f"No recent news found for {ticker}",
                    'news_data': {'news': [], 'sentiment': {'overall': 'neutral'}},
                    'raw_news': []
                }
            
            # Step 2: Use LLM to analyze and summarize
            analysis = self._analyze_with_llm(ticker, news_data)
            
            # Step 3: Compile final research data
            research_output = {
                'ticker': ticker,
                'research_summary': analysis.get('summary', ''),
                'news_data': news_data,
                'key_developments': analysis.get('key_developments', []),
                'sentiment_analysis': analysis.get('sentiment_analysis', news_data.get('sentiment', {})),
                'risks': analysis.get('risks', []),
                'opportunities': analysis.get('opportunities', []),
                'raw_news': news_data.get('news', [])[:5]  # Top 5 news items
            }
            
            logger.info(f"Research completed for {ticker}")
            return research_output
            
        except Exception as e:
            logger.error(f"Error in research: {str(e)}")
            return {
                'ticker': ticker,
                'research_summary': f"Error during research: {str(e)}",
                'news_data': {'news': [], 'sentiment': {'overall': 'neutral'}},
                'error': str(e)
            }
    
    def _analyze_with_llm(self, ticker: str, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze news data"""
        try:
            # Prepare news summary for LLM
            news_summary = self._prepare_news_summary(news_data)
            
            # Create messages
            messages = [
                SystemMessage(content=RESEARCHER_SYSTEM),
                HumanMessage(content=RESEARCHER_PROMPT.format(
                    ticker=ticker,
                    news_data=news_summary
                ))
            ]
            
            # Get LLM response
            response = self.llm.invoke(messages)
            
            # Parse response
            analysis = {
                'summary': response.content,
                'key_developments': self._extract_developments(response.content),
                'sentiment_analysis': news_data.get('sentiment', {}),
                'risks': self._extract_risks(response.content),
                'opportunities': self._extract_opportunities(response.content)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            return {
                'summary': f"Analysis based on {len(news_data.get('news', []))} news articles. Overall sentiment: {news_data.get('sentiment', {}).get('overall', 'neutral')}",
                'key_developments': [],
                'sentiment_analysis': news_data.get('sentiment', {}),
                'risks': [],
                'opportunities': []
            }
    
    def _prepare_news_summary(self, news_data: Dict[str, Any]) -> str:
        """Prepare news data for LLM input"""
        sentiment = news_data.get('sentiment', {})
        news_items = news_data.get('news', [])[:10]  # Limit to 10 articles
        
        summary = f"""
Total News Articles: {len(news_data.get('news', []))}
Overall Sentiment: {sentiment.get('overall', 'neutral')}
Sentiment Breakdown: Positive: {sentiment.get('positive_count', 0)}, Negative: {sentiment.get('negative_count', 0)}, Neutral: {sentiment.get('neutral_count', 0)}

Recent Headlines:
"""
        for item in news_items:
            summary += f"- {item.get('title', 'No title')} ({item.get('source', 'Unknown')})\n"
            if item.get('snippet'):
                summary += f"  Summary: {item.get('snippet')[:150]}...\n"
        
        return summary
    
    def _extract_developments(self, text: str) -> list:
        """Extract key developments from LLM response"""
        # Simple extraction - in production, use better parsing
        lines = text.split('\n')
        developments = []
        for line in lines:
            if any(kw in line.lower() for kw in ['develop', 'announc', 'launch', 'report', 'event']):
                if line.strip() and len(line) > 20:
                    developments.append(line.strip())
        return developments[:5]
    
    def _extract_risks(self, text: str) -> list:
        """Extract risks from LLM response"""
        lines = text.split('\n')
        risks = []
        risk_section = False
        for line in lines:
            if 'risk' in line.lower() or 'concern' in line.lower():
                risk_section = True
            if risk_section and line.strip() and len(line) > 15:
                risks.append(line.strip())
            if risk_section and len(risks) >= 5:
                break
        return risks
    
    def _extract_opportunities(self, text: str) -> list:
        """Extract opportunities from LLM response"""
        lines = text.split('\n')
        opportunities = []
        opp_section = False
        for line in lines:
            if any(kw in line.lower() for kw in ['opportunity', 'catalyst', 'potential', 'growth']):
                opp_section = True
            if opp_section and line.strip() and len(line) > 15:
                opportunities.append(line.strip())
            if opp_section and len(opportunities) >= 5:
                break
        return opportunities