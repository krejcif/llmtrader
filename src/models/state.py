"""State definition for LangGraph workflow"""
from typing import TypedDict, Optional, Dict


class TradingState(TypedDict):
    """State object for the trading analysis workflow"""
    
    symbol: str
    market_data: Optional[Dict]
    news_data: Optional[Dict]
    btc_data: Optional[Dict]
    ixic_data: Optional[Dict]
    analysis: Optional[Dict]
    recommendation_structured: Optional[Dict]
    recommendation_minimal: Optional[Dict]
    recommendation_macro: Optional[Dict]
    recommendation_intraday: Optional[Dict]
    recommendation_intraday2: Optional[Dict]
    trade_execution: Optional[Dict]
    error: Optional[str]

