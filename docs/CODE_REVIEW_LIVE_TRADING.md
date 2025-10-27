# Code Review: Live Trading System

## Datum: 27.10.2025
## Reviewer: AI Assistant
## Soubory: `live_trading.py`, `binance_client.py`, `trading_bot_dynamic.py`

---

## 🟢 SILNÉ STRÁNKY

### 1. Bezpečnostní kontroly ✅
```python
# Řádek 36-44: Kontrola API credentials
if not binance.has_credentials:
    print("❌ No API credentials - LIVE TRADING DISABLED")
    return state
```
- ✅ Kontrola credentials před každým trade
- ✅ Graceful fallback pokud nejsou k dispozici

### 2. Balance Verification ✅
```python
# Řádek 258-262: Kontrola balance před trade
if available_balance < LIVE_POSITION_USD:
    log_data['execution_reason'] = f"Insufficient balance..."
    continue
```
- ✅ Předchází excessive leverage
- ✅ Jasné error messages

### 3. Position Conflict Detection ✅
```python
# Řádek 136-141: Kontrola live positions
live_positions = binance.get_open_positions(symbol)
if strategy_open or live_positions:
    # Handle conflicts
```
- ✅ Kontroluje paper trading DB i Binance live pozice
- ✅ Předchází duplicate positions

### 4. Cooldown Management ✅
```python
# Řádek 234-242: 30min universal cooldown
cooldown_minutes = 30
if time_since_exit < cooldown_minutes:
    continue
```
- ✅ Universal 30 min cooldown pro všechny strategie
- ✅ Prevence overtrading

### 5. Error Handling ✅
```python
# Řádek 519-535: Comprehensive error handling
except Exception as e:
    print(f"❌ Failed to execute live trade: {str(e)}")
    traceback.print_exc()
    # Try to cancel partially filled orders
    binance.cancel_all_orders(symbol)
```
- ✅ Try-except bloky na kritických místech
- ✅ Automatic cleanup při failure
- ✅ Detailed logging

### 6. Database Logging ✅
```python
# Řádek 100-118: Kompletní logging včetně failed attempts
db_log.log_strategy_run(log_data)
```
- ✅ Loguje všechny pokusy (success i failed)
- ✅ Obsahuje reasoning, confidence, market data

### 7. Partial Exit Strategy ✅
```python
# Řádek 283-291: Rozdělené SL pro risk management
sl_partial1 = original_sl  # Original SL
sl_partial2 = entry - (entry - original_sl) * 0.5  # 50% tighter
```
- ✅ Smart risk management
- ✅ Break-even protection po TP1

---

## 🟡 POTENCIÁLNÍ PROBLÉMY

### 1. ⚠️ KRITICKÉ: Quantity Precision (Řádek 297-300)

**Problém:**
```python
# TODO: Get precision from exchange info
quantity_precision = 3  # HARDCODED!
size_partial = round(size_partial, quantity_precision)
```

**Dopad:**
- ❌ Může způsobit order rejection na Binance
- ❌ Některé symboly mají jinou precision (BTC=5, SOL=3, SHIB=0)

**Řešení:**
```python
# Fetch from exchange info
exchange_info = binance.client.futures_exchange_info()
symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
if symbol_info:
    for filter in symbol_info['filters']:
        if filter['filterType'] == 'LOT_SIZE':
            step_size = float(filter['stepSize'])
            quantity_precision = len(str(step_size).rstrip('0').split('.')[-1])
```

**Priority: HIGH** 🔴

---

### 2. ⚠️ VYSOKÁ: Missing Rate Limiting

**Problém:**
- ❌ Žádná kontrola API rate limits
- ❌ Při 4 strategiích = 4 strategie × 5 orders = 20 orders per cycle
- ❌ Binance má limit 1200 orders/minute

**Dopad:**
- Může způsobit API ban
- Failed orders při high-frequency trading

**Řešení:**
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=50, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def wait_if_needed(self):
        now = time.time()
        # Remove old requests
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.requests[0] + self.time_window - now
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.requests.append(now)
```

**Priority: HIGH** 🔴

---

### 3. ⚠️ STŘEDNÍ: Hardcoded strategy_name check (Řádek 271)

**Problém:**
```python
if strategy_name == 'intraday2' and 'take_profit_1' in risk_mgmt:
```

**Dopad:**
- ❌ Tight coupling na specific strategy name
- ❌ Co když přejmenujeme strategii?

**Řešení:**
```python
# Check presence of fields, not strategy name
if 'take_profit_1' in risk_mgmt and 'take_profit_2' in risk_mgmt:
    partial_tp = risk_mgmt['take_profit_1']
    full_tp = risk_mgmt['take_profit_2']
else:
    # Standard calculation
