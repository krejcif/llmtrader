"""Decision Agent - INTRADAY Strategy (Minimal logic with 5m/15m timeframes)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from openai import OpenAI
from utils.indicators import calculate_stop_take_profit
import config
import json
from datetime import datetime


def make_decision_intraday(state: TradingState) -> TradingState:
    """
    Intraday strategy - uses MINIMAL prompt with fast 5m/15m timeframes
    
    Strategy:
    - Uses same AI decision logic as minimal
    - Low TF: 5m (fast entry signals)
    - High TF: 15m (trend context)
    - Runs every 5 minutes
    """
    print(f"\n⚡ [INTRADAY] Making intraday decision (5m/15m)...")
    
    try:
        # Support both generic keys (market_data, analysis) and specific keys (market_data_intraday, analysis_intraday)
        market_data_key = 'market_data_intraday' if 'market_data_intraday' in state else 'market_data'
        analysis_key = 'analysis_intraday' if 'analysis_intraday' in state else 'analysis'
        
        if state.get('error') or not state.get(analysis_key):
            print(f"❌ Cannot make intraday decision - no {analysis_key}")
            return {"recommendation_intraday": None}
        
        market_data_intraday = state[market_data_key]
        analysis = state[analysis_key]
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
        
        # Get momentum data (if available)
        momentum = analysis.get('momentum')
        
        # Build momentum section for prompt
        momentum_section = ""
        if momentum:
            recent = momentum['recent_candles']
            vol_mom = momentum['volume_momentum']
            levels = momentum['immediate_levels']
            score = momentum['momentum_score']
            current = momentum['current_candle']
            
            # Format recent candles
            candles_text = "\n".join([
                f"{i+1}. ${c['open']} → ${c['close']} ({c['change_pct']:+.2f}%, vol: {c['volume_ratio']:.1f}x avg) - {c['type']}"
                for i, c in enumerate(recent['candles'])
            ])
            
            momentum_section = f"""
=== 🔥 RECENT PRICE ACTION (Last 5 candles on {tf_lower}) ===
{candles_text}
PATTERN: {recent['pattern']} ({recent['bullish_count']}/5 bullish)

=== ⚡ VOLUME MOMENTUM ===
Current volume: {vol_mom['current']} ({vol_mom['current_vs_avg']:.1f}x avg)
Previous: {vol_mom['previous']} ({vol_mom['prev_vs_avg']:.1f}x avg)
Change: {vol_mom['change_pct']:+.1f}% vs previous candle
Trend: {vol_mom['trend']}
{vol_mom['status']}

=== 📍 IMMEDIATE LEVELS (last 30 candles on {tf_lower}) ===
Recent swing high: ${levels['recent_high']} (↑ {levels['distance_to_high_pct']:+.2f}%)
Recent swing low: ${levels['recent_low']} (↓ {levels['distance_to_low_pct']:+.2f}%)
Position: {levels['position']}
Range size: {levels['range_size_pct']:.2f}%

=== 🎯 MOMENTUM SCORE ===
Score: {score['score']}/10 - {score['interpretation']}
Direction: {score['direction']}
Price velocity (15min): {score['velocity_15min']:+.2f}%
Price velocity (30min): {score['velocity_30min']:+.2f}%
Volume trend: {score['volume_change_pct']:+.1f}% vs 1h ago
RSI momentum: {score['rsi_momentum']}

=== 📊 CURRENT CANDLE (in progress) ===
Open: ${current['open']}, Current: ${current['close']}, High: ${current['high']}, Low: ${current['low']}
Body: {current['body_pct']:+.2f}%
Type: {current['type']}
Pressure: {current['pressure']}
"""
        
        # MINIMAL PROMPT - Just data, no rules (with momentum focus for intraday)
        prompt = f"""You are a professional crypto trader analyzing {state['symbol']}.

CURRENT PRICE: ${market_data_intraday['current_price']}

