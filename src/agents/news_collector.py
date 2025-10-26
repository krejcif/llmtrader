"""News Collector Agent - Fetches stock market news"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
import config
import requests


def collect_stock_news(state: TradingState) -> TradingState:
    """
    Collect general stock market news for macro analysis
    
    Args:
        state: Current trading state
        
    Returns:
        Updated state with news data
    """
    print(f"\n📰 Collecting stock market news...")
    
    try:
        if not config.STOCKNEWS_API_KEY:
            print("⚠️  STOCKNEWS_API_KEY not configured, skipping news")
            return {"news_data": None}
        
        # StockNews API endpoint
        url = "https://stocknewsapi.com/api/v1/category"
        
        params = {
            "section": "general",  # General market news
            "items": 10,
            "token": config.STOCKNEWS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        news_data = response.json()
        
        # Extract relevant info
        news_items = []
        if 'data' in news_data:
            for item in news_data['data'][:10]:
                news_items.append({
                    "title": item.get('title', ''),
                    "text": item.get('text', '')[:200],  # First 200 chars
                    "date": item.get('date', ''),
                    "sentiment": item.get('sentiment', 'neutral'),
                    "source": item.get('source_name', ''),
                    "tickers": item.get('tickers', [])
                })
        
        print(f"✅ Collected {len(news_items)} news articles")
        if news_items:
            print(f"   Latest: {news_items[0]['title'][:60]}...")
        
        return {"news_data": {"items": news_items, "count": len(news_items)}}
        
    except Exception as e:
        print(f"❌ Error collecting news: {e}")
        return {"news_data": None}

