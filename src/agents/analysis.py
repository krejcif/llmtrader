"""Analysis Agent - Calculates technical indicators and sentiment"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.indicators import calculate_all_indicators, analyze_orderbook, detect_trend_reversal
import config


def analyze_market(state: TradingState) -> TradingState:
    """
    Analyze market data with technical indicators and sentiment
    
    Args:
        state: Current trading state with market data
        
    Returns:
        Updated state with analysis
    """
    print(f"\n🔬 Analyzing market data...")
    
    try:
        # Check if we have market data
        if state.get('error') or not state.get('market_data'):
            print("❌ Cannot analyze - no market data available")
            return state
        
        market_data = state['market_data']
        
        # Get data for both timeframes
        tf_higher = config.TIMEFRAME_HIGHER
        tf_lower = config.TIMEFRAME_LOWER
        
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
        orderbook_analysis = analyze_orderbook(
            market_data['orderbook'],
            market_data['current_price']
        )
        
        # Detect trend reversal (comparing higher TF to lower TF)
        print(f"   Checking for trend reversal...")
        reversal_analysis = detect_trend_reversal(
            indicators_lower,
            indicators_higher,
            market_data['current_price']
        )
        
        # Sentiment analysis
        funding_rate = market_data['funding_rate']
        
        # Funding rate sentiment
        if funding_rate > 0.0001:
            funding_sentiment = "bullish"
        elif funding_rate < -0.0001:
            funding_sentiment = "bearish"
        else:
            funding_sentiment = "neutral"
        
        # Volume momentum (from higher timeframe for trend)
        volume_trend = indicators_higher['volume']['trend']
        if volume_trend == "increasing":
            volume_momentum = "positive"
        elif volume_trend == "decreasing":
            volume_momentum = "negative"
        else:
            volume_momentum = "neutral"
        
        # Orderbook pressure
        orderbook_pressure = orderbook_analysis['imbalance']['pressure']
        
        sentiment = {
            "funding_rate": funding_rate,
            "funding_sentiment": funding_sentiment,
            "volume_momentum": volume_momentum,
            "orderbook_pressure": orderbook_pressure
        }
        
        # Create analysis summary
        summary_parts = []
        
        # Higher timeframe (trend)
        ind_h = indicators_higher
        summary_parts.append(f"{tf_higher}: EMA {ind_h['ema']['trend']}, MACD {ind_h['macd']['signal']}")
        
        # Lower timeframe (entry)
        ind_l = indicators_lower
        summary_parts.append(f"{tf_lower}: RSI {ind_l['rsi']['value']}, MACD {ind_l['macd']['signal']}")
        
        # Orderbook
        ob_imbalance = orderbook_analysis['imbalance']
        summary_parts.append(f"OB {orderbook_pressure} (bid {ob_imbalance['bid_percentage']:.1f}%)")
        
        # Timeframe confluence & Entry setup detection
        higher_trend = ind_h['ema']['trend']
        lower_trend = ind_l['ema']['trend']
        lower_macd = ind_l['macd']['signal']
        lower_rsi = ind_l['rsi']['value']
        
        # Detect entry setups
        if higher_trend == lower_trend == lower_macd:
            # Both aligned - trend running, possibly late
            confluence = "aligned_running"
            entry_quality = "trend_following"
        elif higher_trend == "bullish" and lower_trend == "bearish" and lower_macd == "bullish":
            # Pullback ending, MACD turning back to trend
            confluence = "pullback_entry_long"
            entry_quality = "pullback_reversal"
        elif higher_trend == "bearish" and lower_trend == "bullish" and lower_macd == "bearish":
            # Pullback ending, MACD turning back to trend
            confluence = "pullback_entry_short"
            entry_quality = "pullback_reversal"
        elif higher_trend == "bullish" and lower_trend == "bearish":
            # In pullback, waiting
            confluence = "pullback_in_progress_bullish"
            entry_quality = "wait_for_reversal"
        elif higher_trend == "bearish" and lower_trend == "bullish":
            # In pullback, waiting
            confluence = "pullback_in_progress_bearish"
            entry_quality = "wait_for_reversal"
        elif higher_trend == "neutral" or lower_trend == "neutral":
            confluence = "unclear"
            entry_quality = "avoid"
        else:
            confluence = "divergent"
            entry_quality = "conflicting"
        
        summary = f"Multi-TF: {', '.join(summary_parts)}. Setup: {entry_quality} ({confluence}). Sentiment: {funding_sentiment} funding, {volume_momentum} volume, {orderbook_pressure} orderbook."
        
        analysis = {
            "indicators": indicators,
            "orderbook": orderbook_analysis,
            "sentiment": sentiment,
            "confluence": confluence,
            "entry_quality": entry_quality,
            "reversal": reversal_analysis,
            "summary": summary
        }
        
        print(f"✅ Multi-timeframe analysis completed:")
        print(f"\n   📈 {tf_higher} (Trend Timeframe):")
        print(f"      RSI: {ind_h['rsi']['value']} ({ind_h['rsi']['signal']})")
        print(f"      MACD: {ind_h['macd']['signal']}")
        print(f"      EMA Trend: {ind_h['ema']['trend']}")
        print(f"      S/R: {ind_h['support_resistance']['position']}")
        
        print(f"\n   ⚡ {tf_lower} (Entry Timeframe):")
        print(f"      RSI(14): {ind_l['rsi']['value']} ({ind_l['rsi']['signal']})")
        print(f"      RSI(7): {ind_l['rsi_7']['value']} ({ind_l['rsi_7']['turning']})")
        print(f"      MACD: {ind_l['macd']['signal']}")
        print(f"      EMA Trend: {ind_l['ema']['trend']}")
        print(f"      BB: {ind_l['bollinger_bands']['position']}")
        
        # Market condition
        market_cond = ind_l['market_condition']
        print(f"\n   🌊 Market Condition: {market_cond['condition'].upper()} (score: {market_cond['choppy_score']})")
        if market_cond['warning']:
            print(f"      ⚠️  {market_cond['warning']}")
        if market_cond['signals']:
            print(f"      Signals: {', '.join(market_cond['signals'][:3])}")
        
        print(f"\n   🎯 Entry Setup: {entry_quality.upper()}")
        print(f"      Confluence: {confluence}")
        
        # Explain the setup
        if entry_quality == "pullback_reversal":
            print(f"      💡 Pullback reversal detected (typically better R/R)")
            print(f"      → Check: RSI healthy + MACD clear crossover")
        elif entry_quality == "trend_following":
            print(f"      📊 Trend running (can work if strong confirmation)")
            print(f"      → Check: Strong orderbook + volume + RSI not extreme")
        elif entry_quality == "wait_for_reversal":
            print(f"      ⏳ In pullback (wait for MACD reversal)")
        elif entry_quality == "avoid":
            print(f"      🚫 Unclear signals (avoid)")
        
        print(f"\n   📖 Orderbook: {orderbook_pressure} (bid/ask: {ob_imbalance['bid_percentage']:.1f}%/{ob_imbalance['ask_percentage']:.1f}%)")
        if orderbook_analysis['walls']['has_significant_walls']:
            print(f"      ⚠️  Large orders detected (walls)")
        
        # Trend reversal info
        if reversal_analysis['reversal_detected']:
            print(f"\n   🔄 TREND REVERSAL DETECTED!")
            print(f"      Type: {reversal_analysis['reversal_type']}")
            print(f"      Strength: {reversal_analysis['strength_label'].upper()} ({reversal_analysis['strength']}/100)")
            print(f"      Confirmations ({reversal_analysis['confirmation_count']}):")
            for factor in reversal_analysis['confirmation_factors']:
                print(f"         ✓ {factor}")
            
            if reversal_analysis['strength_label'] == 'strong':
                print(f"      💎 Strong reversal - high probability setup!")
            elif reversal_analysis['strength_label'] == 'medium':
                print(f"      ⚡ Medium reversal - good opportunity")
            else:
                print(f"      ⚠️  Weak reversal - wait for more confirmation")
        
        print(f"\n   💭 Sentiment:")
        print(f"      Funding: {funding_sentiment}")
        print(f"      Volume: {volume_momentum}")
        print(f"      Orderbook: {orderbook_pressure}")
        
        state['analysis'] = analysis
        
    except Exception as e:
        error_msg = f"Error during analysis: {str(e)}"
        print(f"❌ {error_msg}")
        state['error'] = error_msg
        state['analysis'] = None
    
    return state

