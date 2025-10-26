# Complete Workflow - Two-Part System 🔄

## Přehled

Paper trading systém má **DVĚ části:**

1. **Trade Creation** (`./run.sh`) - vytvoří trades
2. **Trade Monitoring** (`./monitor.sh`) - zavírá trades

**OBĚ části jsou potřeba pro kompletní tracking!**

---

## 🔄 Two-Part System

### Part 1: Analysis & Trade Creation

```
┌─────────────────────────────────────┐
│         USER COMMAND                │
│         ./run.sh                    │
└─────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│   LangGraph Multi-Agent System      │
│                                     │
│   1. Data Collector                 │
│   2. Analysis                       │
│   3. Decision (DeepSeek AI)         │
│   4. Paper Trading                  │
└─────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│         DATABASE WRITE              │
│                                     │
│   CREATE new trade:                 │
│   - trade_id: SOLUSDT_xxx           │
│   - status: OPEN                    │
│   - entry: $190.38                  │
│   - stop_loss: $185.20              │
│   - take_profit: $200.74            │
└─────────────────────────────────────┘
```

**Co dělá:**
- ✅ Analýza trhu
- ✅ AI rozhodnutí
- ✅ Risk management calculation
- ✅ Uložení trade jako **OPEN**

**Co NEDĚLÁ:**
- ❌ Nekontroluje cenu později
- ❌ Nezavírá trades

---

### Part 2: Trade Monitoring & Closure

```
┌─────────────────────────────────────┐
│         USER COMMAND                │
│    ./monitor.sh --continuous        │
└─────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│      MONITORING LOOP (60s)          │
│                                     │
│   1. Load OPEN trades from DB       │
│   2. For each trade:                │
│      - Fetch current price          │
│      - Compare with SL/TP           │
│      - If hit → Close trade         │
│   3. Sleep 60s                      │
│   4. Repeat                         │
└─────────────────────────────────────┘
                 │
          (When SL/TP hit)
                 ↓
┌─────────────────────────────────────┐
│         DATABASE UPDATE             │
│                                     │
│   UPDATE trade:                     │
│   - status: CLOSED                  │
│   - exit_price: $200.74             │
│   - exit_reason: TP_HIT             │
│   - pnl: +$10.36                    │
│   - pnl_percentage: +5.44%          │
└─────────────────────────────────────┘
```

**Co dělá:**
- ✅ Kontroluje open trades
- ✅ Stahuje aktuální ceny
- ✅ Detekuje SL/TP hits
- ✅ Zavírá trades
- ✅ Počítá P&L

**Co NEDĚLÁ:**
- ❌ Nevytváří nové trades
- ❌ Nedělá analýzu

---

## 📊 Complete Trading Cycle

### Timeline Example:

**Monday 10:00** - Vytvoření Trade
```bash
./run.sh

Output:
🎯 RECOMMENDATION: LONG
💰 Entry: $190.38 | SL: $185.20 | TP: $200.74

💼 PAPER TRADE EXECUTION:
   Status: ✅ EXECUTED
   Trade ID: SOLUSDT_20251023_100000

→ Trade stored in DB as OPEN
```

**Monday 10:05** - Start Monitor
```bash
./monitor.sh --continuous &

Output:
🔄 Starting continuous monitoring
Press Ctrl+C to stop

[2025-10-23 10:05:00] Checking trades...

Trade: SOLUSDT_20251023_100000
  LONG @ $190.38
  Current: $191.20
  SL: $185.20 | TP: $200.74
  ⏳ Still OPEN | Unrealized P&L: +$0.82

Next check in 60s...
```

**Monday 10:06 - Wednesday 14:30** - Monitoring...
```
Monitor běží v pozadí:
- Every minute checks price
- Trade still OPEN
- Unrealized P&L: -$2.30 → +$1.50 → +$5.20 → ...
```

**Wednesday 14:37** - TP Hit!
```
[2025-10-25 14:37:00] Checking trades...

Trade: SOLUSDT_20251023_100000
  LONG @ $190.38
  Current: $200.74
  SL: $185.20 | TP: $200.74
  🎯 TAKE PROFIT HIT!
  ✅ Trade CLOSED
  Exit: $200.74
  P&L: +$10.36 (+5.44%)

✅ Closed 1 trade(s)

📊 Updated Statistics:
   Win rate: 73.3%
   Total P&L: $215.80

→ Trade automatically CLOSED in DB ✅
```

**Wednesday 15:00** - Check Results
```bash
cd src
python trade_manager.py stats

Output:
Total Trades: 15
Closed: 15
Wins: 11
Losses: 4
Win Rate: 73.33%
Total P&L: $215.80 ✅
```

---

## ⚙️ How Each Part Works

### Trade Creation (run.sh)

**When to run:**
- Když chceš novou analýzu
- Daily (každé ráno pro day trading)
- When significant market change

**What happens:**
1. Analyzuje trh
2. AI rozhodne
3. **Vytvoří trade s status OPEN**
4. Nezavírá nic