```

**Priority: MEDIUM** 🟡

---

### 4. ⚠️ STŘEDNÍ: Database Connection Management (Řádek 449-492)

**Problém:**
```python
conn = db.conn = __import__('sqlite3').connect(db.db_path)
# ... manual SQL ...
conn.commit()
conn.close()
```

**Dopad:**
- Není v transaction
- Pokud spadne mezi partial1 a partial2 insert → inconsistent state

**Řešení:**
```python
try:
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # Use transaction
    conn.execute('BEGIN TRANSACTION')
    
    for tid, tdata in [...]:
        cursor.execute(...)
    
    conn.commit()  # Atomic commit
except Exception as e:
    conn.rollback()  # Rollback on error
    raise
finally:
    conn.close()
```

**Priority: MEDIUM** 🟡

---

### 5. ⚠️ NÍZKÁ: Symbol extraction (Řádek 318)

**Problém:**
```python
print(f"   Quantity: {total_quantity} {symbol[:3]} (split to 2 partials)")
```

**Dopad:**
- Pro "BTCUSDT" → "BTC" ✅
- Pro "1000SHIBUSDT" → "100" ❌

**Řešení:**
```python
base_asset = symbol.replace('USDT', '').replace('BUSD', '')
print(f"   Quantity: {total_quantity} {base_asset}...")
```

**Priority: LOW** 🟢

---

### 6. ⚠️ NÍZKÁ: LIVE_POSITION_SIZE každý loop (Řádek 255)

**Problém:**
```python
LIVE_POSITION_USD = float(os.getenv('LIVE_POSITION_SIZE', '100'))  # Inside loop!
```

**Dopad:**
- Inefficient - čte env var každý iteration
- Mělo by být načteno jednou v config.py

**Řešení:**
```python
# Use from config directly
LIVE_POSITION_USD = config.LIVE_POSITION_SIZE
```

**Priority: LOW** 🟢

---

### 7. ⚠️ STŘEDNÍ: No Partial Fill Handling

**Problém:**
- Pokud entry order je partially filled → SL/TP quantity bude wrong

**Dopad:**
```
Order: BUY 1.0 SOL
Filled: 0.8 SOL (partially)
SL: SELL 1.0 SOL ❌ (wrong quantity!)
```

**Řešení:**
```python
order = binance.place_market_order(...)

# Check actual filled quantity
actual_quantity = float(order['executedQty'])
if actual_quantity < total_quantity:
    print(f"⚠️ Partially filled: {actual_quantity}/{total_quantity}")
    # Adjust SL/TP quantities
    size_partial = actual_quantity / 2
