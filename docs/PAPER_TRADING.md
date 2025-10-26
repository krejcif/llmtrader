# Paper Trading System 💼

## Přehled

Paper Trading Agent automaticky **simuluje a ukládá každý trading signál** do SQLite databáze. To umožňuje sledovat performance systému bez reálného rizika.

---

## 🎯 Co je Paper Trading?

**Paper Trading** = Simulované obchodování bez reálných peněz.

**Výhody:**
✅ Testování strategie bez rizika  
✅ Sledování performance  
✅ Učení se a zlepšování  
✅ Proof of concept před real trading  
✅ Statistical analysis  

---

## 🔄 Workflow

```
1. DeepSeek AI → LONG/SHORT doporučení
   ↓
2. ATR-based SL/TP calculation
   ↓
3. Paper Trading Agent
   │
   ├─→ Vytvoří trade record
   ├─→ Uloží do SQLite DB
   ├─→ Zobrazí trade ID
   └─→ Zobrazí statistics
```

---

## 💾 Database Schema

### Trades Table

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    trade_id TEXT UNIQUE,           -- SOLUSDT_20251023_123456
    symbol TEXT,                     -- SOLUSDT
    action TEXT,                     -- LONG/SHORT
    confidence TEXT,                 -- low/medium/high
    entry_price REAL,               -- $190.38
    stop_loss REAL,                 -- $185.20
    take_profit REAL,               -- $200.74
    risk_amount REAL,               -- $5.18
    reward_amount REAL,             -- $10.36
    risk_reward_ratio REAL,         -- 2.0
    atr REAL,                       -- $3.45
    entry_setup TEXT,               -- pullback_reversal
    status TEXT,                    -- OPEN/CLOSED
    entry_time TEXT,                -- ISO timestamp
    exit_time TEXT,                 -- ISO timestamp (if closed)
    exit_price REAL,                -- Exit price (if closed)
    exit_reason TEXT,               -- TP_HIT/SL_HIT/MANUAL
    pnl REAL,                       -- Profit/Loss in $
    pnl_percentage REAL,            -- P&L in %
    analysis_data TEXT,             -- JSON with full analysis
    reasoning TEXT,                 -- AI reasoning
    created_at TEXT                 -- Creation timestamp
)
```

---

## 📊 Trade Lifecycle

### 1. Trade Creation (OPEN)
```
System creates LONG @ $190.38
  ↓
Store in DB:
  - trade_id: SOLUSDT_20251023_123456
  - status: OPEN
  - entry: $190.38
  - stop: $185.20
  - tp: $200.74
```

### 2. Trade Monitoring
```
Options:
a) Manual check (trade_manager.py)
b) Automated check script
c) Price alerts
```

### 3. Trade Close (CLOSED)
```
When:
- Price hits Stop Loss ($185.20) → SL_HIT
- Price hits Take Profit ($200.74) → TP_HIT
- Manual close → MANUAL

Store:
  - status: CLOSED
  - exit_time: timestamp
  - exit_price: actual exit
  - exit_reason: TP_HIT/SL_HIT/MANUAL
  - pnl: calculated profit/loss
  - pnl_percentage: % return
```

---

## 🛠️ Trade Manager CLI

### List Trades

```bash
cd src
python trade_manager.py list

# Output:
====================================================================================================
📊 TRADES (ALL) - Last 10
====================================================================================================

Trade ID: SOLUSDT_20251023_123456
  Symbol: SOLUSDT
  Action: LONG | Confidence: high
  Entry: $190.38 | SL: $185.20 | TP: $200.74
  R/R: 1:2.0
  Setup: pullback_reversal
  Status: OPEN
  Entry Time: 2025-10-23T12:34:56

Trade ID: SOLUSDT_20251023_113045
  Symbol: SOLUSDT
  Action: SHORT | Confidence: medium
  Entry: $188.50 | SL: $194.20 | TP: $177.10
  R/R: 1:2.0
  Setup: aligned_running
  Status: CLOSED
  Exit: $177.10 | Reason: TP_HIT
  P&L: +$11.40 (+6.05%)
