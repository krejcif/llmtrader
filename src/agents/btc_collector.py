"""BTC Collector Agent - Bitcoin as crypto market indicator"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.binance_client import BinanceClient


def collect_btc_data(state: TradingState) -> TradingState:
    """
    Collect BTC/USDT data for crypto market correlation
    
    Args:
        state: Current trading state
        
    Returns:
        Updated state with BTC data
    """
    print(f"\n₿ Collecting BTC data (crypto market indicator)...")
    
    try:
        client = BinanceClient()
        
        # Get BTC current price
        btc_price = client.get_current_price('BTCUSDT')
        
        # Get 15m and 1h candles for trend (better macro resolution)
        btc_15m = client.get_klines('BTCUSDT', '15m', 100)
        btc_1h = client.get_klines('BTCUSDT', '1h', 100)
        
        # Calculate 15m trend
        btc_sma_20_15m = btc_15m['close'].rolling(20).mean().iloc[-1]
        btc_sma_50_15m = btc_15m['close'].rolling(50).mean().iloc[-1]
        
        if btc_price > btc_sma_20_15m > btc_sma_50_15m:
            btc_trend_15m = "bullish"
        elif btc_price < btc_sma_20_15m < btc_sma_50_15m:
            btc_trend_15m = "bearish"
        else:
            btc_trend_15m = "neutral"
        
        # Calculate 1h trend
        btc_sma_20_1h = btc_1h['close'].rolling(20).mean().iloc[-1]
        
        if btc_price > btc_sma_20_1h:
            btc_trend_1h = "bullish"
        else:
            btc_trend_1h = "bearish"
        
        # Recent changes (from 15m data)
        btc_15m_ago = btc_15m['close'].iloc[-2] if len(btc_15m) >= 2 else btc_price
        btc_1h_ago = btc_15m['close'].iloc[-5] if len(btc_15m) >= 5 else btc_price  # ~1h ago (4x15m)
        btc_4h_ago = btc_15m['close'].iloc[-17] if len(btc_15m) >= 17 else btc_price  # ~4h ago (16x15m)
        
        change_15m = ((btc_price - btc_15m_ago) / btc_15m_ago) * 100
        change_1h = ((btc_price - btc_1h_ago) / btc_1h_ago) * 100
        change_4h = ((btc_price - btc_4h_ago) / btc_4h_ago) * 100
        
        btc_analysis = {
            "symbol": "BTCUSDT",
            "current_price": round(btc_price, 2),
            "trend_15m": btc_trend_15m,
            "trend_1h": btc_trend_1h,
            "change_15m": round(change_15m, 2),
            "change_1h": round(change_1h, 2),
            "change_4h": round(change_4h, 2),
            "sma_20_15m": round(btc_sma_20_15m, 2),
            "sma_20_1h": round(btc_sma_20_1h, 2),
            "fresh": True,
            "data_age_minutes": 0  # Real-time from Binance
        }
        
        print(f"✅ BTC data collected (FRESH 24/7):")
        print(f"   Price: ${btc_price:,.2f}")
        print(f"   Trend 15m: {btc_trend_15m} | 1h: {btc_trend_1h}")
        print(f"   Changes: 15m {change_15m:+.2f}%, 1h {change_1h:+.2f}%, 4h {change_4h:+.2f}%")
        
        return {"btc_data": btc_analysis}
        
    except Exception as e:
        print(f"❌ Error collecting BTC data: {e}")
        return {"btc_data": None}