```

**Priority: MEDIUM** 🟡

---

### 8. ⚠️ NÍZKÁ: Cooldown používá state['symbol'] místo symbol (Řádek 216)

**Problém:**
```python
cursor.execute("""
    SELECT exit_time, exit_price, exit_reason 
    FROM trades 
    WHERE strategy = ? AND symbol = ? AND status = 'CLOSED'
    ORDER BY exit_time DESC 
    LIMIT 1
""", (strategy_name, state['symbol']))  # ← Používá state['symbol']!
```

**Dopad:**
- Pro eth_fast (ETHUSDT) by měl hledat v ETHUSDT
- Ale hledá v state['symbol'] = SOLUSDT (default)

**Řešení:**
```python
""", (strategy_name, symbol))  # Use `symbol` variable instead
```

**Priority: MEDIUM** 🟡

---

### 9. ⚠️ INFORMAČNÍ: Missing Order ID tracking

**Observation:**
- Entry order ID se loguje ✅
- SL/TP order IDs se logují ✅
- ALE: Není způsob jak zjistit kdy se SL/TP vyplní (bot to nedetekuje)

**Důsledek:**
- Trades zůstanou "OPEN" v databázi i když jsou zavřené na Binance
- Potřeba sync mechanismus

**Řešení:**
```python
# Periodic sync job
def sync_live_positions():
    """Sync database with actual Binance positions"""
    open_trades = db.get_open_trades()
    live_positions = binance.get_open_positions()
    
    for trade in open_trades:
        if trade['live_trade']:
            # Check if still open on Binance
            pos = next((p for p in live_positions if p['symbol'] == trade['symbol']), None)
            if not pos:
                # Position closed on Binance, update DB
                db.close_trade(trade['trade_id'], ..., exit_reason='BINANCE_CLOSED')
```

**Priority: MEDIUM** 🟡

---

## 🔴 BEZPEČNOSTNÍ RIZIKA

### 1. 🚨 KRITICKÉ: No Maximum Position Limit

**Problém:**
- Žádný limit na total exposure
- Pokud 4 strategie všechny signalizují LONG → 4 × $100 = $400 exposure

**Řešení:**
```python
# Add global exposure check
total_exposure = sum(
    pos['position_amt'] * pos['entry_price'] 
    for pos in binance.get_open_positions()
)

MAX_TOTAL_EXPOSURE = 1000  # $1000 max
if total_exposure + LIVE_POSITION_USD > MAX_TOTAL_EXPOSURE:
    print(f"⚠️ Max exposure reached: ${total_exposure:.2f}")
    continue
```

**Priority: CRITICAL** 🔴🔴🔴

---

### 2. 🚨 VYSOKÉ: No Emergency Stop Mechanism

**Problém:**
- Pokud API selže při placing SL → position bez SL!
- Neomezená loss

**Řešení:**
```python
# After entry order
if not sl1_order or not sl2_order:
    # Emergency: Close position immediately
    print("🚨 EMERGENCY: Failed to place SL, closing position!")
    binance.place_market_order(
        symbol=symbol,
        side='SELL' if action == 'LONG' else 'BUY',
        quantity=total_quantity,
        reduce_only=True
    )
    raise Exception("Failed to place stop loss - position emergency closed")
```

**Priority: CRITICAL** 🔴🔴

---

### 3. 🚨 STŘEDNÍ: No Leverage Check

**Problém:**
- Kod nenastavuje leverage
- Používá co je nastaveno na účtu (může být 125x!)

**Řešení:**
```python
# Before trading
try:
    leverage_info = binance.set_leverage(symbol, 1)  # 1x for safety
    print(f"✅ Leverage set to 1x for {symbol}")
except Exception as e:
    print(f"⚠️ Failed to set leverage: {e}")
```

**Priority: HIGH** 🔴

---

## 📊 CODE QUALITY

### Pozitivní:
- ✅ Čitelný kód s dobrými komentáři
- ✅ Konzistentní naming conventions
- ✅ Dobré error messages
- ✅ Comprehensive logging

### Negativní:
- ❌ Příliš dlouhá funkce (571 řádků) - měla by být rozdělena
- ❌ Některé TODO komentáře (quantity precision)
- ❌ Hardcoded values (precision, strategy names)

---

## 🎯 DOPORUČENÉ ÚPRAVY

### Priority 1 (CRITICAL) - Implementovat IHNED:
1. ✅ **Max total exposure limit** (řádek před trade execution)
2. ✅ **Emergency SL verification** (po placing entry order)
3. ✅ **Leverage control** (nastavit 1x před tradingem)
4. ✅ **Dynamic quantity precision** (fetch from exchange)

### Priority 2 (HIGH) - Implementovat brzy:
5. ⚠️ **Rate limiting** (před API calls)
6. ⚠️ **Partial fill handling** (po entry order)
7. ⚠️ **Cooldown symbol fix** (použít správný symbol)

### Priority 3 (MEDIUM) - Vylepšení:
8. 🟡 **Transaction safety** (atomic DB commits)
9. 🟡 **Position sync mechanism** (periodic sync s Binance)
10. 🟡 **Remove hardcoded strategy names** (use duck typing)

### Priority 4 (LOW) - Nice to have:
11. 🟢 **Refactor to smaller functions** (rozdělení 571-line funkce)
12. 🟢 **Config optimization** (load LIVE_POSITION_SIZE jednou)
13. 🟢 **Better symbol parsing** (base asset extraction)

---

## 📝 OBECNÉ ZÁVĚRY

### ✅ CO FUNGUJE DOBŘE:
1. Bezpečnostní kontroly (credentials, balance, conflicts)
2. Error handling a logging
3. Cooldown management
4. Partial exit strategie
5. Database tracking

### ⚠️ CO POTŘEBUJE ZLEPŠENÍ:
1. **Quantity precision** (může způsobit order rejection)
2. **Rate limiting** (risk API ban)
3. **Max exposure** (risk overleverage)
4. **SL emergency check** (risk unlimited loss)
5. **Leverage control** (risk excessive leverage)

### 🎯 CELKOVÉ HODNOCENÍ:

| Kategorie | Hodnocení | Poznámka |
|-----------|-----------|----------|
| **Bezpečnost** | 7/10 | Dobré základy, chybí exposure limits a leverage control |
| **Error Handling** | 8/10 | Comprehensive, ale chybí partial fill handling |
| **Code Quality** | 7/10 | Čitelné, ale příliš dlouhé funkce |
| **Logging** | 9/10 | Výborné, comprehensive tracking |
| **Production Ready** | 6/10 | Potřebuje critical fixes před production |

---

## 🚀 AKČNÍ PLÁN

### Před spuštěním v production:
- [ ] Fix quantity precision (fetch from exchange)
- [ ] Implement max exposure limit
- [ ] Add SL emergency verification
- [ ] Set leverage to 1x
- [ ] Add rate limiting
- [ ] Fix cooldown symbol bug

### První týden produkce:
- [ ] Monitor API rate limits
- [ ] Check for partial fills
- [ ] Verify SL/TP placement success rate
- [ ] Test emergency scenarios

### Průběžné vylepšování:
- [ ] Refactor do menších funkcí
- [ ] Implement position sync
- [ ] Add monitoring/alerts
- [ ] Performance optimization

---

**Závěr:** Systém má dobré základy a bezpečnostní kontroly, ale před plným production use potřebuje několik critical fixes. S těmito úpravami bude ready pro safe live trading. 🎯