```

### Show Statistics

```bash
python trade_manager.py stats

# Output:
============================================================
📊 TRADING STATISTICS (ALL)
============================================================

Total Trades: 10
  Open: 3
  Closed: 7

Performance:
  Wins: 5
  Losses: 2
  Win Rate: 71.43%
  Total P&L: $45.67
  Avg P&L: 2.85%
  Rating: 🌟 Excellent
```

### Filter by Symbol

```bash
python trade_manager.py stats --symbol SOLUSDT
python trade_manager.py list --symbol SOLUSDT --limit 20
```

### Close Trade Manually

```bash
# Pokud chceš manually uzavřít trade (např. fundamentální změna)
python trade_manager.py close --trade-id SOLUSDT_20251023_123456 --price 195.50
```

---

## 📈 Tracking Performance

### Metrics Tracked

1. **Win Rate**: % profitable trades
2. **Total P&L**: Celkový profit/loss v $
3. **Average P&L %**: Průměrný % return per trade
4. **Open Trades**: Aktuálně running trades
5. **Entry Setups**: Which setups work best

### Performance Analysis

```sql
-- Best performing setups
SELECT entry_setup, 
       COUNT(*) as trades,
       AVG(pnl_percentage) as avg_pnl,
       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
FROM trades 
WHERE status = 'CLOSED'
GROUP BY entry_setup;

-- Results:
pullback_reversal: 75% win rate, +3.2% avg
aligned_running: 60% win rate, +1.8% avg
```

---

## 🎯 Typical Use Case

### Day 1: Setup
```bash
./run.sh
→ LONG @ $190, stored in DB
```

### Day 2-5: Monitor
```bash
python src/trade_manager.py list --status open
→ See open positions
```

### Day 6: Check if closed
```bash
# Manually check prices or run automated check
→ If TP hit: Auto-closed with profit
→ If SL hit: Auto-closed with loss
```

### Weekly: Review
```bash
python src/trade_manager.py stats
→ See win rate, total P&L
→ Analyze what works
```

---

## 🤖 Automated Trade Checking

Vytvořte script pro automatickou kontrolu open trades:

```python
# check_trades.py
from utils.binance_client import BinanceClient
from utils.database import TradingDatabase

db = TradingDatabase()
client = BinanceClient()

# Get open trades
open_trades = db.get_open_trades()

for trade in open_trades:
    current_price = client.get_current_price(trade['symbol'])
    
    # Check LONG
    if trade['action'] == 'LONG':
        if current_price <= trade['stop_loss']:
            db.close_trade(trade['trade_id'], trade['stop_loss'], 'SL_HIT')
            print(f"🛑 {trade['trade_id']}: Stop Loss hit")
        elif current_price >= trade['take_profit']:
            db.close_trade(trade['trade_id'], trade['take_profit'], 'TP_HIT')
            print(f"🎯 {trade['trade_id']}: Take Profit hit")
    
    # Check SHORT
    elif trade['action'] == 'SHORT':
        if current_price >= trade['stop_loss']:
            db.close_trade(trade['trade_id'], trade['stop_loss'], 'SL_HIT')
            print(f"🛑 {trade['trade_id']}: Stop Loss hit")
        elif current_price <= trade['take_profit']:
            db.close_trade(trade['trade_id'], trade['take_profit'], 'TP_HIT')
            print(f"🎯 {trade['trade_id']}: Take Profit hit")
