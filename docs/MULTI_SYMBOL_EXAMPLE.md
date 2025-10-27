# Multi-Symbol Support - Příklad použití

## ✅ Implementace dokončena!

Multi-symbol support je plně funkční. Každá strategie může nyní tradovat vlastní symbol.

## 📋 Jak to použít

### Krok 1: Upravit `strategy_config.py`

```python
from agents.decision_minimal import make_decision_minimal
from agents.decision_minimal_e725 import make_decision_minimal_e725
from agents.analysis_minimal_e725 import analyze_market_minimal_e725
import config

STRATEGIES = [
    # MINIMAL - Trading SOLUSDT (výchozí)
    StrategyConfig(
        name="minimal",
        symbol="SOLUSDT",  # ← Explicitně SOL/USDT
        decision_func=make_decision_minimal,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # MINIMAL_E725 - Trading ETHUSDT (rychlé EMA na ETH)
    StrategyConfig(
        name="minimal_e725",
        symbol="ETHUSDT",  # ← ETH/USDT
        decision_func=make_decision_minimal_e725,
        analysis_func=analyze_market_minimal_e725,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # MINIMAL_BTC - Trading BTCUSDT (BTC s BTC contextem)
    StrategyConfig(
        name="minimalbtc",
        symbol="BTCUSDT",  # ← BTC/USDT
        decision_func=make_decision_minimalbtc,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    
    # MACRO - Trading SOLUSDT (long-term macro)
    StrategyConfig(
        name="macro",
        # symbol není specifikován → použije config.SYMBOL
        decision_func=make_decision_macro,
        timeframe_higher="1d",
        timeframe_lower="4h",
        interval_minutes=240,
        enabled=True
    ),
]
```

### Krok 2: Restartovat bota

```bash
./bot.sh restart-all
```

### Krok 3: Ověřit v dashboardu

Dashboard nyní zobrazí:
```
🤖 Minimal (SOLUSDT)
   Win Rate: 65%
   
⚡ Minimal E725 (ETHUSDT)
   Win Rate: 58%
   
₿ MinimalBTC (BTCUSDT)
   Win Rate: 72%
   
🌍 Macro (SOLUSDT)
   Win Rate: 60%
```

## 🎯 Ukázkové scénáře

### Scénář 1: Diverzifikace (SOL + BTC + ETH)

```python
STRATEGIES = [
    StrategyConfig(name="minimal", symbol="SOLUSDT", ...),      # SOL
    StrategyConfig(name="minimal_e725", symbol="ETHUSDT", ...),  # ETH
    StrategyConfig(name="minimalbtc", symbol="BTCUSDT", ...),    # BTC
]

# Kapitál: 3 strategie × $10k = $30k
# Diverzifikace: SOL (volatilní) + ETH (mid) + BTC (stabilní)
```

### Scénář 2: Specialization (různé strategie na stejném symbolu)

```python
STRATEGIES = [
    StrategyConfig(name="minimal", symbol="BTCUSDT", ...),       # EMA 20/50 na BTC
    StrategyConfig(name="minimal_e725", symbol="BTCUSDT", ...),  # EMA 7/25 na BTC
    StrategyConfig(name="macro", symbol="BTCUSDT", ...),         # Long-term na BTC
]

# Kapitál: 3 strategie × $10k = $30k na BTCUSDT
# Různé timeframy a logiky na stejném assetu
```

### Scénář 3: Testing (jedna strategie na více symbolech)

```python
STRATEGIES = [
    StrategyConfig(name="minimal_sol", symbol="SOLUSDT", ...),
    StrategyConfig(name="minimal_eth", symbol="ETHUSDT", ...),
    StrategyConfig(name="minimal_btc", symbol="BTCUSDT", ...),
]

# Porovnání stejné strategie na různých symbolech
# Zjistíme, na kterém symbolu strategie funguje nejlépe
```

## 📊 Co se zobrazí v logu

```
✅ [MINIMAL] Decision made:
   Symbol: SOLUSDT
   Action: LONG
   Entry: $142.50

✅ [MINIMAL_E725] Decision made:
   Symbol: ETHUSDT
   Action: SHORT
   Entry: $2,450.00

✅ [MINIMALBTC] Decision made:
   Symbol: BTCUSDT
   Action: NEUTRAL
   Entry: N/A
```

## 🔄 Backward Compatibility

**Bez specifikace symbolu:**
```python
StrategyConfig(name="minimal", decision_func=make_decision_minimal, ...)
# → Použije config.SYMBOL (výchozí SOLUSDT)
```

**Se specifikací symbolu:**
```python
StrategyConfig(name="minimal", symbol="ETHUSDT", decision_func=make_decision_minimal, ...)
# → Použije ETHUSDT
```

## ✅ Co je implementováno

1. ✅ **StrategyConfig** - parametr `symbol` s fallback na `config.SYMBOL`
2. ✅ **Trading Bot** - propagace `symbol` do `state`
3. ✅ **Decision Agents** - přidání `symbol` do recommendation
4. ✅ **Paper Trading** - použití `symbol` z recommendation
5. ✅ **Web API** - endpoint vrací `strategy_symbols` mapping
6. ✅ **Dashboard** - zobrazení symbolu v titulku každé strategie
7. ✅ **Risk Management** - kontrola open trades per symbol
8. ✅ **Logging** - symbol v decision výpisu

## 🚀 Další kroky (volitelné)

### Pokročilé features (budoucnost)

1. **Symbol-specific position sizing**
   ```python
   if symbol == 'SOLUSDT':
       position_usd = 8000  # Volatilnější
   elif symbol == 'BTCUSDT':
       position_usd = 12000  # Stabilnější
   ```

2. **Cross-symbol correlation**
   ```python
   if has_open_long('ETHUSDT'):
       reduce_size_for('SOLUSDT')  # Korelace
   ```

3. **Portfolio rebalancing**
   ```python
   if btc_exposure > 0.6:  # >60% v BTC
       pause_btc_entries()
   ```

## 📝 Poznámky

- **API Rate Limits**: Více symbolů = více API calls, ale paralelní execution to řeší ✅
- **Kapitál**: Každá strategie = $10k position, plánuj celkový kapitál podle počtu strategií
- **Database**: Symbol je už v DB, žádné migrace potřeba ✅
- **Dashboard**: Symboly se zobrazují automaticky po restartu ✅

---

**Status**: ✅ PLNĚ FUNKČNÍ
**Verze**: 1.0
**Datum**: 2025-10-27

