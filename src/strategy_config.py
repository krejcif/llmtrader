"""Strategy Configuration System - Flexible multi-strategy setup"""

from agents.decision_sol import make_decision_sol
from agents.decision_sol_fast import make_decision_sol_fast
from agents.decision_eth import make_decision_eth
from agents.decision_eth_fast import make_decision_eth_fast
from agents.decision_doge import make_decision_doge
from agents.decision_doge_fast import make_decision_doge_fast
from agents.decision_xrp import make_decision_xrp
from agents.decision_xrp_fast import make_decision_xrp_fast
from agents.decision_example import make_decision_example

# Analysis functions
from agents.analysis_generic import analyze_market_generic
from agents.analysis_sol_fast import analyze_market_sol_fast
from agents.analysis_eth_fast import analyze_market_eth_fast
from agents.analysis_doge_fast import analyze_market_doge_fast
from agents.analysis_xrp_fast import analyze_market_xrp_fast

# Import config for default symbol
import config


class StrategyConfig:
    """Configuration for a trading strategy"""
    
    def __init__(self, name: str, decision_func, timeframe_higher: str, 
                 timeframe_lower: str, interval_minutes: int, enabled: bool = True,
                 analysis_func=None, symbol: str = None):
        """
        Initialize strategy configuration
        
        Args:
            name: Strategy name (e.g., 'minimal', 'intraday')
            decision_func: Decision making function
            timeframe_higher: Higher timeframe for trend (e.g., '1h', '15m')
            timeframe_lower: Lower timeframe for entry (e.g., '15m', '5m')
            interval_minutes: How often to run this strategy in minutes
            enabled: Whether strategy is active
            analysis_func: Optional custom analysis function (defaults to analyze_market_generic)
            symbol: Trading symbol (e.g., 'SOLUSDT', 'BTCUSDT'). Defaults to config.SYMBOL
        """
        self.name = name
        self.symbol = symbol if symbol is not None else config.SYMBOL
        self.decision_func = decision_func
        self.analysis_func = analysis_func if analysis_func else analyze_market_generic
        self.timeframe_higher = timeframe_higher
        self.timeframe_lower = timeframe_lower
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self.enabled = enabled
        
        # State keys for this strategy
        self.market_data_key = f"market_data_{name}"
        self.analysis_key = f"analysis_{name}"
        self.recommendation_key = f"recommendation_{name}"
    
    def __repr__(self):
        return (f"StrategyConfig(name={self.name}, symbol={self.symbol}, tf={self.timeframe_higher}/{self.timeframe_lower}, "
                f"interval={self.interval_minutes}min, enabled={self.enabled})")


# =============================================================================
# STRATEGY REGISTRY - Add your strategies here!
# =============================================================================

STRATEGIES = [
    # Sol strategy - 1h/15m, runs every 15 min (EMA 20/50 for SOLUSDT)
    StrategyConfig(
        name="sol",
        decision_func=make_decision_sol,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # Sol Fast strategy - 1h/15m, runs every 15 min (EMA 7/25 for SOLUSDT - faster response)
    StrategyConfig(
        name="sol_fast",
        decision_func=make_decision_sol_fast,
        analysis_func=analyze_market_sol_fast,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # ETH strategy - 1h/15m, runs every 15 min (EMA 20/50 for ETHUSDT)
    StrategyConfig(
        name="eth",
        symbol="ETHUSDT",
        decision_func=make_decision_eth,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # ETH Fast strategy - 1h/15m, runs every 15 min (EMA 7/25 for ETHUSDT)
    StrategyConfig(
        name="eth_fast",
        symbol="ETHUSDT",
        decision_func=make_decision_eth_fast,
        analysis_func=analyze_market_eth_fast,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # DOGE strategy - 1h/15m, runs every 15 min (EMA 20/50 for DOGEUSDT)
    StrategyConfig(
        name="doge",
        symbol="DOGEUSDT",
        decision_func=make_decision_doge,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # DOGE Fast strategy - 1h/15m, runs every 15 min (EMA 7/25 for DOGEUSDT - faster response)
    StrategyConfig(
        name="doge_fast",
        symbol="DOGEUSDT",
        decision_func=make_decision_doge_fast,
        analysis_func=analyze_market_doge_fast,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # XRP strategy - 1h/15m, runs every 15 min (EMA 20/50 for XRPUSDT)
    StrategyConfig(
        name="xrp",
        symbol="XRPUSDT",
        decision_func=make_decision_xrp,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # XRP Fast strategy - 1h/15m, runs every 15 min (EMA 7/25 for XRPUSDT - faster response)
    StrategyConfig(
        name="xrp_fast",
        symbol="XRPUSDT",
        decision_func=make_decision_xrp_fast,
        analysis_func=analyze_market_xrp_fast,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # Example strategy (DISABLED) - Use as template for new strategies!
    # To activate: change enabled=False to enabled=True
    StrategyConfig(
        name="example",
        decision_func=make_decision_example,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=False  # DISABLED - template only
    ),
]


def get_active_strategies():
    """Get all enabled strategies"""
    return [s for s in STRATEGIES if s.enabled]


def get_strategy_by_name(name: str):
    """Get strategy config by name"""
    for strategy in STRATEGIES:
        if strategy.name == name:
            return strategy
    return None


def get_strategies_by_interval(interval_minutes: int):
    """Get all strategies that should run at this interval"""
    return [s for s in get_active_strategies() if s.interval_minutes == interval_minutes]


def get_all_intervals():
    """Get list of all unique intervals from active strategies"""
    intervals = set(s.interval_minutes for s in get_active_strategies())
    return sorted(intervals)


def get_min_interval():
    """Get shortest interval (for main bot loop)"""
    intervals = get_all_intervals()
    return min(intervals) if intervals else 15

