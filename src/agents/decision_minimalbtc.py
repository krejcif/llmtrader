"""Decision Agent - Minimal BTC version (with BTCUSDT orderbook context)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from openai import OpenAI
from utils.indicators import calculate_stop_take_profit
import config
import json


def make_decision_minimalbtc(state: TradingState) -> TradingState:
    """
    Make trading decision using MINIMAL prompt with BTCUSDT orderbook context
    
    Args:
        state: Current trading state with market data and analysis
        
    Returns:
        Updated state with trading recommendation (minimalbtc strategy)
    """
    
    # 🚨 TEMPORARY: FORCE SHORT FOR TESTING PAPER TRADING 🚨
    FORCE_SHORT_TEST = False  # Set to True to test paper trading
    
    if FORCE_SHORT_TEST:
        print(f"\n⚠️  [MINIMALBTC STRATEGY - TEST MODE] FORCING SHORT for paper trading test!")
        
        # Get market data for risk management
        market_data = state.get('market_data')
        analysis = state.get('analysis')
        
        if not market_data or not analysis:
            return {"recommendation_minimalbtc": None}
        
        indicators = analysis['indicators']
        tf_lower = indicators['lower_tf']['timeframe']
        candles_lower = market_data['timeframes'][tf_lower]
        
        risk_mgmt = calculate_stop_take_profit(candles_lower, 'bearish')
        
        recommendation = {
            'action': 'SHORT',
            'confidence': 'high',
            'reasoning': 'TEST MODE - Forced SHORT to test paper trading execution',
            'risk_management': risk_mgmt,
            'strategy': 'minimalbtc'
        }
        
        print(f"✅ [MINIMALBTC - TEST] Forced SHORT decision:")
        print(f"   Entry: ${risk_mgmt['entry']}")
        print(f"   Stop Loss: ${risk_mgmt['stop_loss']}")
        print(f"   Take Profit: ${risk_mgmt['take_profit']}")
        print(f"   R/R: 1:{risk_mgmt['risk_reward_ratio']}")
        
        return {"recommendation_minimalbtc": recommendation}
    
    # Normal flow (when FORCE_SHORT_TEST = False)
    print(f"\n🤖 [MINIMALBTC STRATEGY] Making decision with DeepSeek AI + BTCUSDT context...")
    
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
        
        # Get BTCUSDT orderbook
        btc_orderbook = None
        try:
            from utils.binance_client import BinanceClient
            client = BinanceClient()
            
            btc_depth = client.client.get_order_book(symbol='BTCUSDT', limit=100)
            
            # Calculate BTC orderbook metrics
            btc_bids = btc_depth['bids'][:20]
            btc_asks = btc_depth['asks'][:20]
            
            btc_bid_volume = sum(float(price) * float(qty) for price, qty in btc_bids)
            btc_ask_volume = sum(float(price) * float(qty) for price, qty in btc_asks)
            btc_total_volume = btc_bid_volume + btc_ask_volume
            
            btc_bid_pct = (btc_bid_volume / btc_total_volume * 100) if btc_total_volume > 0 else 50
            btc_ask_pct = (btc_ask_volume / btc_total_volume * 100) if btc_total_volume > 0 else 50
            
            btc_ratio = btc_bid_volume / btc_ask_volume if btc_ask_volume > 0 else 1
            
            if btc_ratio > 1.5:
                btc_pressure = "strong bullish"
            elif btc_ratio > 1.2:
                btc_pressure = "bullish"
            elif btc_ratio < 0.67:
                btc_pressure = "strong bearish"
            elif btc_ratio < 0.83:
                btc_pressure = "bearish"
            else:
                btc_pressure = "neutral"
            
            btc_orderbook = {
                'bid_percentage': btc_bid_pct,
                'ask_percentage': btc_ask_pct,
                'ratio': btc_ratio,
                'pressure': btc_pressure
            }
            
            print(f"   ✅ BTCUSDT orderbook loaded: {btc_pressure} (ratio {btc_ratio:.2f})")
            
        except Exception as e:
            print(f"   ⚠️  Could not load BTCUSDT orderbook: {e}")
            btc_orderbook = None
        
        # Initialize DeepSeek client
        client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL
        )
        
        # Build dual orderbook section with confluence
        orderbook_section = f"""
=== ORDERBOOK ANALYSIS ===

