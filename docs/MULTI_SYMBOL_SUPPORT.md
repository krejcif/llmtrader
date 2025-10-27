# Multi-Symbol Support Implementation

## 🎯 Overview

Implementace **Fáze 1** a **Fáze 2** multi-symbol supportu pro trading bot. Každá strategie nyní může tradovat vlastní symbol s backward compatibility (výchozí `config.SYMBOL`).

## ✅ Implementované změny

### 1. **Strategy Configuration** (`src/strategy_config.py`)

```python
class StrategyConfig:
    def __init__(self, name: str, decision_func, timeframe_higher: str, 
                 timeframe_lower: str, interval_minutes: int, enabled: bool = True,
                 analysis_func=None, symbol: str = None):
        """
        Args:
            symbol: Trading symbol (e.g., 'SOLUSDT', 'BTCUSDT'). Defaults to config.SYMBOL
        """
        self.name = name
        self.symbol = symbol if symbol is not None else config.SYMBOL  # ← NEW
        # ...
```

**Výhody:**
- ✅ **Backward compatible** - existující strategie bez `symbol` parametru používají `config.SYMBOL`
- ✅ **Flexibilní** - nové strategie mohou specifikovat vlastní symbol
- ✅ **Centralizované** - všechny symboly definovány v `strategy_config.py`

### 2. **Trading Bot** (`src/trading_bot_dynamic.py`)

```python
def run_strategy_wrapper(self, strategy, base_state):
    # Each thread gets its own copy of base state
    thread_state = deepcopy(base_state)
    
    # Set strategy-specific symbol (Fáze 2: multi-symbol support)
    thread_state['symbol'] = strategy.symbol  # ← NEW
    
    # Run strategy (modifies thread_state)
    result_state = self.run_strategy(strategy, thread_state)
```

**Výhody:**
- ✅ Každá strategie dostává vlastní `state['symbol']`
- ✅ Data collection automaticky používá správný symbol
- ✅ Funguje s paralelním execution

### 3. **Decision Agents** (všechny strategie)

Přidán symbol do každého recommendation objektu:

```python
recommendation['symbol'] = state['symbol']  # ← NEW

print(f"\n✅ [MINIMAL] Decision made:")
print(f"   Symbol: {state['symbol']}")  # ← NEW
print(f"   Action: {recommendation['action']}")
```

**Upravené soubory:**
- `src/agents/decision_minimal.py`
- `src/agents/decision_minimal_e725.py`
- `src/agents/decision_minimalbtc.py`
- `src/agents/decision_macro.py`
- `src/agents/decision_intraday.py`
- `src/agents/decision_example.py`

### 4. **Paper Trading** (`src/agents/paper_trading.py`)

```python
# Check if strategy already has open trade (RISK MANAGEMENT!)
db_check = TradingDatabase()
symbol = recommendation.get('symbol', state['symbol'])  # ← Use symbol from recommendation
existing_open = db_check.get_open_trades(symbol)

# TRADE 1 & 2: Use symbol from recommendation
trade_data_1 = {
    "symbol": recommendation.get('symbol', state['symbol']),  # ← Prefer from recommendation
    "strategy": strategy_name,
    # ...
}
```

**Výhody:**
- ✅ Paper trading respektuje symbol z recommendation
- ✅ Risk management kontroluje open trades per symbol
- ✅ Fallback na `state['symbol']` pro kompatibilitu

### 5. **Web API** (`src/web_api.py`)

```python
from strategy_config import STRATEGIES  # ← NEW import

@app.route('/api/stats')
def get_stats():
    # Create strategy symbol mapping from config
    strategy_symbols = {strategy.name: strategy.symbol for strategy in STRATEGIES}  # ← NEW
    
    return jsonify({
        'overall': stats_all,
        'strategies': {...},
        'strategy_symbols': strategy_symbols  # ← NEW: Add symbol mapping
    })
```

**Výhody:**
- ✅ Frontend dostává symbol mapping pro každou strategii
- ✅ Dynamické - vždy aktuální z `strategy_config.py`

### 6. **Dashboard UI** (`web/index.html`)

```javascript
async function loadStats() {
    const response = await fetch('/api/stats');
    const data = await response.json();
    
    // Store strategy symbols for later use (Fáze 2: multi-symbol support)
    window.strategySymbols = data.strategy_symbols || {};  // ← NEW
    
    // Display symbol in strategy titles
    const minimalSymbol = window.strategySymbols['minimal'] || 'SOLUSDT';
    document.getElementById('minimalTitle').textContent = `🤖 Minimal (${minimalSymbol})`;
}
```

