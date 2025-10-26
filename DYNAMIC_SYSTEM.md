# Dynamický multi-strategický systém ✨

## Co bylo změněno

Vytvořil jsem **flexibilní, abstraktní systém** pro snadné přidávání trading strategií s různými timeframes a intervaly.

### ✅ Původní požadavek

- **Intraday** strategie běží každých **5 minut** s timeframes **5m/15m**
- **Ostatní strategie** (minimal, structured, minimalbtc, macro) běží každých **15 minut** s timeframes **1h/15m**

### 🚀 Nový systém umožňuje

- ✅ Snadno přidávat nové strategie (3 kroky)
- ✅ Různé timeframes pro každou strategii (1m, 5m, 15m, 1h, 4h...)
- ✅ Různé intervaly běhu (1, 5, 15, 30, 60 minut...)
- ✅ Žádné hard-coded workflow
- ✅ Automatická orchestrace
- ✅ Každá strategie má svá vlastní data a analýzu

## Nové soubory

### 1. Konfigurace
- **`src/strategy_config.py`** - Centrální konfigurace všech strategií
- **`src/agents/decision_example.py`** - Template pro nové strategie
- **`STRATEGIE_HOWTO.md`** - Návod jak přidat strategii

### 2. Generické moduly
- **`src/agents/data_collector_generic.py`** - Sběr dat pro libovolné timeframes
- **`src/agents/analysis_generic.py`** - Analýza pro libovolné timeframes
- **`src/agents/decision_generic.py`** - Wrapper pro decision funkce

### 3. Bot
- **`src/trading_bot_dynamic.py`** - Nový dynamický bot
- **`test_dynamic_system.py`** - Test systému

## Aktuální strategie

Po implementaci máte:

| Strategie   | Timeframes | Interval | Popis                          |
|-------------|------------|----------|--------------------------------|
| structured  | 1h/15m     | 15 min   | Strukturovaná strategie        |
| minimal     | 1h/15m     | 15 min   | Minimální prompt               |
| minimalbtc  | 1h/15m     | 15 min   | Minimal + BTC kontext          |
| macro       | 1h/15m     | 15 min   | Makro fundamenty               |
| **intraday**| **15m/5m** | **5 min**| **Rychlá intraday (NOVÉ TF)** ⚡|
| example     | 1h/15m     | 15 min   | Template (disabled)            |

## Jak spustit

### Nový dynamický bot (doporučeno)
```bash
cd src
python3 trading_bot_dynamic.py
```

### Test systému
```bash
python3 test_dynamic_system.py
```

## Jak přidat novou strategii (3 kroky)

### Krok 1: Vytvoř decision funkci
`src/agents/decision_moje.py`:
```python
def make_decision_moje(state):
    # Tvoje logika
    return {"recommendation_moje": recommendation}
```

### Krok 2: Zaregistruj v konfigu
`src/strategy_config.py`:
```python
from agents.decision_moje import make_decision_moje

STRATEGIES = [
    # ... existující ...
    
    StrategyConfig(
        name="moje",
        decision_func=make_decision_moje,
        timeframe_higher="4h",  # Vyšší TF
        timeframe_lower="1h",   # Nižší TF
        interval_minutes=60,    # Každých 60 min
        enabled=True
    ),
]
```

### Krok 3: Spusť
```bash
python3 trading_bot_dynamic.py
```

**To je vše!** Žádné další změny nejsou potřeba.

## Příklady konfigurací

### Ultra-fast scalper (1m candles, běží každou minutu)
```python
StrategyConfig(
    name="scalper_ultra",
    decision_func=make_decision_scalper_ultra,
    timeframe_higher="5m",
    timeframe_lower="1m",
    interval_minutes=1,
    enabled=True
)
```

### Swing trading (4h/1h, každou hodinu)
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

### Position trading (1d/4h, každé 4 hodiny)
```python
StrategyConfig(
    name="position",
    decision_func=make_decision_position,
    timeframe_higher="1d",
    timeframe_lower="4h",
    interval_minutes=240,
    enabled=True
)
```

## Výhody nového systému

### Před (původní systém)
❌ Hard-coded workflow  
❌ Pevné timeframes  
❌ Stejný interval pro všechny  
❌ Těžké přidávání strategií (změny v workflow)  

### Nyní (dynamický systém)
✅ Konfigurovatelné workflow  
✅ Libovolné timeframes pro každou strategii  
✅ Různé intervaly běhu  
✅ Snadné přidávání (jen config)  
✅ Automatická orchestrace  
✅ Škálovatelné  

## Architektura

```
User Config (strategy_config.py)
         ↓
┌────────────────────────────────────┐
│   Dynamic Trading Bot              │
│                                    │
│   • Načte aktivní strategie        │
│   • Spouští podle intervalů        │
│   • Paralelní data collection      │
│   • Automatická orchestrace        │
└────────────────────────────────────┘
         ↓
┌─────────────────────┬──────────────┐
│ Strategy 1 (5min)   │ Strategy 2-5 │
│ • Collect 15m/5m    │ • Collect    │
│ • Analyze           │   1h/15m     │
│ • Decide            │ • Analyze    │
└─────────────────────┤ • Decide     │
                      └──────────────┘
         ↓
    Execute Trades (paper)
```

## Kompatibilita

- ✅ Stejná databáze jako původní bot
- ✅ Stejný paper trading systém
- ✅ Stejný web dashboard
- ✅ Zachována všechna data

Můžete používat oba boty paralelně (ne současně!).

## Soubory k odstranění (deprecated)

Po přechodu na dynamický systém můžete smazat:
- `src/agents/data_collector_intraday.py` (použit generic)
- `src/agents/analysis_intraday.py` (použit generic)

Original bot (`trading_bot.py`) zůstává pro zpětnou kompatibilitu.

## Status implementace

✅ Všechny TODO hotové  
✅ Všechny testy prošly  
✅ 5 aktivních strategií  
✅ 2 intervaly (5 min, 15 min)  
✅ Template strategie (example)  
✅ Dokumentace  

## Další kroky (volitelné)

1. Přejít na `trading_bot_dynamic.py` jako hlavní bot
2. Přidat více strategií podle potřeby
3. Experimentovat s různými timeframes
4. Upravit cooldown periody v `paper_trading.py` pro nové strategie

---

**🎉 Systém je připraven!**

Nyní můžete snadno přidávat strategie s jakýmikoliv timeframes a intervaly, bez změn v bot logice.

