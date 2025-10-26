"""Decision Agent - Makes trading recommendations using DeepSeek AI"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from openai import OpenAI
from utils.indicators import calculate_stop_take_profit
import config
import json


def make_decision(state: TradingState) -> TradingState:
    """
    Make trading decision using DeepSeek AI
    
    Args:
        state: Current trading state with market data and analysis
        
    Returns:
        Updated state with trading recommendation
    """
    print(f"\n🤖 Making trading decision with DeepSeek AI...")
    
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
        
        # Prepare prompt
        prompt = f"""Jsi expert na trading analýzu kryptoměn s multi-timeframe analýzou. Na základě poskytnutých dat rozhodneš o trading doporučení pro {state['symbol']}.

AKTUÁLNÍ CENA: {market_data['current_price']} USDT

MULTI-TIMEFRAME ANALÝZA:
{analysis['summary']}

=== {tf_higher.upper()} (TREND TIMEFRAME) ===
Určuje celkový směr trhu a hlavní trend.

- RSI: {ind_higher['rsi']['value']} ({ind_higher['rsi']['signal']})
- MACD: {ind_higher['macd']['signal']} (histogram: {ind_higher['macd']['histogram']})
- EMA Trend: {ind_higher['ema']['trend']}
- Bollinger Bands: {ind_higher['bollinger_bands']['position']}
- Support/Resistance: {ind_higher['support_resistance']['position']} (S: {ind_higher['support_resistance']['nearest_support']}, R: {ind_higher['support_resistance']['nearest_resistance']})
- Volume: {ind_higher['volume']['trend']} ({ind_higher['volume']['current_vs_avg']}x avg)

=== {tf_lower.upper()} (ENTRY TIMEFRAME) ===
Určuje přesný vstupní bod a timing.

- RSI(14): {ind_lower['rsi']['value']} ({ind_lower['rsi']['signal']})
- RSI(7): {ind_lower['rsi_7']['value']} ({ind_lower['rsi_7']['turning']}) ← FAST reversal indicator!
- MACD: {ind_lower['macd']['signal']} (histogram: {ind_lower['macd']['histogram']})
- EMA Trend: {ind_lower['ema']['trend']}
- Bollinger Bands: {ind_lower['bollinger_bands']['position']} (squeeze: {ind_lower['bollinger_bands']['squeeze']})
- Support/Resistance: {ind_lower['support_resistance']['position']}
- ATR: ${ind_lower['atr']['value']} ({ind_lower['atr']['percentage']}% volatility)

=== MARKET CONDITION ===
Condition: {ind_lower['market_condition']['condition'].upper()} (choppy score: {ind_lower['market_condition']['choppy_score']})
{f"⚠️  WARNING: {ind_lower['market_condition']['warning']}" if ind_lower['market_condition']['warning'] else "✅ Market is trending - good for trend trades"}
Signals: {', '.join(ind_lower['market_condition']['signals']) if ind_lower['market_condition']['signals'] else 'None'}

=== ENTRY SETUP ANALYSIS ===
- Higher TF trend: {ind_higher['ema']['trend']} (main trend direction)
- Lower TF trend: {ind_lower['ema']['trend']} (current price action)
- Lower TF MACD: {ind_lower['macd']['signal']} (momentum change)
- Setup Type: {analysis['entry_quality']}
- Confluence: {analysis['confluence']}

=== TREND PATTERN ANALYSIS ===
Higher TF Pattern: {ind_higher.get('trend_pattern', {}).get('pattern', 'N/A')} ({ind_higher.get('trend_pattern', {}).get('trend_direction', 'N/A')})
Lower TF Pattern: {ind_lower.get('trend_pattern', {}).get('pattern', 'N/A')} ({ind_lower.get('trend_pattern', {}).get('trend_direction', 'N/A')})

=== TREND REVERSAL DETECTION ===
{f"🔄 REVERSAL DETECTED: {analysis['reversal']['reversal_type']}" if analysis['reversal']['reversal_detected'] else "No reversal detected"}
{f"Strength: {analysis['reversal']['strength_label'].upper()} ({analysis['reversal']['strength']}/100)" if analysis['reversal']['reversal_detected'] else ""}
{f"Confirmations: {', '.join(analysis['reversal']['confirmation_factors'])}" if analysis['reversal']['reversal_detected'] else ""}

=== ORDERBOOK (REAL-TIME) ===
- Bid/Ask Imbalance: {orderbook['imbalance']['bid_percentage']:.1f}% / {orderbook['imbalance']['ask_percentage']:.1f}% (ratio: {orderbook['imbalance']['ratio']:.2f})
- Pressure: {orderbook['imbalance']['pressure']}
- Spread: {orderbook['spread']['percentage']:.4f}%
- Large orders (walls): {"Ano" if orderbook['walls']['has_significant_walls'] else "Ne"}

