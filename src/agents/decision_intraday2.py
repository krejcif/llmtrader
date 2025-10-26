"""
INTRADAY2 Strategy - Mean Reversion Scalping

Strategy Overview:
- Mean reversion scalping on 15m timeframe
- Bollinger Bands extremes (price touching bands)
- RSI oversold/overbought confirmation
- Quick TP (0.4-0.8%), tight SL (0.3%)
- Multiple trades per day (more than trend strategies)
- Orderbook support/resistance confirmation

Entry Conditions:
LONG:
- Price touches or breaks below BB lower band
- RSI < 35 (oversold)
- Orderbook shows support (bid pressure)
- Not in choppy market
- Expect bounce back to mean (BB middle)

SHORT:
- Price touches or breaks above BB upper band  
- RSI > 65 (overbought)
- Orderbook shows resistance (ask pressure)
- Not in choppy market
- Expect reversion to mean (BB middle)

Exit Strategy:
- Quick TP: 0.4-0.8% (half distance to BB middle)
- Tight SL: 0.3% (beyond BB extreme)
- 2 partial exits (50% at 0.4%, 50% at 0.8%)

Risk Management:
- Avoid breakouts (volume spike + BB breakout = skip)
- Avoid choppy/ranging markets
- Confirm with orderbook imbalance
- Size: smaller due to tight stops
"""

import json
from typing import Dict
from openai import OpenAI
from models.state import TradingState
import config