**Frequency:** On-demand nebo 1x denně

---

### Trade Monitoring (monitor.sh)

**When to run:**
- **Neustále!** (continuous mode)
- Nebo cron job každou hodinu

**What happens:**
1. Načte OPEN trades
2. Stáhne current prices
3. Porovná s SL/TP
4. **Zavře trade pokud hit**
5. Repeat

**Frequency:** Continuous (60s) nebo cron (hourly)

**KRITICKÉ: Musí běžet nebo trades nikdy nezavřeš!**

---

## 🎯 Doporučené Setup

### Day Trading (1h/15m timeframes)

**Terminal 1: Analysis**
```bash
# Run when you want new trades
./run.sh
```

**Terminal 2: Monitor (Always Running)**
```bash
# Start a forget
nohup ./monitor.sh --continuous > monitor.log 2>&1 &

# Check status
tail -f monitor.log

# Stop když končíš
pkill -f monitor_trades
```

**Terminal 3: Stats & Management**
```bash
# Check anytime
cd src
python trade_manager.py stats
python trade_manager.py list --status open
```

---

### Swing Trading (4h/1h timeframes)

**Cron Job (Automatic)**
```bash
# Setup once:
crontab -e

# Add:
# Run analysis každý den v 9:00
0 9 * * * cd /home/flow/langtest && ./run.sh >> analysis.log 2>&1

# Monitor every hour
0 * * * * cd /home/flow/langtest && ./monitor.sh >> monitor.log 2>&1

# Check stats každý večer v 18:00
0 18 * * * cd /home/flow/langtest/src && python trade_manager.py stats >> stats.log 2>&1
```

**Fully automated! ✅**

---

## 🔍 Monitoring Modes

### Mode 1: Single Check
```bash
./monitor.sh

# Runs once
# Shows current status
# Closes trades if SL/TP hit
# Exits
```

**Use for:** Manual checks, testing

---

### Mode 2: Continuous
```bash
./monitor.sh --continuous

# Runs forever
# Checks every 60s
# Auto-closes trades
# Shows live updates
```

**Use for:** Active day trading, real-time tracking

---

### Mode 3: Cron Job
```bash
# In crontab:
0 * * * * cd /path/to/langtest && ./monitor.sh

# Runs every hour
# Automatic
# Logs to file
```

**Use for:** Swing trading, hands-off

---

## 📊 What Gets Stored in DB

### When Trade Created (run.sh):
```sql
INSERT INTO trades (
    trade_id = 'SOLUSDT_20251023_123456',
    status = 'OPEN',           ← Created as OPEN
    entry_price = 190.38,
    stop_loss = 185.20,
    take_profit = 200.74,
    entry_time = '2025-10-23T12:34:56',
    exit_time = NULL,          ← Not yet closed
    exit_price = NULL,
    pnl = NULL
)
```

### When Monitor Closes (monitor.sh):
```sql
UPDATE trades SET
    status = 'CLOSED',         ← Changed to CLOSED
    exit_time = '2025-10-25T14:37:00',
    exit_price = 200.74,       ← Actual exit
    exit_reason = 'TP_HIT',    ← Why closed
    pnl = 10.36,               ← Calculated P&L
    pnl_percentage = 5.44      ← Percentage return
WHERE trade_id = 'SOLUSDT_20251023_123456'
```

---

## ⚠️ Common Issues

### Issue 1: Trades Never Close
```
Problem: Monitor není spuštěn
Solution: ./monitor.sh --continuous

Check:
python src/trade_manager.py list --status open
→ Pokud vidíš staré trades (týdny), monitor neběží!
```

### Issue 2: Monitor Stopped
```
Problem: Monitor process died
Solution: Restart

# Check if running
ps aux | grep monitor_trades

# If not running
./monitor.sh --continuous &
```

### Issue 3: Can't See Closed Trades
```
Problem: Monitor možná neběžel
Solution: 
1. Check monitor.log
2. Manual close pokud chceš:
   python src/trade_manager.py close --trade-id XXX --price 195.50
```

---

## 🎯 Quick Commands Reference

```bash
# CREATE TRADES
./run.sh                          # Run analysis, create trade

# MONITOR TRADES
./monitor.sh                      # Single check
./monitor.sh --continuous         # Keep monitoring
nohup ./monitor.sh -c > m.log &   # Background

# VIEW TRADES
cd src
python trade_manager.py list      # All trades
python trade_manager.py list --status open   # Open only
python trade_manager.py stats     # Statistics

# STOP MONITOR
pkill -f monitor_trades           # Kill monitor process
```

---

## 📈 Example Session

```bash
# Morning: Create trades
./run.sh
→ LONG @ $190 created (OPEN)

# Start monitor in background
nohup ./monitor.sh --continuous > monitor.log 2>&1 &
→ Monitoring started

# Afternoon: Check status
cd src
python trade_manager.py list --status open
→ Trade still OPEN, current: $195

# Evening: Check if closed
python trade_manager.py stats
→ Win rate: 70%, P&L: $145
→ If higher, trade closed! ✅

# Check log
tail monitor.log
→ See "TP_HIT" message

# Next day: Run again
./run.sh
→ New trade created
→ Monitor already running, will handle it
```

