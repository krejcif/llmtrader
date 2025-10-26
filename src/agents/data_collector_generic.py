"""Generic Data Collector - Works with any timeframe configuration"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.binance_client import BinanceClient
import config


def collect_market_data_generic(state: TradingState, strategy_name: str, 
                                tf_higher: str, tf_lower: str) -> TradingState:
    """
    Generic market data collector for any timeframe pair
    
    Args:
        state: Current trading state
        strategy_name: Name of strategy (for state key)
        tf_higher: Higher timeframe (e.g., '1h', '15m')
        tf_lower: Lower timeframe (e.g., '15m', '5m')
        
    Returns:
        Updated state with market data at state[f'market_data_{strategy_name}']
    """
    state_key = f"market_data_{strategy_name}"
    
    print(f"📊 [{strategy_name.upper()}] Collecting market data for {state['symbol']}...")
    print(f"   Timeframes: {tf_higher} (trend), {tf_lower} (entry)")
    
    try:
        # Initialize Binance client
        client = BinanceClient(
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_API_SECRET
        )
        
        # Fetch multi-timeframe market data
        market_data = client.get_multi_timeframe_data(
            symbol=state['symbol'],
            timeframes=[tf_higher, tf_lower],
            limit=config.CANDLES_LIMIT
        )
        
        print(f"✅ [{strategy_name.upper()}] Market data collected:")
        print(f"   Current price: ${market_data['current_price']}")
        print(f"   Funding rate: {market_data['funding_rate']:.6f}")
        print(f"   {tf_higher}: {len(market_data['timeframes'][tf_higher])} bars")
        print(f"   {tf_lower}: {len(market_data['timeframes'][tf_lower])} bars")
        print(f"   Orderbook: {len(market_data['orderbook']['bids'])} bids, {len(market_data['orderbook']['asks'])} asks")
        
        state[state_key] = market_data
        
    except Exception as e:
        error_msg = f"Error collecting market data for {strategy_name}: {str(e)}"
        print(f"❌ {error_msg}")
        state[state_key] = None
    
    return state