def make_decision_intraday2(state: TradingState) -> Dict:
    """
    INTRADAY2 Strategy: Mean reversion scalping
    
    Returns:
        Dictionary with recommendation including action, confidence, and reasoning
    """
    print(f"\n🔄 [INTRADAY2 STRATEGY] Mean Reversion Scalping analysis...")
    
    try:
        if state.get('error') or not state.get('analysis'):
            print("❌ Cannot make intraday2 decision - no analysis")
            return {"recommendation_intraday2": None}
        
        market_data = state['market_data']
        analysis = state['analysis']
        
        # Use 15m as primary (same as other strategies, but different approach)
        indicators = analysis['indicators']['lower_tf']['indicators']
        tf = analysis['indicators']['lower_tf']['timeframe']
        
        # Key indicators for mean reversion
        rsi = indicators['rsi']['value']
        rsi_7 = indicators['rsi_7']['value']
        bb = indicators['bollinger_bands']
        orderbook = analysis['orderbook']
        volume = indicators['volume']
        market_condition = indicators['market_condition']['condition']
        current_price = market_data['current_price']
        
        # Calculate distance from BB bands
        bb_upper = bb['upper']
        bb_middle = bb['middle']
        bb_lower = bb['lower']
        
        distance_to_upper = ((bb_upper - current_price) / current_price) * 100
        distance_to_lower = ((current_price - bb_lower) / current_price) * 100
        distance_to_middle = ((bb_middle - current_price) / current_price) * 100
        
        # Prepare structured data for LLM
        analysis_data = {
            "current_price": current_price,
            "timeframe": tf,
            
            "bollinger_bands": {
                "upper": bb_upper,
                "middle": bb_middle,
                "lower": bb_lower,
                "position": bb['position'],
                "squeeze": bb['squeeze'],
                "distance_to_upper_pct": round(distance_to_upper, 2),
                "distance_to_lower_pct": round(distance_to_lower, 2),
                "distance_to_middle_pct": round(abs(distance_to_middle), 2)
            },
            
            "rsi": {
                "rsi_14": rsi,
                "rsi_7": rsi_7,
                "signal": indicators['rsi']['signal'],
                "rsi_7_signal": indicators['rsi_7']['signal']
            },
            
            "orderbook": {
                "pressure": orderbook['imbalance']['pressure'],
                "bid_pct": orderbook['imbalance']['bid_percentage'],
                "ask_pct": orderbook['imbalance']['ask_percentage'],
                "bid_ask_ratio": orderbook['imbalance']['ratio']
            },
            
            "volume": {
                "vs_avg": volume['current_vs_avg'],
                "trend": volume['trend']
            },
            
            "market_condition": {
                "condition": market_condition,
                "warning": indicators['market_condition']['warning']
            },
            
            "ema_trend": indicators['ema']['trend'],
            "macd_signal": indicators['macd']['signal']
        }
        
        # Create detailed prompt for mean reversion analysis
        client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL
        )
        
        prompt = f"""
You are a mean reversion scalping expert. Analyze {state['symbol']} for scalp opportunities based on Bollinger Bands mean reversion on {tf} timeframe.

=== MARKET DATA ({tf} timeframe) ===
Current Price: ${current_price}

BOLLINGER BANDS (Mean Reversion Zones):
- Upper Band: {bb_upper} ({distance_to_upper:+.2f}% away)
- Middle (Mean): {bb_middle} ({distance_to_middle:+.2f}% away)
- Lower Band: {bb_lower} ({distance_to_lower:+.2f}% away)
- Position: {bb['position']}
- Squeeze: {bb['squeeze']}

RSI (Oversold/Overbought):
- RSI(14): {rsi} ({indicators['rsi']['signal']})
- RSI(7): {rsi_7} ({indicators['rsi_7']['signal']})

ORDERBOOK (Support/Resistance):
- Pressure: {orderbook['imbalance']['pressure']}
- Bids: {orderbook['imbalance']['bid_percentage']:.1f}%
- Asks: {orderbook['imbalance']['ask_percentage']:.1f}%
- Bid/Ask Ratio: {orderbook['imbalance']['ratio']}

VOLUME: {volume['current_vs_avg']}x average ({volume['trend']})
MARKET: {market_condition} {f"⚠️ {indicators['market_condition']['warning']}" if indicators['market_condition']['warning'] else ""}
TREND: {indicators['ema']['trend']} (EMA), {indicators['macd']['signal']} (MACD)

=== MEAN REVERSION STRATEGY RULES ===

LONG Entry (Buy oversold, sell at mean):
✅ Price at/below BB lower (< -0.5% from lower band)
✅ RSI < 35 (oversold)
✅ Orderbook support (bids > 52% or strong_buy pressure)
✅ NOT choppy market
✅ NOT volume breakout (volume < 2x)
→ Expect: Bounce to BB middle (mean reversion)
→ Target: 0.4-0.8% gain (partial exits)
→ Stop: 0.3% below entry

SHORT Entry (Sell overbought, buy at mean):
✅ Price at/above BB upper (< 0.5% from upper band)
✅ RSI > 65 (overbought)
✅ Orderbook resistance (asks > 52% or strong_sell pressure)
✅ NOT choppy market
✅ NOT volume breakout (volume < 2x)
→ Expect: Drop to BB middle (mean reversion)
→ Target: 0.4-0.8% gain (partial exits)
→ Stop: 0.3% above entry

SKIP (Not mean reversion):
❌ Price in BB middle zone (no extreme)
❌ Choppy/ranging market (BB squeeze)
❌ Volume spike + breakout (trend, not reversion)
❌ Conflicting signals (e.g., price low but orderbook resistance)

=== YOUR TASK ===
Analyze if this is a MEAN REVERSION scalp setup. Consider:
1. Is price at BB extreme (touching bands)?
2. Is RSI confirming oversold/overbought?
3. Does orderbook support the reversion direction?
4. Is market NOT choppy and NOT breaking out?

Respond ONLY in JSON:
{{
  "action": "LONG" | "SHORT" | "NEUTRAL",
  "confidence": "high" | "medium" | "low",
  "reasoning": "Brief explanation of mean reversion setup or why skipping"
}}

Focus on QUALITY over QUANTITY - only take clear mean reversion setups on {tf} timeframe!
"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a mean reversion scalping expert focused on Bollinger Bands extremes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Lower temp for more consistent decisions
            max_tokens=400
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
        
        recommendation = json.loads(response_text)
        
        # Add risk management for mean reversion (quick scalp exits)
        if recommendation['action'] in ['LONG', 'SHORT']:
            direction = 'bullish' if recommendation['action'] == 'LONG' else 'bearish'
            
            # Mean reversion specific stops (tighter than trend following)
            if direction == 'bullish':
                # LONG: expect bounce to mean
                stop_loss = current_price * 0.997  # -0.3% SL (tight)
                take_profit_1 = current_price * 1.004  # +0.4% TP1 (quick)
                take_profit_2 = current_price * 1.008  # +0.8% TP2 (to BB middle)
            else:
                # SHORT: expect drop to mean
                stop_loss = current_price * 1.003  # +0.3% SL (tight)
                take_profit_1 = current_price * 0.996  # -0.4% TP1 (quick)
                take_profit_2 = current_price * 0.992  # -0.8% TP2 (to BB middle)
            
            recommendation['risk_management'] = {
                "entry": round(current_price, 2),
                "stop_loss": round(stop_loss, 2),
                "take_profit_1": round(take_profit_1, 2),
                "take_profit_2": round(take_profit_2, 2),
                "stop_distance_pct": 0.3,
                "tp1_distance_pct": 0.4,
                "tp2_distance_pct": 0.8,
                "risk_reward_ratio": round((0.4 / 0.3), 2),  # Min 1.33:1
                "strategy": "mean_reversion_scalp",
                "exit_plan": "50% at TP1 (+0.4%), 50% at TP2 (+0.8%)"
            }
        
        print(f"\n✅ [INTRADAY2] Decision made:")
        print(f"   Action: {recommendation['action']}")
        print(f"   Confidence: {recommendation.get('confidence', 'N/A')}")
        print(f"   Setup: Mean Reversion @ BB {bb['position']}")
        print(f"   Reasoning: {recommendation.get('reasoning', 'N/A')[:80]}...")
        
        if recommendation['action'] in ['LONG', 'SHORT']:
            rm = recommendation['risk_management']
            print(f"   Entry: ${rm['entry']}")
            print(f"   TP1: ${rm['take_profit_1']} (+{rm['tp1_distance_pct']}%)")
            print(f"   TP2: ${rm['take_profit_2']} (+{rm['tp2_distance_pct']}%)")
            print(f"   SL: ${rm['stop_loss']} (-{rm['stop_distance_pct']}%)")
        
        return {"recommendation_intraday2": recommendation}
        
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing AI response (intraday2): {str(e)}. Response: {response_text[:200]}..."
        print(f"❌ {error_msg}")
        return {"recommendation_intraday2": None}
    except Exception as e:
        error_msg = f"Error making decision (intraday2): {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return {"recommendation_intraday2": None}