```

Spusťte jako cron job každou hodinu.

---

## 📊 Example Trade Record

```json
{
  "trade_id": "SOLUSDT_20251023_123456",
  "symbol": "SOLUSDT",
  "action": "LONG",
  "confidence": "high",
  "entry_price": 190.38,
  "stop_loss": 185.20,
  "take_profit": 200.74,
  "risk_amount": 5.18,
  "reward_amount": 10.36,
  "risk_reward_ratio": 2.0,
  "atr": 3.45,
  "entry_setup": "pullback_reversal",
  "status": "OPEN",
  "entry_time": "2025-10-23T12:34:56",
  "analysis_data": {
    "confluence": "pullback_entry_long",
    "entry_quality": "pullback_reversal",
    "orderbook_pressure": "buy",
    "timeframe_higher": "1h",
    "timeframe_lower": "15m"
  },
  "reasoning": "Pullback reversal s excellent confirmací..."
}
```

---

## 🎓 Learning from Results

### After 20+ Trades

**Analyze:**
```bash
python src/trade_manager.py stats

Win Rate: 68%
Total P&L: +$156.80
Avg P&L: +2.4%
```

**Questions to ask:**
1. Který entry setup má vyšší win rate?
2. Která timeframe kombinace funguje lépe?
3. V jakých market conditions systém selhává?
4. Kdy má AI nejvyšší confidence?

### Improve Strategy

Based on data:
- Pokud pullback_reversal 80% win rate → preferuj je více
- Pokud aligned_running 45% win rate → buď opatrnější
- Pokud high volatility (ATR >3%) → adjust strategy

---

## 🔧 Advanced: Custom Queries

### SQLite Direct Access

```bash
sqlite3 data/paper_trades.db

# Example queries:
SELECT * FROM trades WHERE status = 'OPEN';
SELECT AVG(pnl_percentage) FROM trades WHERE action = 'LONG' AND status = 'CLOSED';
SELECT entry_setup, COUNT(*) FROM trades GROUP BY entry_setup;
```

### Python Script Analysis

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/paper_trades.db')
df = pd.read_sql_query("SELECT * FROM trades", conn)

# Analyze by setup type
print(df.groupby('entry_setup')['pnl_percentage'].agg(['mean', 'count', 'std']))

# Analyze by confidence
print(df.groupby('confidence')['pnl_percentage'].mean())

# Win rate by time of day
df['hour'] = pd.to_datetime(df['entry_time']).dt.hour
print(df.groupby('hour')['pnl'].apply(lambda x: (x > 0).sum() / len(x)))
```

---

## 🚀 Future Enhancements

### Planned:
- [ ] Automated SL/TP checking (background service)
- [ ] Email/Telegram notifications on TP/SL hits
- [ ] Web dashboard for trade visualization
- [ ] Equity curve tracking
- [ ] Drawdown analysis
- [ ] Monte Carlo simulation
- [ ] Risk of ruin calculation

### Maybe:
- [ ] Integration with real exchange (for real trading)
- [ ] Multi-account support
- [ ] Portfolio management
- [ ] Correlation analysis

---

## ⚠️ Limitations

**Paper Trading ≠ Real Trading:**

1. **No Slippage**: DB uses exact SL/TP prices
2. **No Fees**: Real trading má fees (0.02-0.04%)
3. **No Psychology**: Emotions v real trading jsou jiné
4. **Perfect Execution**: V realitě nemusíš dostat exact price
5. **No Market Impact**: V realitě velké ordery pohnou trhem

**Adjustment for Real Trading:**
- Reduce expected win rate o 5-10%
- Add fees to P&L calculations (~0.04% per trade)
- Add slippage buffer (~0.1% per trade)
- Test with smaller position sizes first

---

## 📊 Success Criteria

### Good Paper Trading Results:
```
Win Rate: >60%
Avg P&L: >1.5%
R/R Ratio: >1.5
Max consecutive losses: <5
Total trades: >30 (statistical significance)
```

### Ready for Real Trading:
```
✅ 50+ paper trades executed
✅ Win rate >65% sustained
✅ Positive P&L over 3+ months
✅ Understand why wins/losses happen
✅ Psychological readiness
✅ Risk management discipline
```

---

## 📚 Database Files