---

## 💡 Pro Tips

### Tip 1: Always Keep Monitor Running
```bash
# Add to startup script
echo "cd /home/flow/langtest && nohup ./monitor.sh --continuous > monitor.log 2>&1 &" >> ~/.bashrc
```

### Tip 2: Check Monitor Health
```bash
# Create health check
ps aux | grep monitor_trades || ./monitor.sh --continuous &
```

### Tip 3: Log Rotation
```bash
# Prevent huge logs
# In cron (daily at midnight):
0 0 * * * mv /home/flow/langtest/monitor.log /home/flow/langtest/monitor_$(date +\%Y\%m\%d).log
```

### Tip 4: Mobile Monitoring
```bash
# SSH to your server
ssh user@your-server
cd langtest
tail -f monitor.log

# See live updates on phone!
```

---

## 🎓 Understanding the Flow

### Why Two Parts?

**Separace concerns:**
- ✅ Trade creation = Complex (AI, indicators, analysis)
- ✅ Trade monitoring = Simple (price check, close)
- ✅ Can run independently
- ✅ Scalable (one monitor, many analysis runs)

**Alternative (Single System):**
- ❌ Analysis by měla kontrolovat všechny open trades
- ❌ Pomalé (každá analýza by checkovala všechny trades)
- ❌ Nepraktické

---

## 📊 Database Lifecycle

```
STATUS: OPEN
├── Created by: Paper Trading Agent (run.sh)
├── Fields set: entry, SL, TP, setup, reasoning
├── Fields null: exit_time, exit_price, pnl
└── Waiting for: Monitor to close

       ↓ (price reaches SL/TP)

STATUS: CLOSED
├── Closed by: Monitor (monitor.sh)
├── Fields set: exit_time, exit_price, exit_reason, pnl
├── Stats updated: Win rate, total P&L
└── Permanent record
```

---

## ✅ Checklist

### Daily Routine:

**Morning:**
- [ ] Check if monitor běží: `ps aux | grep monitor`
- [ ] If not: `./monitor.sh --continuous &`
- [ ] Run analysis: `./run.sh`
- [ ] Note open trades: `python src/trade_manager.py list --status open`

**Evening:**
- [ ] Check stats: `python src/trade_manager.py stats`
- [ ] Check monitor log: `tail monitor.log`
- [ ] Review closed trades

**Weekly:**
- [ ] Backup database: `cp data/paper_trades.db data/backup_$(date +%Y%m%d).db`
- [ ] Analyze performance
- [ ] Adjust strategy if needed

---

## 🚀 Quick Start

### First Time Setup:
```bash
# 1. Run first analysis
./run.sh
→ Creates first trade (OPEN)

# 2. Start monitor
./monitor.sh --continuous &
→ Will close trade when SL/TP hits

# 3. Check after few hours/days
cd src
python trade_manager.py stats
→ See results!
```

### Ongoing Use:
```bash
# Monitor always running in background
# Run analysis when you want new trades
./run.sh

# Monitor automatically handles new trades
```

---

## 📚 Related Documentation

- **TRADE_MONITORING.md** - Detailed monitoring guide
- **PAPER_TRADING.md** - Paper trading overview
- **README.md** - Main documentation

---

## 🎯 Summary

### Odpověď na tvou otázku:

**"Jak se zjistí že trades jsou zavřeny? Kdo to vloží do DB?"**

**Odpověď:**

1. **Trades se vytváří jako OPEN** pomocí `./run.sh`
   - Paper Trading Agent ukládá do DB
   - Status: OPEN

2. **Trades se zavírají pomocí `./monitor.sh`**
   - Monitor Script kontroluje ceny
   - Když SL/TP hit → zavře v DB
   - Status: OPEN → CLOSED
   - Počítá P&L

3. **Musíš mít OBĚ části running:**
   - `./run.sh` - vytváří trades (on-demand)
   - `./monitor.sh --continuous` - zavírá trades (always running)

**Bez monitoru = trades nikdy nezavřeš = no statistics!**

---

## 🔧 System Architecture

```
┌──────────────┐         ┌──────────────┐
│   run.sh     │         │  monitor.sh  │
│  (Part 1)    │         │   (Part 2)   │
│              │         │              │
│  Creates     │         │  Closes      │
│  OPEN trades │         │  trades      │
└──────┬───────┘         └──────┬───────┘
       │                        │
       ↓                        ↓
   ┌────────────────────────────────┐
   │    SQLite Database             │
   │    data/paper_trades.db        │
   │                                │
   │  - OPEN trades (created)       │
   │  - CLOSED trades (monitored)   │
   └────────────────────────────────┘
              │
              ↓
      ┌───────────────┐
      │   Stats &     │
      │  Performance  │
      └───────────────┘
```

---

**Nyní rozumíš kompletnímu systému! 🎓**

**Start both parts a build your track record! 🚀**

