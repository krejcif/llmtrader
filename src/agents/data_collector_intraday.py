"""Data Collector Agent - Intraday (5m/15m timeframes)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.binance_client import BinanceClient
import config


def collect_market_data_intraday(state: TradingState) -> TradingState:
    """
    Collect intraday market data from Binance (5m/15m timeframes)
    
    Args:
        state: Current trading state
        
    Returns:
        Updated state with intraday market data
    """
    print(f"📊 [INTRADAY] Collecting market data for {state['symbol']}...")
    print(f"   Timeframes: 15m (trend), 5m (entry)")
    
    try:
        # Initialize Binance client
        client = BinanceClient(
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_API_SECRET
        )
        
        # Fetch intraday data with 5m/15m timeframes
        market_data_intraday = client.get_multi_timeframe_data(
            symbol=state['symbol'],
            timeframes=['15m', '5m'],  # Higher TF first, then lower TF
            limit=config.CANDLES_LIMIT
        )
        
        print(f"✅ [INTRADAY] Market data collected:")
        print(f"   Current price: ${market_data_intraday['current_price']}")
        print(f"   Funding rate: {market_data_intraday['funding_rate']:.6f}")
        print(f"   15m: {len(market_data_intraday['timeframes']['15m'])} bars")
        print(f"   5m: {len(market_data_intraday['timeframes']['5m'])} bars")
        print(f"   Orderbook: {len(market_data_intraday['orderbook']['bids'])} bids, {len(market_data_intraday['orderbook']['asks'])} asks")
        
        state['market_data_intraday'] = market_data_intraday
        
    except Exception as e:
        error_msg = f"Error collecting intraday market data: {str(e)}"
        print(f"❌ {error_msg}")
        state['market_data_intraday'] = None
    
    return state