=== HIGHER TIMEFRAME ({tf_higher}) - TREND CONTEXT ===
RSI: {ind_higher['rsi']['value']} ({ind_higher['rsi']['signal']})
MACD: value={ind_higher['macd']['macd']}, signal={ind_higher['macd']['signal_line']}, histogram={ind_higher['macd']['histogram']}, trend={ind_higher['macd']['signal']}
EMA: 20={ind_higher['ema']['ema_20']}, 50={ind_higher['ema']['ema_50']}, trend={ind_higher['ema']['trend']}
Volume: trend={ind_higher['volume']['trend']}, vs_avg={ind_higher['volume']['current_vs_avg']}x
{momentum_section}
=== LOWER TIMEFRAME ({tf_lower}) - TECHNICAL INDICATORS ===
RSI(14): {ind_lower['rsi']['value']} ({ind_lower['rsi']['signal']})
RSI(7): {ind_lower['rsi_7']['value']} (turning: {ind_lower['rsi_7']['turning']})
MACD: {ind_lower['macd']['signal']}
Bollinger Bands: position={ind_lower['bollinger_bands']['position']}, squeeze={ind_lower['bollinger_bands']['squeeze']}

=== ORDERBOOK (LIVE PRESSURE) ===
Bid/Ask: {orderbook['imbalance']['bid_percentage']:.1f}% / {orderbook['imbalance']['ask_percentage']:.1f}%
Pressure: {orderbook['imbalance']['pressure']}
Spread: {orderbook['spread']['percentage']:.4f}%

=== MARKET CONTEXT ===
Funding rate: {sentiment['funding_rate']:.6f} ({sentiment['funding_sentiment']})
Entry quality: {analysis.get('entry_quality', 'unknown')}
Timeframe confluence: {analysis.get('confluence', 'unknown')}

YOUR TASK - INTRADAY MOMENTUM TRADING:
This is a FAST {tf_lower}/{tf_higher} strategy - look for SHORT-TERM momentum plays!
Focus on: volume spikes, recent price action pattern, momentum score, and current candle pressure.

Respond ONLY with JSON (action MUST be "LONG", "SHORT", or "NEUTRAL" - do NOT use "HOLD"):
{{
  "action": "LONG",
  "confidence": "high",
  "reasoning": "Your 2-3 sentence reasoning focusing on momentum and entry timing",
  "key_factors": ["factor1", "factor2", "factor3"]
}}

IMPORTANT: Use "NEUTRAL" (not "HOLD") when you don't see a clear momentum opportunity."""
        
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
        
        # Debug: Show what AI returned
        print(f"   AI Response: {json.dumps(recommendation, indent=2)}")
        
        # Validate
        if 'action' not in recommendation or recommendation['action'] not in ['LONG', 'SHORT', 'NEUTRAL']:
            print(f"❌ Invalid action in recommendation: {recommendation}")
            raise ValueError(f"Invalid action in recommendation: {recommendation.get('action', 'MISSING')}")
        
        # Calculate ATR-based SL/TP
        if recommendation['action'] in ['LONG', 'SHORT']:
            print(f"   Calculating ATR-based risk management...")
            
            candles_lower = market_data_intraday['timeframes'][tf_lower]
            direction = 'bullish' if recommendation['action'] == 'LONG' else 'bearish'
            risk_mgmt = calculate_stop_take_profit(candles_lower, direction)
            
            recommendation['risk_management'] = risk_mgmt
            recommendation['strategy'] = 'intraday'  # Tag strategy
            
            print(f"\n✅ [INTRADAY] Decision made (5m/15m):")
            print(f"   Action: {recommendation['action']}")
            print(f"   Confidence: {recommendation.get('confidence', 'N/A')}")
            print(f"   Entry: ${risk_mgmt['entry']}")
            print(f"   Stop Loss: ${risk_mgmt['stop_loss']} (-{risk_mgmt['stop_distance_percentage']}%)")
            print(f"   Take Profit: ${risk_mgmt['take_profit']} (+{risk_mgmt['tp_distance_percentage']}%)")
            print(f"   R/R: 1:{risk_mgmt['risk_reward_ratio']}")
        else:
            recommendation['strategy'] = 'intraday'
            print(f"\n✅ [INTRADAY] Decision made:")
            print(f"   Action: {recommendation['action']}")
            print(f"   Reasoning: {recommendation.get('reasoning', 'N/A')}")
        
        # Only update recommendation, don't return full state (for parallel execution)
        return {"recommendation_intraday": recommendation}
        
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing AI response: {str(e)}"
        print(f"❌ {error_msg}")
        return {"recommendation_intraday": None}
    except Exception as e:
        error_msg = f"Error making decision (intraday): {str(e)}"
        print(f"❌ {error_msg}")
        return {"recommendation_intraday": None}

