# Jak přidat novou trading strategii

## Přehled nového systému

Nový dynamický systém umožňuje snadno přidávat strategie s různými:
- **Timeframes** (např. 1h/15m, 15m/5m, 5m/1m)
- **Intervaly** (každých 1, 5, 15 minut atd.)
- **Decision logikou** (vlastní AI prompty, rules-based atd.)

## Rychlý start: Přidání nové strategie

### Krok 1: Vytvořte decision funkci

Vytvořte soubor `src/agents/decision_<název>.py`:

```python
"""Decision Agent - <Název> Strategy"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from openai import OpenAI
from utils.indicators import calculate_stop_take_profit
import config
import json


def make_decision_<název>(state: TradingState) -> TradingState:
    """
    <Popis strategie>
    """
    print(f"\n🎯 [<NÁZEV>] Making decision...")
    
    try:
        # Kontrola dat
        if state.get('error') or not state.get('analysis'):
            print("❌ Cannot make decision - no analysis")
            return {"recommendation_<název>": None}
        
        market_data = state['market_data']
        analysis = state['analysis']
        indicators = analysis['indicators']
        ind_higher = indicators['higher_tf']['indicators']
        ind_lower = indicators['lower_tf']['indicators']
        tf_higher = indicators['higher_tf']['timeframe']
        tf_lower = indicators['lower_tf']['timeframe']
        
        # Initialize DeepSeek client
        client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL
        )
        
        # Váš vlastní prompt
        prompt = f"""Your trading prompt here...
        
Current price: ${market_data['current_price']}
Higher TF ({tf_higher}): RSI={ind_higher['rsi']['value']}...
Lower TF ({tf_lower}): RSI={ind_lower['rsi']['value']}...

Respond with JSON:
{{
  "action": "LONG",
  "confidence": "high",
  "reasoning": "...",
  "key_factors": ["factor1", "factor2"]
}}"""
        
        # Call AI
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an expert trader..."},
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
        
        # Calculate risk management
        if recommendation['action'] in ['LONG', 'SHORT']:
            candles_lower = market_data['timeframes'][tf_lower]
            direction = 'bullish' if recommendation['action'] == 'LONG' else 'bearish'
            risk_mgmt = calculate_stop_take_profit(candles_lower, direction)
            
            recommendation['risk_management'] = risk_mgmt
            recommendation['strategy'] = '<název>'
            
            print(f"\n✅ [<NÁZEV>] Decision: {recommendation['action']}")
            print(f"   Entry: ${risk_mgmt['entry']} | SL: ${risk_mgmt['stop_loss']} | TP: ${risk_mgmt['take_profit']}")
        else:
            recommendation['strategy'] = '<název>'
            print(f"\n✅ [<NÁZEV>] Decision: {recommendation['action']}")
        
        return {"recommendation_<název>": recommendation}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"recommendation_<název>": None}
```

### Krok 2: Zaregistrujte strategii v konfiguraci

Editujte `src/strategy_config.py` a přidejte novou strategii do seznamu `STRATEGIES`:

```python
from agents.decision_<název> import make_decision_<název>

STRATEGIES = [
    # ... existující strategie ...
    
    # Nová strategie
    StrategyConfig(
        name="<název>",
        decision_func=make_decision_<název>,
        timeframe_higher="15m",  # Vyšší timeframe
        timeframe_lower="5m",     # Nižší timeframe
        interval_minutes=5,       # Jak často běží (5 min)
        enabled=True              # Zapnout/vypnout
    ),
]
```

### Krok 3: Spusťte bota

```bash
cd src
python trading_bot_dynamic.py
```

To je vše! Strategie se automaticky načte a začne běžet.

## Příklady konfigurací

### Rychlý scalper (1m/5m, každou minutu)
```python
StrategyConfig(
    name="scalper",
    decision_func=make_decision_scalper,
    timeframe_higher="5m",
    timeframe_lower="1m",
    interval_minutes=1,
    enabled=True
)
```

### Swing trading (4h/1h, každých 60 minut)
```python
StrategyConfig(
    name="swing",
    decision_func=make_decision_swing,
    timeframe_higher="4h",
    timeframe_lower="1h",
    interval_minutes=60,
    enabled=True
)
```

### Day trading (1h/15m, každých 15 minut)
```python
StrategyConfig(
    name="daytrader",
    decision_func=make_decision_daytrader,
    timeframe_higher="1h",
    timeframe_lower="15m",
    interval_minutes=15,
    enabled=True
)
```

## Aktuální strategie

Po implementaci máte:

1. **structured** - 1h/15m, každých 15 min
2. **minimal** - 1h/15m, každých 15 min
3. **minimalbtc** - 1h/15m, každých 15 min
4. **macro** - 1h/15m, každých 15 min
5. **intraday** - 15m/5m, každých 5 min ⚡

## Výhody nového systému

✅ Snadno přidáváte nové strategie  
✅ Různé timeframes pro různé strategie  
✅ Různé intervaly běhu  
✅ Žádné hard-coded workflow  
✅ Každá strategie má svá vlastní data a analýzu  
✅ Flexibilní škálování  

## Struktura souborů

```
src/
├── strategy_config.py              # Konfigurace strategií
├── trading_bot_dynamic.py          # Dynamický bot
├── agents/
│   ├── decision_<název>.py        # Vaše decision funkce
│   ├── data_collector_generic.py  # Generický sběr dat
│   ├── analysis_generic.py        # Generická analýza
│   └── decision_generic.py        # Generický wrapper
└── ...
```

## Přepnutí z původního bota

Původní bot: `python trading_bot.py`  
Nový dynamický bot: `python trading_bot_dynamic.py`

Oba boty používají stejnou databázi a jsou kompatibilní.

