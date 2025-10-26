"""Decision Agent - Macro strategy (Structured + News + IXIC correlation)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from openai import OpenAI
from utils.indicators import calculate_stop_take_profit
import config
import json


def make_decision_macro(state: TradingState) -> TradingState:
    """
    Make trading decision using MACRO strategy (news + IXIC + technical)
    
    Args:
        state: Trading state with market data, news, and IXIC data
        
    Returns:
        Updated state with macro recommendation
    """
    print(f"\n🌍 [MACRO STRATEGY] Making macro-aware decision...")
    
    try:
        # Check data availability
        if state.get('error') or not state.get('analysis'):
            print("❌ Cannot make macro decision - no analysis")
            return {"recommendation_macro": None}
        
        market_data = state['market_data']
        analysis = state['analysis']
        news_data = state.get('news_data')
        btc_data = state.get('btc_data')
        ixic_data = state.get('ixic_data')
        
        # DEBUG: Check what we received
        print(f"   [DEBUG] btc_data available: {btc_data is not None}")
        if btc_data:
            print(f"   [DEBUG] BTC price: ${btc_data.get('current_price', 'N/A')}")
        print(f"   [DEBUG] State keys: {list(state.keys())}")
        
        indicators = analysis['indicators']
        ind_higher = indicators['higher_tf']['indicators']
        ind_lower = indicators['lower_tf']['indicators']
        tf_higher = indicators['higher_tf']['timeframe']
        tf_lower = indicators['lower_tf']['timeframe']
        
        # Prepare macro context
        news_summary = "No news data available"
        if news_data and news_data.get('items'):
            news_list = []
            for item in news_data['items'][:10]:
                news_list.append(f"- {item['title']} (sentiment: {item.get('sentiment', 'N/A')})")
            news_summary = "\n".join(news_list)
        
        # BTC correlation (always available - primary)
        btc_summary = "No BTC data available"
        if btc_data:
            btc_summary = f"""BITCOIN (BTC/USD) - Crypto Market Leader:
- Current: ${btc_data['current_price']:,.2f}
- Trend 15m: {btc_data['trend_15m']} | 1h: {btc_data['trend_1h']}
- Changes: 15m {btc_data['change_15m']:+.2f}%, 1h {btc_data['change_1h']:+.2f}%, 4h {btc_data['change_4h']:+.2f}%
- Data: FRESH (real-time from Binance)

Correlation insight:
- BTC is crypto market leader
- Altcoins (like SOL) typically follow BTC trend
- BTC bullish → SOL likely bullish
- BTC bearish → SOL likely bearish (stronger correlation than stocks)"""
        
        # IXIC correlation (when fresh - secondary)
        ixic_summary = ""
        if ixic_data and ixic_data.get('fresh', False):
            ixic_summary = f"""
NASDAQ (IXIC) - Tech Stocks (FRESH DATA):
- Current: {ixic_data['current_price']}
- Trend: {ixic_data['trend']}
- 1h change: {ixic_data['change_1h']:+.2f}%
- 4h change: {ixic_data['change_4h']:+.2f}%
- Data age: {ixic_data['data_age_minutes']}min

Secondary correlation:
- Tech stocks sentiment affects crypto
- NASDAQ bullish = risk-on for crypto"""
        elif ixic_data:
            ixic_summary = f"\nNASDAQ (IXIC): ⚠️ STALE ({ixic_data.get('data_age_minutes', 0)//60}h old - market closed, not using)"
        else:
            ixic_summary = "\nNASDAQ (IXIC): Not available"
        
        # Initialize DeepSeek
        client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL
        )
        
        # MACRO PROMPT (based on structured but with macro context)
        prompt = f"""You are a macro-aware crypto trader analyzing {state['symbol']} with broader market context.

CURRENT PRICE: ${market_data['current_price']}

=== STOCK MARKET NEWS (Last 10 general news) ===
{news_summary}

=== {btc_summary} ==={ixic_summary}

=== CRYPTO TECHNICAL ANALYSIS ({state['symbol']}) ===
Higher TF ({tf_higher}): RSI {ind_higher['rsi']['value']}, MACD {ind_higher['macd']['signal']}, EMA {ind_higher['ema']['trend']}
Lower TF ({tf_lower}): RSI(14) {ind_lower['rsi']['value']}, RSI(7) {ind_lower['rsi_7']['value']} ({ind_lower['rsi_7']['turning']}), MACD {ind_lower['macd']['signal']}

Market Condition: {ind_lower['market_condition']['condition']} {f"⚠️ {ind_lower['market_condition']['warning']}" if ind_lower['market_condition']['warning'] else ""}

Entry Setup: {analysis.get('entry_quality', 'unknown')}
Orderbook: {analysis['orderbook']['imbalance']['pressure']} ({analysis['orderbook']['imbalance']['bid_percentage']:.1f}% bids)

YOUR TASK (MACRO STRATEGY):
Consider (in priority order):
1. BTC trend (PRIMARY - always fresh, strong crypto correlation)
2. Technical crypto signals (SOLUSDT technicals)
3. Stock market news sentiment (general risk appetite)
4. NASDAQ (SECONDARY - only if fresh, weak correlation)
5. Market condition (choppy = avoid)

Decision Logic:
- If BTC strongly bearish + news bearish → HIGH confidence SHORT/NEUTRAL (risk-off)
- If BTC bullish + SOLUSDT technicals bullish → HIGH confidence LONG
- If BTC neutral → rely more on SOLUSDT technicals
- If BTC and SOLUSDT diverge → NEUTRAL or reduce confidence
- IXIC: Only minor weight, only if fresh
- If choppy market → NEUTRAL or reduce confidence

BTC is 10x more important than IXIC for crypto trading!

Respond in JSON:
{{
  "action": "LONG",
  "confidence": "high",
  "reasoning": "Include macro factors in reasoning (2-3 sentences)",
  "key_factors": ["factor1 including news/IXIC if relevant", "factor2", "factor3"]
}}"""
        
        # Call DeepSeek
        print("   Calling DeepSeek API (macro analysis)...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a macro-aware cryptocurrency trader. Consider broader market context, news sentiment, and stock market correlation in your decisions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse response
        response_text = response.choices[0].message.content.strip()
        
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        recommendation = json.loads(response_text)
        
        # Validate
        if 'action' not in recommendation or recommendation['action'] not in ['LONG', 'SHORT', 'NEUTRAL']:
            raise ValueError("Invalid action")
        
        # Calculate SL/TP
        if recommendation['action'] in ['LONG', 'SHORT']:
            candles_lower = market_data['timeframes'][tf_lower]
            direction = 'bullish' if recommendation['action'] == 'LONG' else 'bearish'
            risk_mgmt = calculate_stop_take_profit(candles_lower, direction)
            
            recommendation['risk_management'] = risk_mgmt
            recommendation['strategy'] = 'macro'
            
            print(f"\n✅ [MACRO] Decision made:")
            print(f"   Action: {recommendation['action']}")
            print(f"   Confidence: {recommendation.get('confidence', 'N/A')}")
            print(f"   Entry: ${risk_mgmt['entry']}")
            print(f"   SL: ${risk_mgmt['stop_loss']} | TP: ${risk_mgmt['take_profit']}")
        else:
            recommendation['strategy'] = 'macro'
            print(f"\n✅ [MACRO] Decision made:")
            print(f"   Action: {recommendation['action']}")
            print(f"   Reasoning: {recommendation.get('reasoning', 'N/A')[:100]}...")
        
        return {"recommendation_macro": recommendation}
        
    except Exception as e:
        print(f"❌ Error in macro decision: {e}")
        return {"recommendation_macro": None}

