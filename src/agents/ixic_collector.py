"""IXIC Data Collector Agent - Fetches Nasdaq index data from Yahoo Finance"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
import yfinance as yf
import pandas as pd


def collect_ixic_data(state: TradingState) -> TradingState:
    """
    Collect IXIC (Nasdaq) data - only when fresh (market open)
    
    Args:
        state: Current trading state
        
    Returns:
        Updated state with IXIC data (or None if stale)
    """
    print(f"\n📈 Collecting IXIC (Nasdaq) data...")
    
    try:
        # Get IXIC data (Nasdaq Composite)
        ticker = yf.Ticker("^IXIC")
        
        # Get 15m data (last 5 days worth)
        ixic_data = ticker.history(period="5d", interval="15m")
        
        if ixic_data.empty:
            print("⚠️  No IXIC data available")
            return {"ixic_data": None}
        
        # Calculate basic indicators on IXIC
        current_price = ixic_data['Close'].iloc[-1]
        
        # Simple trend
        sma_20 = ixic_data['Close'].rolling(20).mean().iloc[-1]
        sma_50 = ixic_data['Close'].rolling(50).mean().iloc[-1] if len(ixic_data) >= 50 else sma_20
        
        if current_price > sma_20 > sma_50:
            ixic_trend = "bullish"
        elif current_price < sma_20 < sma_50:
            ixic_trend = "bearish"
        else:
            ixic_trend = "neutral"
        
        # Recent change (last hour = 4 candles)
        if len(ixic_data) >= 4:
            price_1h_ago = ixic_data['Close'].iloc[-4]
            change_1h = ((current_price - price_1h_ago) / price_1h_ago) * 100
        else:
            change_1h = 0
        
        # Recent change (last 4h = 16 candles)
        if len(ixic_data) >= 16:
            price_4h_ago = ixic_data['Close'].iloc[-16]
            change_4h = ((current_price - price_4h_ago) / price_4h_ago) * 100
        else:
            change_4h = 0
        
        # Check data freshness
        from datetime import datetime, timedelta
        latest_time = ixic_data.index[-1].to_pydatetime().replace(tzinfo=None)
        now = datetime.now()
        data_age = (now - latest_time).total_seconds() / 60  # minutes
        
        # Consider fresh if < 2 hours old
        is_fresh = data_age < 120
        
        ixic_analysis = {
            "current_price": round(current_price, 2),
            "trend": ixic_trend,
            "change_1h": round(change_1h, 2),
            "change_4h": round(change_4h, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2) if len(ixic_data) >= 50 else None,
            "candles_available": len(ixic_data),
            "fresh": is_fresh,
            "data_age_minutes": int(data_age),
            "latest_time": latest_time.isoformat()
        }
        
        if is_fresh:
            print(f"✅ IXIC data collected (FRESH - {int(data_age)}min old):")
            print(f"   Price: {current_price:.2f}")
            print(f"   Trend: {ixic_trend}")
            print(f"   1h change: {change_1h:+.2f}%")
            print(f"   4h change: {change_4h:+.2f}%")
        else:
            print(f"⚠️  IXIC data STALE ({int(data_age/60)}h old - market closed)")
            print(f"   Last price: {current_price:.2f} from {latest_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Using with caution or skipping in analysis")
        
        return {"ixic_data": ixic_analysis}
        
    except Exception as e:
        print(f"❌ Error collecting IXIC data: {e}")
        return {"ixic_data": None}

