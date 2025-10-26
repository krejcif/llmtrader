"""Strategy Configuration System - Flexible multi-strategy setup"""

from agents.decision_minimal import make_decision_minimal
from agents.decision_minimalbtc import make_decision_minimalbtc
from agents.decision_macro import make_decision_macro
from agents.decision_intraday import make_decision_intraday
from agents.decision_example import make_decision_example


class StrategyConfig:
    """Configuration for a trading strategy"""
    
    def __init__(self, name: str, decision_func, timeframe_higher: str, 
                 timeframe_lower: str, interval_minutes: int, enabled: bool = True):
        """
        Initialize strategy configuration
        
        Args:
            name: Strategy name (e.g., 'minimal', 'intraday')
            decision_func: Decision making function
            timeframe_higher: Higher timeframe for trend (e.g., '1h', '15m')
            timeframe_lower: Lower timeframe for entry (e.g., '15m', '5m')
            interval_minutes: How often to run this strategy in minutes
            enabled: Whether strategy is active
        """
        self.name = name
        self.decision_func = decision_func
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
        return (f"StrategyConfig(name={self.name}, tf={self.timeframe_higher}/{self.timeframe_lower}, "
                f"interval={self.interval_minutes}min, enabled={self.enabled})")


# =============================================================================
# STRATEGY REGISTRY - Add your strategies here!
# =============================================================================

STRATEGIES = [
    # Minimal strategy - 1h/15m, runs every 15 min
    StrategyConfig(
        name="minimal",
        decision_func=make_decision_minimal,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # MinimalBTC strategy - 1h/15m, runs every 15 min
    StrategyConfig(
        name="minimalbtc",
        decision_func=make_decision_minimalbtc,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # Macro strategy - 4h/1h (bigger picture), runs every 15 min
    StrategyConfig(
        name="macro",
        decision_func=make_decision_macro,
        timeframe_higher="4h",
        timeframe_lower="1h",
        interval_minutes=15,
        enabled=True
    ),
    
    # Intraday strategy - 15m/5m, runs every 5 min
    StrategyConfig(
        name="intraday",
        decision_func=make_decision_intraday,
        timeframe_higher="15m",
        timeframe_lower="5m",
        interval_minutes=5,
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
    
    # Add more strategies here!
    # Example: Ultra-fast scalper (1m/5m, every 1 minute)
    # StrategyConfig(
    #     name="scalper",
    #     decision_func=make_decision_scalper,
    #     timeframe_higher="5m",
    #     timeframe_lower="1m",
    #     interval_minutes=1,
    #     enabled=False
    # ),
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