SOLUSDT Orderbook (Direct):
• Bid/Ask: {orderbook['imbalance']['bid_percentage']:.1f}% / {orderbook['imbalance']['ask_percentage']:.1f}%
• Imbalance ratio: {orderbook['imbalance']['ratio']:.2f}
• Pressure: {orderbook['imbalance']['pressure']}
• Spread: {orderbook['spread']['percentage']:.4f}%
• Large orders: {orderbook['walls']['has_significant_walls']}
"""
        
        if btc_orderbook:
            # Calculate confluence
            sol_ratio = orderbook['imbalance']['ratio']
            btc_ratio = btc_orderbook['ratio']
            
            sol_bullish = sol_ratio > 1.2
            sol_bearish = sol_ratio < 0.83
            btc_bullish = btc_ratio > 1.2
            btc_bearish = btc_ratio < 0.83
            
            if sol_bullish and btc_bullish:
                confluence = "STRONG BULLISH (both orderbooks aligned)"
            elif sol_bearish and btc_bearish:
                confluence = "STRONG BEARISH (both orderbooks aligned)"
            elif sol_bullish and btc_bearish:
                confluence = "DIVERGENCE (SOL bullish but BTC bearish - CAUTION: BTC usually leads!)"
            elif sol_bearish and btc_bullish:
                confluence = "DIVERGENCE (SOL bearish but BTC bullish - possible SOL reversal incoming)"
            elif sol_bullish or btc_bullish:
                confluence = "MILD BULLISH (one orderbook bullish)"
            elif sol_bearish or btc_bearish:
                confluence = "MILD BEARISH (one orderbook bearish)"
            else:
                confluence = "NEUTRAL (both orderbooks neutral)"
            
            orderbook_section += f"""
BTCUSDT Orderbook (Market Leader):
• Bid/Ask: {btc_orderbook['bid_percentage']:.1f}% / {btc_orderbook['ask_percentage']:.1f}%
• Imbalance ratio: {btc_orderbook['ratio']:.2f}
• Pressure: {btc_orderbook['pressure']}

CONFLUENCE ANALYSIS:
• SOL ratio: {sol_ratio:.2f} | BTC ratio: {btc_ratio:.2f}
• Overall: {confluence}
"""
        
        # MINIMAL PROMPT - Just data, no rules + BTC context
        prompt = f"""You are a professional crypto trader analyzing {state['symbol']}.

CURRENT PRICE: ${market_data['current_price']}

=== HIGHER TIMEFRAME ({tf_higher}) ===
RSI: {ind_higher['rsi']['value']} ({ind_higher['rsi']['signal']})
MACD: value={ind_higher['macd']['macd']}, signal={ind_higher['macd']['signal_line']}, histogram={ind_higher['macd']['histogram']}, trend={ind_higher['macd']['signal']}
EMA: 20={ind_higher['ema']['ema_20']}, 50={ind_higher['ema']['ema_50']}, trend={ind_higher['ema']['trend']}
Bollinger Bands: upper={ind_higher['bollinger_bands']['upper']}, middle={ind_higher['bollinger_bands']['middle']}, lower={ind_higher['bollinger_bands']['lower']}, position={ind_higher['bollinger_bands']['position']}
Support/Resistance: support=${ind_higher['support_resistance']['nearest_support']}, resistance=${ind_higher['support_resistance']['nearest_resistance']}, position={ind_higher['support_resistance']['position']}
Volume: trend={ind_higher['volume']['trend']}, vs_avg={ind_higher['volume']['current_vs_avg']}x
ATR: ${ind_higher['atr']['value']} ({ind_higher['atr']['percentage']}%)
Pattern: {ind_higher['trend_pattern']['pattern']} ({ind_higher['trend_pattern']['trend_direction']})

