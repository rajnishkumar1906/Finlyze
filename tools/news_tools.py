# tools/news_tools.py
from duckduckgo_search import DDGS
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_news(ticker: str, company_name: str = "", max_results: int = 10) -> List[Dict[str, str]]:
    """
    Search for news using DuckDuckGo
    """
    try:
        logger.info(f"Searching news for {ticker}")
        
        # Create search queries
        queries = [
            f"{ticker} stock news",
            f"{ticker} earnings",
            f"{ticker} market sentiment"
        ]
        
        if company_name:
            queries.append(f"{company_name} stock news")
        
        all_news = []
        seen_titles = set()
        
        with DDGS() as ddgs:
            for query in queries:
                try:
                    # Search for news from last 7 days
                    results = ddgs.news(
                        query,
                        max_results=max_results // len(queries),
                        timelimit="7d"  # Last 7 days
                    )
                    
                    for result in results:
                        # Deduplicate by title
                        title = result.get('title', '')
                        if title and title not in seen_titles:
                            seen_titles.add(title)
                            
                            # Extract date
                            date = result.get('date', '')
                            if date:
                                try:
                                    # Try to parse date
                                    if isinstance(date, str):
                                        # Handle relative dates like "1 hour ago"
                                        if 'hour' in date or 'minute' in date:
                                            date = datetime.now().strftime("%Y-%m-%d")
                                        else:
                                            # Try to extract YYYY-MM-DD
                                            match = re.search(r'\d{4}-\d{2}-\d{2}', date)
                                            if match:
                                                date = match.group()
                                except:
                                    pass
                            
                            news_item = {
                                'title': title,
                                'link': result.get('link', ''),
                                'snippet': result.get('body', '') or result.get('snippet', ''),
                                'source': result.get('source', 'Unknown'),
                                'date': date,
                                'query': query
                            }
                            all_news.append(news_item)
                            
                except Exception as e:
                    logger.warning(f"Error searching query '{query}': {str(e)}")
                    continue
        
        # Sort by date (most recent first) and limit results
        all_news.sort(key=lambda x: x.get('date', ''), reverse=True)
        all_news = all_news[:max_results]
        
        logger.info(f"Found {len(all_news)} news items for {ticker}")
        return all_news
        
    except Exception as e:
        logger.error(f"Error searching news: {str(e)}")
        return []

def analyze_sentiment(news_items: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Simple sentiment analysis based on keywords
    Note: In production, you'd use a proper sentiment model
    """
    if not news_items:
        return {
            'overall': 'neutral',
            'score': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0
        }
    
    positive_keywords = [
        'up', 'rise', 'gain', 'positive', 'bull', 'growth', 'beat', 'upgrade',
        'upgraded', 'outperform', 'strong', 'record', 'high', 'rally', 'surge',
        'jump', 'soar', 'profit', 'win', 'success', 'opportunity', 'breakthrough'
    ]
    
    negative_keywords = [
        'down', 'fall', 'drop', 'negative', 'bear', 'decline', 'miss', 'downgrade',
        'downgraded', 'underperform', 'weak', 'low', 'crash', 'plunge', 'slump',
        'loss', 'risk', 'warning', 'concern', 'investigation', 'lawsuit', 'probe'
    ]
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_score = 0
    
    for item in news_items:
        text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
        
        # Count positive keywords
        pos_matches = sum(1 for kw in positive_keywords if kw in text)
        neg_matches = sum(1 for kw in negative_keywords if kw in text)
        
        # Determine sentiment
        if pos_matches > neg_matches:
            sentiment = 'positive'
            positive_count += 1
            score = min(pos_matches / (pos_matches + neg_matches + 1), 1.0)
        elif neg_matches > pos_matches:
            sentiment = 'negative'
            negative_count += 1
            score = -min(neg_matches / (pos_matches + neg_matches + 1), 1.0)
        else:
            sentiment = 'neutral'
            neutral_count += 1
            score = 0
        
        total_score += score
        item['sentiment'] = sentiment
    
    # Calculate overall metrics
    total_items = len(news_items)
    avg_score = total_score / total_items if total_items > 0 else 0
    
    # Determine overall sentiment
    if avg_score > 0.2:
        overall = 'positive'
    elif avg_score < -0.2:
        overall = 'negative'
    else:
        overall = 'neutral'
    
    return {
        'overall': overall,
        'score': avg_score,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'total_items': total_items,
        'positive_percentage': (positive_count / total_items) * 100 if total_items > 0 else 0,
        'negative_percentage': (negative_count / total_items) * 100 if total_items > 0 else 0,
        'neutral_percentage': (neutral_count / total_items) * 100 if total_items > 0 else 0
    }

def search_market_news(query: str = "stock market", max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search for broader market news
    """
    try:
        with DDGS() as ddgs:
            results = ddgs.news(
                query,
                max_results=max_results,
                timelimit="2d"
            )
            
            news = []
            for result in results:
                news.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('body', '') or result.get('snippet', ''),
                    'source': result.get('source', 'Unknown'),
                    'date': result.get('date', '')
                })
            
            return news
            
    except Exception as e:
        logger.error(f"Error searching market news: {str(e)}")
        return []

def get_ticker_news_with_sentiment(ticker: str, company_name: str = "") -> Dict[str, Any]:
    """
    Main function to get news with sentiment analysis
    """
    # Search for news
    news_items = search_news(ticker, company_name)
    
    if not news_items:
        return {
            'news': [],
            'sentiment': {
                'overall': 'neutral',
                'score': 0,
                'message': 'No recent news found'
            }
        }
    
    # Analyze sentiment
    sentiment = analyze_sentiment(news_items)
    
    # Add market context
    market_news = search_market_news(max_results=3)
    
    return {
        'news': news_items,
        'market_news': market_news,
        'sentiment': sentiment,
        'total_articles': len(news_items),
        'last_updated': datetime.now().isoformat()
    }