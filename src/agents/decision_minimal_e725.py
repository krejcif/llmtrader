"""Decision Agent - Minimal E725 (EMA 7/25 instead of 20/50)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from openai import OpenAI
from utils.indicators import calculate_stop_take_profit
import config
import json


def make_decision_minimal_e725(state: TradingState) -> TradingState:
    """
    Make trading decision using MINIMAL prompt with EMA 7/25
    
    Args:
        state: Current trading state with market data and analysis
        
    Returns:
        Updated state with trading recommendation (minimal_e725 strategy)
    """
    
    print(f"\n🤖 [MINIMAL_E725 STRATEGY] Making decision with DeepSeek AI (EMA 7/25)...")
    
    try:
        # Check if we have analysis data
        if state.get('error') or not state.get('analysis'):
            print("❌ Cannot make decision - no analysis available")
            return state
        
        market_data = state['market_data']
        analysis = state['analysis']
        indicators = analysis['indicators']
        ind_higher = indicators['higher_tf']['indicators']
        ind_lower = indicators['lower_tf']['indicators']
        tf_higher = indicators['higher_tf']['timeframe']
        tf_lower = indicators['lower_tf']['timeframe']
        orderbook = analysis['orderbook']
        sentiment = analysis['sentiment']
        
        # Initialize DeepSeek client
        client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL
        )
        
        # MINIMAL PROMPT - Just data, no rules (EMA 7/25)
        prompt = f"""You are a professional crypto trader analyzing {state['symbol']}.

CURRENT PRICE: ${market_data['current_price']}

=== HIGHER TIMEFRAME ({tf_higher}) ===
RSI: {ind_higher['rsi']['value']} ({ind_higher['rsi']['signal']})
MACD: value={ind_higher['macd']['macd']}, signal={ind_higher['macd']['signal_line']}, histogram={ind_higher['macd']['histogram']}, trend={ind_higher['macd']['signal']}
EMA: 7={ind_higher['ema']['ema_7']}, 25={ind_higher['ema']['ema_25']}, trend={ind_higher['ema']['trend']}
Bollinger Bands: upper={ind_higher['bollinger_bands']['upper']}, middle={ind_higher['bollinger_bands']['middle']}, lower={ind_higher['bollinger_bands']['lower']}, position={ind_higher['bollinger_bands']['position']}
Support/Resistance: support=${ind_higher['support_resistance']['nearest_support']}, resistance=${ind_higher['support_resistance']['nearest_resistance']}, position={ind_higher['support_resistance']['position']}
Volume: trend={ind_higher['volume']['trend']}, vs_avg={ind_higher['volume']['current_vs_avg']}x
ATR: ${ind_higher['atr']['value']} ({ind_higher['atr']['percentage']}%)
Pattern: {ind_higher['trend_pattern']['pattern']} ({ind_higher['trend_pattern']['trend_direction']})

=== LOWER TIMEFRAME ({tf_lower}) ===
RSI(14): {ind_lower['rsi']['value']} ({ind_lower['rsi']['signal']})
RSI(7): {ind_lower['rsi_7']['value']} (turning: {ind_lower['rsi_7']['turning']}) ← Fast reversal signal
MACD: value={ind_lower['macd']['macd']}, signal={ind_lower['macd']['signal_line']}, histogram={ind_lower['macd']['histogram']}, trend={ind_lower['macd']['signal']}
EMA: 7={ind_lower['ema']['ema_7']}, 25={ind_lower['ema']['ema_25']}, trend={ind_lower['ema']['trend']}
Bollinger Bands: upper={ind_lower['bollinger_bands']['upper']}, middle={ind_lower['bollinger_bands']['middle']}, lower={ind_lower['bollinger_bands']['lower']}, position={ind_lower['bollinger_bands']['position']}, squeeze={ind_lower['bollinger_bands']['squeeze']}
Support/Resistance: support=${ind_lower['support_resistance']['nearest_support']}, resistance=${ind_lower['support_resistance']['nearest_resistance']}, position={ind_lower['support_resistance']['position']}
Volume: trend={ind_lower['volume']['trend']}, vs_avg={ind_lower['volume']['current_vs_avg']}x
ATR: ${ind_lower['atr']['value']} ({ind_lower['atr']['percentage']}%)
Pattern: {ind_lower['trend_pattern']['pattern']} ({ind_lower['trend_pattern']['trend_direction']})
Market Condition: {ind_lower['market_condition']['condition']} (choppy_score: {ind_lower['market_condition']['choppy_score']}) - {ind_lower['market_condition']['warning'] or 'trending OK'}

=== ORDERBOOK ===
Bid/Ask: {orderbook['imbalance']['bid_percentage']:.1f}% / {orderbook['imbalance']['ask_percentage']:.1f}%
Imbalance ratio: {orderbook['imbalance']['ratio']:.2f}
Pressure: {orderbook['imbalance']['pressure']}
Spread: {orderbook['spread']['percentage']:.4f}%
Large orders present: {orderbook['walls']['has_significant_walls']}

=== MARKET CONTEXT ===
Funding rate: {sentiment['funding_rate']:.6f} ({sentiment['funding_sentiment']})
Volume momentum: {sentiment['volume_momentum']}
Orderbook pressure: {sentiment['orderbook_pressure']}

