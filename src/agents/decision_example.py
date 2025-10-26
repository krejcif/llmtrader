"""Decision Agent - EXAMPLE Strategy (template for new strategies)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from openai import OpenAI
from utils.indicators import calculate_stop_take_profit
import config
import json


def make_decision_example(state: TradingState) -> TradingState:
    """
    EXAMPLE STRATEGY - Use this as a template for your own strategies
    
    This is a simple strategy that uses minimal prompt logic.
    You can customize the prompt, timeframes, and decision logic.
    """
    print(f"\n🎯 [EXAMPLE] Making decision...")
    
    try:
        # Support both generic keys (market_data, analysis) and specific keys
        market_data_key = 'market_data_example' if 'market_data_example' in state else 'market_data'
        analysis_key = 'analysis_example' if 'analysis_example' in state else 'analysis'
        
        if state.get('error') or not state.get(analysis_key):
            print(f"❌ Cannot make example decision - no {analysis_key}")
            return {"recommendation_example": None}
        
        market_data = state[market_data_key]
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
        
        # EXAMPLE PROMPT - Customize this for your strategy
        prompt = f"""You are a professional crypto trader analyzing {state['symbol']}.

CURRENT PRICE: ${market_data['current_price']}

=== HIGHER TIMEFRAME ({tf_higher}) ===
RSI: {ind_higher['rsi']['value']} ({ind_higher['rsi']['signal']})
MACD: {ind_higher['macd']['signal']}
EMA Trend: {ind_higher['ema']['trend']}

=== LOWER TIMEFRAME ({tf_lower}) ===
RSI: {ind_lower['rsi']['value']} ({ind_lower['rsi']['signal']})
MACD: {ind_lower['macd']['signal']}
EMA Trend: {ind_lower['ema']['trend']}
Volume: {ind_lower['volume']['trend']} ({ind_lower['volume']['current_vs_avg']}x avg)

=== ORDERBOOK ===
Pressure: {orderbook['imbalance']['pressure']}

=== SENTIMENT ===
Funding: {sentiment['funding_sentiment']}
Volume momentum: {sentiment['volume_momentum']}

YOUR TASK:
Based on the data, decide: LONG, SHORT, or NEUTRAL.

Respond ONLY with JSON:
{{
  "action": "LONG",
  "confidence": "high",
  "reasoning": "Brief explanation",
  "key_factors": ["factor1", "factor2"]
}}"""
        
        # Call AI
        print("   Calling DeepSeek API...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an expert cryptocurrency trader. Respond with JSON only."},
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
        
        if 'action' not in recommendation or recommendation['action'] not in ['LONG', 'SHORT', 'NEUTRAL']:
            raise ValueError("Invalid action")
        
        # Calculate risk management for LONG/SHORT
        if recommendation['action'] in ['LONG', 'SHORT']:
            print(f"   Calculating risk management...")
            
            candles_lower = market_data['timeframes'][tf_lower]
            direction = 'bullish' if recommendation['action'] == 'LONG' else 'bearish'
            risk_mgmt = calculate_stop_take_profit(candles_lower, direction)
            
            recommendation['risk_management'] = risk_mgmt
            recommendation['strategy'] = 'example'
            
            print(f"\n✅ [EXAMPLE] Decision: {recommendation['action']} ({recommendation.get('confidence', 'N/A')})")
            print(f"   Entry: ${risk_mgmt['entry']}")
            print(f"   Stop Loss: ${risk_mgmt['stop_loss']} (-{risk_mgmt['stop_distance_percentage']}%)")
            print(f"   Take Profit: ${risk_mgmt['take_profit']} (+{risk_mgmt['tp_distance_percentage']}%)")
            print(f"   R/R: 1:{risk_mgmt['risk_reward_ratio']}")
        else:
            recommendation['strategy'] = 'example'
            print(f"\n✅ [EXAMPLE] Decision: {recommendation['action']}")
            print(f"   Reasoning: {recommendation.get('reasoning', 'N/A')}")
        
        return {"recommendation_example": recommendation}
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing AI response: {e}")
        return {"recommendation_example": None}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"recommendation_example": None}

