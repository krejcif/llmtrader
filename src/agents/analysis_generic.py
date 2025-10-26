"""Generic Analysis - Works with any timeframe configuration"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.indicators import calculate_all_indicators, analyze_orderbook, detect_trend_reversal
from utils.momentum_analysis import (
    analyze_recent_candles,
    analyze_volume_momentum,
    find_immediate_levels,
    calculate_momentum_score,
    analyze_current_candle
)


def analyze_market_generic(state: TradingState, strategy_name: str,
                           tf_higher: str, tf_lower: str) -> TradingState:
    """
    Generic market analysis for any timeframe pair
    
    Args:
        state: Current trading state
        strategy_name: Name of strategy (for state keys)
        tf_higher: Higher timeframe (e.g., '1h', '15m')
        tf_lower: Lower timeframe (e.g., '15m', '5m')
        
    Returns:
        Updated state with analysis at state[f'analysis_{strategy_name}']
    """
    market_data_key = f"market_data_{strategy_name}"
    analysis_key = f"analysis_{strategy_name}"
    
    print(f"\n🔬 [{strategy_name.upper()}] Analyzing market data ({tf_higher}/{tf_lower})...")
    
    try:
        # Check if we have market data
        if not state.get(market_data_key):
            print(f"❌ Cannot analyze - no market data for {strategy_name}")
            state[analysis_key] = None
            return state
        
        market_data = state[market_data_key]
        
        # Get data for both timeframes
        candles_higher = market_data['timeframes'][tf_higher]
        candles_lower = market_data['timeframes'][tf_lower]
        
        # Calculate technical indicators for both timeframes
        print(f"   Analyzing {tf_higher} (trend)...")
        indicators_higher = calculate_all_indicators(candles_higher)
        
        print(f"   Analyzing {tf_lower} (entry)...")
        indicators_lower = calculate_all_indicators(candles_lower)
        
        # Combine indicators
        indicators = {
            "higher_tf": {
                "timeframe": tf_higher,
                "indicators": indicators_higher
            },
            "lower_tf": {
                "timeframe": tf_lower,
                "indicators": indicators_lower
            }
        }
        
        # Analyze orderbook
        print(f"   Analyzing orderbook...")
        orderbook_analysis = analyze_orderbook(market_data['orderbook'], market_data['current_price'])
        
        # Market sentiment from funding + volume + orderbook
        funding_rate = market_data['funding_rate']
        
        if funding_rate > 0.0001:
            funding_sentiment = "bullish_extreme"
        elif funding_rate > 0:
            funding_sentiment = "bullish"
        elif funding_rate < -0.0001:
            funding_sentiment = "bearish_extreme"
        else:
            funding_sentiment = "bearish"
        
        # Volume momentum (from lower TF)
        volume_trend = indicators_lower['volume']['trend']
        volume_ratio = indicators_lower['volume']['current_vs_avg']
        
        if volume_ratio > 1.5:
            volume_momentum = "surging"
        elif volume_ratio > 1.2:
            volume_momentum = "increasing"
        elif volume_ratio < 0.8:
            volume_momentum = "weak"
        else:
            volume_momentum = "normal"
        
        # Orderbook pressure
        orderbook_pressure = orderbook_analysis['imbalance']['pressure']
        
        sentiment = {
            "funding_rate": funding_rate,
            "funding_sentiment": funding_sentiment,
            "volume_momentum": volume_momentum,
            "orderbook_pressure": orderbook_pressure
        }
        
        # Detect trend reversal (lower timeframe vs higher timeframe)
        print(f"   Detecting trend reversal...")
        reversal_analysis = detect_trend_reversal(indicators_lower, indicators_higher, market_data['current_price'])
        
        # Entry quality assessment
        rsi_lower = indicators_lower['rsi']['value']
        macd_signal = indicators_lower['macd']['signal']
        bb_position = indicators_lower['bollinger_bands']['position']
        
        entry_quality = "unknown"
        if (rsi_lower < 30 and macd_signal == 'bullish') or (rsi_lower > 70 and macd_signal == 'bearish'):
            entry_quality = "high"
        elif (rsi_lower < 40 and macd_signal == 'bullish') or (rsi_lower > 60 and macd_signal == 'bearish'):
            entry_quality = "medium"
        else:
            entry_quality = "low"
        
        # Timeframe confluence
        ema_higher_trend = indicators_higher['ema']['trend']
        ema_lower_trend = indicators_lower['ema']['trend']
        
        if ema_higher_trend == ema_lower_trend:
            confluence = "aligned"
        else:
            confluence = "divergent"
        
        # MOMENTUM ANALYSIS (for intraday/5m strategies)
        momentum_data = None
        if tf_lower == "5m":
            print(f"   Computing momentum analysis for 5m timeframe...")
            momentum_data = {
                'recent_candles': analyze_recent_candles(candles_lower, n=5),
                'volume_momentum': analyze_volume_momentum(candles_lower),
                'immediate_levels': find_immediate_levels(candles_lower, lookback=30),
                'momentum_score': calculate_momentum_score(candles_lower, indicators_lower['rsi_7']['value']),
                'current_candle': analyze_current_candle(candles_lower)
            }
            print(f"   ⚡ Momentum score: {momentum_data['momentum_score']['score']}/10 ({momentum_data['momentum_score']['interpretation']})")
        
        # Build analysis result
        analysis = {
            "indicators": indicators,
            "orderbook": orderbook_analysis,
            "sentiment": sentiment,
            "reversal": reversal_analysis,
            "entry_quality": entry_quality,
            "confluence": confluence,
            "momentum": momentum_data  # Will be None for non-5m strategies
        }
        
        state[analysis_key] = analysis
        
        print(f"✅ [{strategy_name.upper()}] Analysis complete:")
        print(f"   Entry quality: {entry_quality}")
        print(f"   Timeframe confluence: {confluence}")
        print(f"   Reversal detected: {reversal_analysis.get('reversal_detected', False)}")
        
    except Exception as e:
        error_msg = f"Error analyzing data for {strategy_name}: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        state[analysis_key] = None
    
    return state

