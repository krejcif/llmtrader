"""State definition for dynamic multi-strategy trading system"""
from typing import TypedDict, Optional, Dict, Any


class TradingState(TypedDict, total=False):
    """
    State object for the trading workflow
    
    Dynamic keys are created at runtime:
    - market_data_{strategy_name}: Market data for each strategy
    - analysis_{strategy_name}: Analysis results for each strategy
    - recommendation_{strategy_name}: Recommendations for each strategy
    
    Example dynamic keys:
    - market_data_sol, analysis_sol, recommendation_sol
    - market_data_eth_fast, analysis_eth_fast, recommendation_eth_fast
    """
    
    # Core state fields (always present)
    symbol: str
    error: Optional[str]
    
    # Shared data (collected once per cycle)
    market_data: Optional[Dict]  # Generic market data
    news_data: Optional[Dict]    # Stock news
    btc_data: Optional[Dict]     # Bitcoin data
    ixic_data: Optional[Dict]    # NASDAQ data
    
    # Generic fields (may be strategy-specific or shared)
    analysis: Optional[Dict]
    
    # Trade execution results
    trade_execution: Optional[Dict]
    
    # NOTE: Strategy-specific fields are added dynamically:
    # market_data_{strategy}, analysis_{strategy}, recommendation_{strategy}