=== LOWER TIMEFRAME ({tf_lower}) ===
RSI(14): {ind_lower['rsi']['value']} ({ind_lower['rsi']['signal']})
RSI(7): {ind_lower['rsi_7']['value']} (turning: {ind_lower['rsi_7']['turning']}) ← Fast reversal signal
MACD: value={ind_lower['macd']['macd']}, signal={ind_lower['macd']['signal_line']}, histogram={ind_lower['macd']['histogram']}, trend={ind_lower['macd']['signal']}
EMA: 20={ind_lower['ema']['ema_20']}, 50={ind_lower['ema']['ema_50']}, trend={ind_lower['ema']['trend']}
Bollinger Bands: upper={ind_lower['bollinger_bands']['upper']}, middle={ind_lower['bollinger_bands']['middle']}, lower={ind_lower['bollinger_bands']['lower']}, position={ind_lower['bollinger_bands']['position']}, squeeze={ind_lower['bollinger_bands']['squeeze']}
Support/Resistance: support=${ind_lower['support_resistance']['nearest_support']}, resistance=${ind_lower['support_resistance']['nearest_resistance']}, position={ind_lower['support_resistance']['position']}
Volume: trend={ind_lower['volume']['trend']}, vs_avg={ind_lower['volume']['current_vs_avg']}x
ATR: ${ind_lower['atr']['value']} ({ind_lower['atr']['percentage']}%)
Pattern: {ind_lower['trend_pattern']['pattern']} ({ind_lower['trend_pattern']['trend_direction']})
Market Condition: {ind_lower['market_condition']['condition']} (choppy_score: {ind_lower['market_condition']['choppy_score']}) - {ind_lower['market_condition']['warning'] or 'trending OK'}

{orderbook_section}
=== MARKET CONTEXT ===
Funding rate: {sentiment['funding_rate']:.6f} ({sentiment['funding_sentiment']})
Volume momentum: {sentiment['volume_momentum']}
Orderbook pressure: {sentiment['orderbook_pressure']}

Entry setup detected: {analysis.get('entry_quality', 'unknown')}
Timeframe confluence: {analysis.get('confluence', 'unknown')}

{f"TREND REVERSAL: {analysis['reversal']['reversal_type']}, strength {analysis['reversal']['strength']}/100, confirmations: {analysis['reversal']['confirmation_count']}" if analysis.get('reversal', {}).get('reversal_detected') else "No trend reversal detected"}

YOUR TASK:
Based on ALL the above data (including BTC market context), decide whether to go LONG, SHORT, or stay NEUTRAL.
Use your trading expertise to weigh all factors. Consider BTC orderbook pressure as it often leads altcoin moves.

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
        
        # Calculate ATR-based SL/TP
        if recommendation['action'] in ['LONG', 'SHORT']:
            print(f"   Calculating ATR-based risk management...")
            
            candles_lower = market_data['timeframes'][tf_lower]
            direction = 'bullish' if recommendation['action'] == 'LONG' else 'bearish'
            risk_mgmt = calculate_stop_take_profit(candles_lower, direction)
            
            recommendation['risk_management'] = risk_mgmt
            recommendation['strategy'] = 'minimalbtc'  # Tag strategy
            
            # Add BTC context to recommendation
            if btc_orderbook:
                recommendation['btc_context'] = btc_orderbook['pressure']
            
            print(f"\n✅ [MINIMALBTC] Decision made:")
            print(f"   Action: {recommendation['action']}")
            print(f"   Confidence: {recommendation.get('confidence', 'N/A')}")
            print(f"   Entry: ${risk_mgmt['entry']}")
            print(f"   Stop Loss: ${risk_mgmt['stop_loss']} (-{risk_mgmt['stop_distance_percentage']}%)")
            print(f"   Take Profit: ${risk_mgmt['take_profit']} (+{risk_mgmt['tp_distance_percentage']}%)")
            print(f"   R/R: 1:{risk_mgmt['risk_reward_ratio']}")
            if btc_orderbook:
                print(f"   BTC Context: {btc_orderbook['pressure']}")
        else:
            recommendation['strategy'] = 'minimalbtc'
            if btc_orderbook:
                recommendation['btc_context'] = btc_orderbook['pressure']
            print(f"\n✅ [MINIMALBTC] Decision made:")
            print(f"   Action: {recommendation['action']}")
            print(f"   Reasoning: {recommendation.get('reasoning', 'N/A')}")
        
        # Only update recommendation, don't return full state (for parallel execution)
        return {"recommendation_minimalbtc": recommendation}
        
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing AI response: {str(e)}"
        print(f"❌ {error_msg}")
        return {"recommendation_minimalbtc": None}
    except Exception as e:
        error_msg = f"Error making decision (minimalbtc): {str(e)}"
        print(f"❌ {error_msg}")
        return {"recommendation_minimalbtc": None}