**Výhody:**
- ✅ Symbol zobrazován v nadpisu každé strategie
- ✅ Fallback na 'SOLUSDT' pro kompatibilitu
- ✅ Automaticky update při změně v config

## 📋 Příklad použití

### Výchozí (všechny strategie = stejný symbol)

```python
# strategy_config.py
STRATEGIES = [
    StrategyConfig(
        name="minimal",
        # symbol není specifikován → použije config.SYMBOL
        decision_func=make_decision_minimal,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
]
```

### Multi-symbol (každá strategie = vlastní symbol)

```python
# strategy_config.py
STRATEGIES = [
    StrategyConfig(
        name="minimal",
        symbol="SOLUSDT",  # ← SOL/USDT
        decision_func=make_decision_minimal,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    StrategyConfig(
        name="minimal_btc",
        symbol="BTCUSDT",  # ← BTC/USDT
        decision_func=make_decision_minimal,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
    StrategyConfig(
        name="minimal_e725_eth",
        symbol="ETHUSDT",  # ← ETH/USDT
        decision_func=make_decision_minimal_e725,
        analysis_func=analyze_market_minimal_e725,
        timeframe_higher="1h",
        timeframe_lower="15m",
        interval_minutes=15,
        enabled=True
    ),
]
```

## ✅ Backward Compatibility

- ✅ **Existující strategie bez `symbol` parametru** → používají `config.SYMBOL`
- ✅ **Database** → žádné změny (symbol už byl uložen v trades)
- ✅ **Paper trading** → fallback na `state['symbol']`
- ✅ **Dashboard** → fallback na 'SOLUSDT' pokud symbol není dostupný

## 🎯 Výhody implementace

### **Diverzifikace**
```
MINIMAL (SOL)   → Volatilní, rychlé pohyby
MINIMAL (BTC)   → Stabilnější, trending
MINIMAL (ETH)   → Mix BTC/SOL vlastností
MACRO (BTC)     → Long-term macro trends
```

### **Specialization**
- Některé strategie fungují lépe na určitých symbolech
- EMA 7/25 může být lepší pro volatilní altcoiny
- EMA 20/50 může být lepší pro BTC long-term

### **Testing**
- Otestovat strategii na různých symbolech paralelně
- Porovnat performance na SOL vs BTC vs ETH

### **Risk Management**
- Rozložení rizika přes více assetů
- Max $10k per strategy (diverzifikace kapitálu)

## ⚠️ Considerations

### **Kapitál**
```
4 strategie × $10k = $40k celkem potřeba
```

### **API Rate Limits**
- Více symbolů = více Binance API calls
- S paralelním execution: všechny najednou (OK ✅)

### **Position Management**
- Každá strategie sleduje vlastní open trades per symbol
- Risk management: max 1 position per strategy per symbol

## 🚀 Další kroky (budoucnost - Fáze 3)

### **Symbol-specific position sizing**
```python
# Volatilnější asset = menší position
if symbol == 'SOLUSDT':
    position_usd = 8000  # Více volatilní
elif symbol == 'BTCUSDT':
    position_usd = 12000  # Stabilnější
```

### **Cross-symbol correlation analysis**
```python
# Nepřidávat SOL LONG pokud už máme ETH LONG (korelace)
if has_open_position('ETHUSDT', 'LONG'):
    reduce_position_size('SOLUSDT')
```

### **Portfolio rebalancing**
```python
# Udržovat balanci mezi symboly
if btc_exposure > 0.6:  # Více než 60% v BTC
    reduce_btc_entries()
```

## 📊 Dashboard zobrazení

```
🤖 Minimal (SOLUSDT)
   Win Rate: 65%
   P&L: $1,234

⚡ Minimal E725 (ETHUSDT)
   Win Rate: 58%
   P&L: $876

₿ MinimalBTC (BTCUSDT)
   Win Rate: 72%
   P&L: $2,100
```

## ✅ Status: IMPLEMENTED

- ✅ Fáze 1: Basic symbol support v `StrategyConfig`
- ✅ Fáze 2: Symbol propagace přes bot → decision agents → paper trading → dashboard
- ⏳ Fáze 3: Advanced features (budoucnost)

---

*Implementováno: 2025-10-27*
*Verze: 1.0*