### Location
```
langtest/
└── data/
    ├── paper_trades.db      # Main database
    └── README.md           # Database info
```

### Backup
```bash
# Backup database
cp data/paper_trades.db data/paper_trades_backup_$(date +%Y%m%d).db

# Restore
cp data/paper_trades_backup_20251023.db data/paper_trades.db
```

---

## 🔍 Troubleshooting

### "Database locked"
```bash
# Close all connections
# Or restart system
```

### "No trades showing"
```bash
# Check database exists
ls -la data/paper_trades.db

# Check table exists
sqlite3 data/paper_trades.db "SELECT COUNT(*) FROM trades;"
```

### "Wrong P&L calculation"
```bash
# Verify in database
sqlite3 data/paper_trades.db "SELECT trade_id, entry_price, exit_price, pnl FROM trades WHERE trade_id = 'XXX';"
```

---

## 🎯 Best Practices

### ✅ DO:
- Run system regularly (daily for day trading)
- Review stats weekly
- Analyze losing trades
- Keep database backed up
- Let trades run to SL/TP

### ❌ DON'T:
- Manually close trades early (defeats purpose)
- Change strategy mid-testing
- Cherry-pick data
- Ignore losing streaks
- Skip statistical analysis

---

## 📈 Example Performance Report

### After 1 Month (30 Trades)

```
============================================================
📊 MONTHLY PERFORMANCE REPORT
============================================================

Period: Oct 1-30, 2025
Symbol: SOLUSDT
Trades: 30

Results:
  Wins: 21 (70%)
  Losses: 9 (30%)
  
P&L:
  Total: +$287.50
  Average: +$9.58 per trade
  Best: +$25.80 (pullback_reversal)
  Worst: -$8.20 (aligned_running SL hit)

Entry Setups:
  pullback_reversal: 15 trades, 80% win rate
  aligned_running: 12 trades, 58% win rate
  wait_for_reversal: 3 trades (NEUTRAL, no execution)

Risk/Reward:
  Average R/R: 1:2.1
  Average Risk: 2.8%
  Average Reward: 5.9%

Rating: 🌟🌟🌟🌟 Excellent
Status: ✅ Ready to consider real trading (with caution)
```

---

## 🚀 Getting Started

### 1. Run System
```bash
./run.sh
```

### 2. Trade Gets Stored
```
💼 PAPER TRADE EXECUTION:
   Status: ✅ EXECUTED
   Trade ID: SOLUSDT_20251023_123456
   Stored in database: paper_trades.db
```

### 3. View Trades
```bash
cd src
python trade_manager.py list --status open
python trade_manager.py stats
```

### 4. Repeat Daily
Build up trade history for analysis

---

## 💡 Tips

### For Best Results:
1. **Consistency**: Run daily at same time
2. **Discipline**: Don't skip signals
3. **Analysis**: Review weekly
4. **Patience**: Need 30+ trades for stats
5. **Honesty**: Don't cherry-pick data

### Trade Management:
- Let SL/TP work (don't intervene)
- Track unrealized P&L mentally
- Note market conditions
- Learn from losses

---

## 🔮 Future: Automated Monitoring

Create `monitor_trades.py`:

```python
# Run every hour via cron
# Check open trades
# Auto-close if SL/TP hit
# Send notifications
```

Cron job:
```bash
0 * * * * cd /home/flow/langtest && python src/monitor_trades.py
```

---

## Summary

**Paper Trading Agent provides:**

✅ **Automatic execution** of all LONG/SHORT signals  
✅ **Database storage** in SQLite  
✅ **Performance tracking** (win rate, P&L)  
✅ **Trade history** for analysis  
✅ **CLI tools** for management  
✅ **Statistical validation** of strategy  

**Essential for:**
- Strategy validation
- Performance tracking
- Learning and improvement
- Pre-real-trading testing

---

**Každý signál je nyní automaticky tracked - build your trading history! 💼📊**

