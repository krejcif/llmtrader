"""Data Collector Agent - Fetches market data from Binance"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.binance_client import BinanceClient
import config


def collect_market_data(state: TradingState) -> TradingState:
    """
    Collect market data from Binance Futures API (multi-timeframe)
    
    Args:
        state: Current trading state
        
    Returns:
        Updated state with market data
    """
    print(f"📊 Collecting multi-timeframe market data for {state['symbol']}...")
    print(f"   Timeframes: {config.TIMEFRAME_HIGHER} (trend), {config.TIMEFRAME_LOWER} (entry)")
    
    try:
        # Initialize Binance client
        client = BinanceClient(
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_API_SECRET
        )
        
        # Fetch multi-timeframe market data
        market_data = client.get_multi_timeframe_data(
            symbol=state['symbol'],
            timeframes=[config.TIMEFRAME_HIGHER, config.TIMEFRAME_LOWER],
            limit=config.CANDLES_LIMIT
        )
        
        print(f"✅ Market data collected:")
        print(f"   Current price: ${market_data['current_price']}")
        print(f"   Funding rate: {market_data['funding_rate']:.6f}")
        print(f"   {config.TIMEFRAME_HIGHER}: {len(market_data['timeframes'][config.TIMEFRAME_HIGHER])} bars")
        print(f"   {config.TIMEFRAME_LOWER}: {len(market_data['timeframes'][config.TIMEFRAME_LOWER])} bars")
        print(f"   Orderbook: {len(market_data['orderbook']['bids'])} bids, {len(market_data['orderbook']['asks'])} asks")
        
        state['market_data'] = market_data
        state['error'] = None
        
    except Exception as e:
        error_msg = f"Error collecting market data: {str(e)}"
        print(f"❌ {error_msg}")
        state['error'] = error_msg
        state['market_data'] = None
    
    return state