=== SENTIMENT ===
- Funding rate: {sentiment['funding_sentiment']} ({sentiment['funding_rate']:.6f})
- Volume momentum: {sentiment['volume_momentum']}
- Orderbook pressure: {sentiment['orderbook_pressure']}

ENTRY SETUP ANALÝZA:
Systém detekoval setup: "{analysis['entry_quality']}"
{f"⚠️ DŮLEŽITÉ: Trend reversal detekován ({analysis['reversal']['strength_label']} strength)!" if analysis['reversal']['reversal_detected'] else ""}

MOŽNÉ ENTRY SETUPS:

1. **pullback_reversal** - Pullback reversal entry
   Situace: Higher TF trend + Lower TF pullback se vrací zpět do trendu
   Detekce: RSI(7) turning_up (EARLY!) nebo MACD crossover (CONFIRMED)
   Výhody: ✅ Nejlepší R/R (1:3+), ✅ Entry na začátku pohybu, ✅ Tight stop
   Nevýhody: ⚠️ Pokud pullback moc hluboký, může pokračovat
   Kdy vstoupit:
   - EARLY: RSI(7) turning_up + RSI(7) < 40 → Medium confidence (fast entry)
   - CONFIRMED: RSI(7) turning_up + MACD crossover → High confidence (safer)
   - LATE: Pouze MACD crossover → Medium confidence (may be late)
   
2. **trend_following** - Aligned running trend
   Situace: Oba TF aligned, trend běží
   Výhody: ✅ Silný momentum, ✅ Jasný trend, ✅ Může pokračovat daleko
   Nevýhody: ⚠️ Možná pozdě, ⚠️ Horší R/R (1:1.5), ⚠️ Blízko krátkodobého top
   Kdy vstoupit: Pokud silný orderbook support + volume increasing + RSI není overbought/oversold

3. **wait_for_reversal** - V pullbacku, čekat
   Situace: Higher TF trend OK, ale Lower TF v pullbacku (MACD ještě neobrací)
   Action: NEUTRAL / WAIT (pullback není dokončený)

4. **conflicting/avoid** - Konfliktní signály
   Action: NEUTRAL / AVOID

5. **TREND REVERSAL** - Speciální setup!
   Situace: Trend se MĚNÍ (bearish → bullish nebo bullish → bearish)
   Detekce:
   - EMA crossover na higher TF
   - MACD alignment
   - Higher Highs/Lows pattern change
   - Volume surge
   Výhody: ✅ Catching reversal early, ✅ Huge profit potential
   Nevýhody: ⚠️ Risky (reversal může failnout), ⚠️ Need strong confirmation
   Kdy vstoupit: 
   - STRONG reversal (75+) + orderbook potvrzuje → HIGH confidence
   - MEDIUM reversal (60-75) + confirmace → MEDIUM confidence
   - WEAK reversal (<60) → WAIT for more confirmation

TVOJE ÚLOHA:
Rozhodneš SAM na základě VŠECH faktorů:
- Entry setup type a jeho výhody/nevýhody
- Market condition: CHOPPY = AVOID/reduce! TRENDING = trade normally
- RSI(7): turning_up/down = early reversal signal (fast but noisier)
- RSI(14): oversold/overbought = confirmation
- MACD: trend confirmation (slower but reliable)
- Orderbook: Potvrzuje entry? (buy/sell pressure)
- Volume: Increasing = silnější signál
- Support/Resistance: Blízko klíčových levelů?

PŘÍKLADY SPRÁVNÉHO ROZHODOVÁNÍ:

✅ VSTUP při pullback_reversal:
EARLY (aggressive):
- RSI(7) turning_up + RSI(7) < 40 ✓
- Orderbook potvrzuje ✓
→ LONG s MEDIUM confidence (fast entry, best R/R but riskier)

CONFIRMED (recommended):
- RSI(7) turning_up + MACD crossover ✓
- RSI(14) healthy 40-65 ✓
- Orderbook potvrzuje ✓
→ LONG/SHORT s HIGH confidence (best balance)

LATE:
- Pouze MACD crossover ✓
- RSI indicators OK ✓
→ LONG/SHORT s MEDIUM confidence (safer but worse R/R)

✅ VSTUP při aligned_running (může být správně!):
- Silný momentum ✓
- Strong orderbook pressure ✓
- Volume increasing ✓
- RSI <65 (není overbought) ✓
- Není blízko resistance ✓
→ LONG/SHORT s medium/high confidence

✅ VSTUP při STRONG trend reversal:
- Reversal strength 75+ ✓
- Multiple confirmations (4+) ✓
- Orderbook shift v novou direction ✓
- Volume surge ✓
- Pattern change (HH/HL nebo LH/LL) ✓
→ LONG/SHORT s HIGH confidence (early reversal entry!)

