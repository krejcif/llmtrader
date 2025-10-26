"""Analysis Agent - Intraday (5m/15m timeframes)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.indicators import calculate_all_indicators, analyze_orderbook, detect_trend_reversal


def analyze_market_intraday(state: TradingState) -> TradingState:
    """
    Analyze intraday market data with 5m/15m timeframes
    
    Args:
        state: Current trading state with intraday market data
        
    Returns:
        Updated state with intraday analysis
    """
    print(f"\n🔬 [INTRADAY] Analyzing market data (5m/15m)...")
    
    try:
        # Check if we have intraday market data
        if not state.get('market_data_intraday'):
            print("❌ Cannot analyze - no intraday market data")
            return state
        
        market_data_intraday = state['market_data_intraday']
        
        # Get data for both timeframes
        tf_higher = '15m'
        tf_lower = '5m'
        
        candles_higher = market_data_intraday['timeframes'][tf_higher]
        candles_lower = market_data_intraday['timeframes'][tf_lower]
        
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
        orderbook_analysis = analyze_orderbook(market_data_intraday['orderbook'])
        
        # Market sentiment from funding + volume + orderbook
        funding_rate = market_data_intraday['funding_rate']
        
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
        
        # Detect trend reversal (lower timeframe)
        print(f"   Detecting trend reversal...")
        reversal_analysis = detect_trend_reversal(candles_lower, indicators_lower)
        
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
        
        # Build analysis result
        analysis = {
            "indicators": indicators,
            "orderbook": orderbook_analysis,
            "sentiment": sentiment,
            "reversal": reversal_analysis,
            "entry_quality": entry_quality,
            "confluence": confluence
        }
        
        state['analysis_intraday'] = analysis
        
        print(f"✅ [INTRADAY] Analysis complete:")
        print(f"   Entry quality: {entry_quality}")
        print(f"   Timeframe confluence: {confluence}")
        print(f"   Reversal detected: {reversal_analysis.get('reversal_detected', False)}")
        
    except Exception as e:
        error_msg = f"Error analyzing intraday data: {str(e)}"
        print(f"❌ {error_msg}")
        state['analysis_intraday'] = None
    
    return state