Entry setup detected: {analysis.get('entry_quality', 'unknown')}
Timeframe confluence: {analysis.get('confluence', 'unknown')}

{f"TREND REVERSAL: {analysis['reversal']['reversal_type']}, strength {analysis['reversal']['strength']}/100, confirmations: {analysis['reversal']['confirmation_count']}" if analysis.get('reversal', {}).get('reversal_detected') else "No trend reversal detected"}

YOUR TASK:
Based on ALL the above data, decide whether to go LONG, SHORT, or stay NEUTRAL.
Use your trading expertise to weigh all factors. Note: This analysis uses faster EMAs (7/25) for more responsive signals.

Respond ONLY with JSON:
{{
  "action": "LONG",
  "confidence": "high",
  "reasoning": "Your 2-3 sentence reasoning",
  "key_factors": ["factor1", "factor2", "factor3"]
}}"""
        
        # Call DeepSeek AI
        print("   Calling DeepSeek API...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an expert cryptocurrency trader. Analyze data and make independent trading decisions. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse response
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        recommendation = json.loads(response_text)
        
        # Validate
        if 'action' not in recommendation or recommendation['action'] not in ['LONG', 'SHORT', 'NEUTRAL']:
            raise ValueError("Invalid action in recommendation")
        
        # 🛡️ GUARD RAIL #1: Check momentum alignment (last 2 candles)
        # If AI recommendation is opposite to recent price momentum, override to NEUTRAL
        if recommendation['action'] in ['LONG', 'SHORT']:
            candles_lower = market_data['timeframes'][tf_lower]
            
            # Get last 3 closes to determine momentum
            last_3_closes = candles_lower['close'].tail(3).tolist()
            
            if len(last_3_closes) >= 3:
                # Check if last 2 candles are bullish or bearish
                candle_1_bullish = last_3_closes[-1] > last_3_closes[-2]  # Most recent candle
                candle_2_bullish = last_3_closes[-2] > last_3_closes[-3]  # Previous candle
                
                # Determine momentum (need at least 2 candles in same direction)
                momentum_bullish = candle_1_bullish and candle_2_bullish
                momentum_bearish = not candle_1_bullish and not candle_2_bullish
                
                original_action = recommendation['action']
                override_reason = None
                
                # Check for misalignment
                if recommendation['action'] == 'LONG' and momentum_bearish:
                    recommendation['action'] = 'NEUTRAL'
                    override_reason = f"AI suggested LONG, but last 2 candles are bearish ({last_3_closes[-3]:.2f} → {last_3_closes[-2]:.2f} → {last_3_closes[-1]:.2f})"
                
                elif recommendation['action'] == 'SHORT' and momentum_bullish:
                    recommendation['action'] = 'NEUTRAL'
                    override_reason = f"AI suggested SHORT, but last 2 candles are bullish ({last_3_closes[-3]:.2f} → {last_3_closes[-2]:.2f} → {last_3_closes[-1]:.2f})"
                
                if override_reason:
                    print(f"\n🛡️  [GUARD RAIL] Momentum misalignment detected!")
                    print(f"   {override_reason}")
                    print(f"   Overriding {original_action} → NEUTRAL")
                    recommendation['reasoning'] = f"[GUARD RAIL OVERRIDE] {override_reason}"
                    recommendation['original_action'] = original_action
        
        # Calculate ATR-based SL/TP
        if recommendation['action'] in ['LONG', 'SHORT']:
            print(f"   Calculating ATR-based risk management...")
            
            candles_lower = market_data['timeframes'][tf_lower]
            direction = 'bullish' if recommendation['action'] == 'LONG' else 'bearish'
            risk_mgmt = calculate_stop_take_profit(candles_lower, direction)
            
            recommendation['risk_management'] = risk_mgmt
            recommendation['strategy'] = 'minimal_e725'  # Tag strategy
            
            print(f"\n✅ [MINIMAL_E725] Decision made:")
            print(f"   Action: {recommendation['action']}")
            print(f"   Confidence: {recommendation.get('confidence', 'N/A')}")
            print(f"   Entry: ${risk_mgmt['entry']}")
            print(f"   Stop Loss: ${risk_mgmt['stop_loss']} (-{risk_mgmt['stop_distance_percentage']}%)")
            print(f"   Take Profit: ${risk_mgmt['take_profit']} (+{risk_mgmt['tp_distance_percentage']}%)")
            print(f"   R/R: 1:{risk_mgmt['risk_reward_ratio']}")
        else:
            recommendation['strategy'] = 'minimal_e725'
            print(f"\n✅ [MINIMAL_E725] Decision made:")
            print(f"   Action: {recommendation['action']}")
            print(f"   Reasoning: {recommendation.get('reasoning', 'N/A')}")
        
        # Only update recommendation, don't return full state (for parallel execution)
        return {"recommendation_minimal_e725": recommendation}
        
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing AI response: {str(e)}"
        print(f"❌ {error_msg}")
        return {"recommendation_minimal_e725": None}
    except Exception as e:
        error_msg = f"Error making decision (minimal_e725): {str(e)}"
        print(f"❌ {error_msg}")
        return {"recommendation_minimal_e725": None}