❌ NEVSTUPOVAT:
- Market condition: CHOPPY (score 5+) → AVOID trend trades!
- Market condition: RANGING (score 3-4) → Be cautious, reduce size
- RSI(14) extrémní (>75 nebo <25) → Too extended
- Orderbook conflicting → No support
- RSI(7) false signal (whipsaw) → Wait for MACD confirmation
→ WAIT / NEUTRAL

❌ NEVSTUPOVAT při aligned_running:
- RSI overbought/oversold
- Blízko resistance/support
- Orderbook slabý nebo konfliktní
→ NEUTRAL

❌ NEVSTUPOVAT při WEAK reversal:
- Reversal strength <60
- Málo confirmations (<3)
- Orderbook nesouhlasí
→ WAIT (reversal není confirmed)

RISK MANAGEMENT:
- Pokud doporučíš LONG/SHORT, systém automaticky vypočítá:
  - Stop Loss: 1.5x ATR od entry (volatility-adjusted)
  - Take Profit: 3.0x ATR od entry (R/R ratio 1:2+)
  - ATR na {tf_lower}: ${ind_lower['atr']['value']} ({ind_lower['atr']['percentage']}%)
  
- Vysoká ATR (>3%) = volatilní trh = širší stops, větší profit potential
- Nízká ATR (<1%) = klidný trh = tight stops, menší pohyby

Na základě VŠECH dat rozhodneš:
1. Action: LONG/SHORT/NEUTRAL
   - Zvážit entry setup + orderbook + RSI + volume + S/R + ATR
   - Může být LONG/SHORT i při aligned_running pokud všechno potvrzuje!
   - ATR vysoká (>3%) = větší risk, ale i reward
   
2. Confidence: low/medium/high
   - HIGH: Všechny faktory aligned (setup + OB + indicators + healthy RSI)
   - MEDIUM: Většina faktorů OK, něco chybí
   - LOW: Setup OK ale slabá confirmace
   
3. Reasoning: Vysvětli PROČ vstupuješ nebo ne-vstupuješ (2-3 věty)
   - Zahrň entry setup type
   - Zahrň confirming/conflicting faktory
   - Můžeš zmínit ATR pokud relevantní (vysoká volatilita)
   
4. Key factors: 3 hlavní důvody pro rozhodnutí

Odpověz POUZE v tomto JSON formátu:
{{
  "action": "LONG",
  "confidence": "high",
  "reasoning": "...",
  "key_factors": ["factor1", "factor2", "factor3"]
}}"""
        
        # Call DeepSeek AI
        print("   Calling DeepSeek API...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional cryptocurrency trading analyst. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse response
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON if there's extra text
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        recommendation = json.loads(response_text)
        
        # Validate recommendation
        if 'action' not in recommendation or recommendation['action'] not in ['LONG', 'SHORT', 'NEUTRAL']:
            raise ValueError("Invalid action in recommendation")
        
        # Calculate ATR-based stop loss and take profit
        if recommendation['action'] in ['LONG', 'SHORT']:
            print(f"   Calculating ATR-based risk management...")
            
            # Use lower timeframe for more responsive stops
            candles_lower = market_data['timeframes'][tf_lower]
            
            direction = 'bullish' if recommendation['action'] == 'LONG' else 'bearish'
            risk_mgmt = calculate_stop_take_profit(candles_lower, direction)
            
            recommendation['risk_management'] = risk_mgmt
            recommendation['strategy'] = 'structured'  # Tag strategy
            
            print(f"\n✅ [STRUCTURED] Decision made:")
            print(f"   Action: {recommendation['action']}")
            print(f"   Confidence: {recommendation.get('confidence', 'N/A')}")
            print(f"   Entry: ${risk_mgmt['entry']}")
            print(f"   Stop Loss: ${risk_mgmt['stop_loss']} (-{risk_mgmt['stop_distance_percentage']}%)")
            print(f"   Take Profit: ${risk_mgmt['take_profit']} (+{risk_mgmt['tp_distance_percentage']}%)")
            print(f"   Risk/Reward: 1:{risk_mgmt['risk_reward_ratio']}")
            print(f"   ATR: ${risk_mgmt['atr']} ({risk_mgmt['atr_percentage']}%)")
        else:
            recommendation['strategy'] = 'structured'
            print(f"\n✅ [STRUCTURED] Decision made:")
            print(f"   Action: {recommendation['action']}")
            print(f"   Reasoning: {recommendation.get('reasoning', 'N/A')}")
        
        # Only update recommendation, don't return full state (for parallel execution)
        return {"recommendation_structured": recommendation}
        
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing AI response: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"   Response was: {response_text[:200]}...")
        return {"recommendation_structured": None}
    except Exception as e:
        error_msg = f"Error making decision: {str(e)}"
        print(f"❌ {error_msg}")
        return {"recommendation_structured": None}

