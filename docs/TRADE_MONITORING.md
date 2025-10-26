# Trade Monitoring - How It Works 🔍

## 📋 Problém

**Paper trades se ukládají jako OPEN, ale kdo je zavírá?**

```
System runs → LONG @ $190
  ↓
Stored in DB: status = OPEN
  ↓
??? Jak zjistit že cena dosáhla SL/TP ???
```

---

## ✅ Řešení: Automated Trade Monitor

### Workflow

```
1. System vytvoří trade
   ↓
   Status: OPEN
   Entry: $190.38
   SL: $185.20
   TP: $200.74
   
2. Monitor script (pravidelně běží)
   ↓
   Načte všechny OPEN trades
   Pro každý trade:
     - Stáhne aktuální cenu z Binance
     - Porovná s SL a TP
     - Pokud hit → zavře trade v DB
   
3. Trade uzavřen
   ↓
   Status: CLOSED
   Exit price: $200.74
   Exit reason: TP_HIT
   P&L: +$10.36 (+5.44%)
```

---

## 🛠️ Monitor Script

### `monitor_trades.py`

**Funkce:**
- Načte všechny OPEN trades z databáze
- Pro každý trade stáhne current price
- Zkontroluje LONG positions:
  - `current_price <= stop_loss` → Close jako SL_HIT
  - `current_price >= take_profit` → Close jako TP_HIT
- Zkontroluje SHORT positions:
  - `current_price >= stop_loss` → Close jako SL_HIT
  - `current_price <= take_profit` → Close jako TP_HIT
- Vypočítá P&L a uloží do DB

---

## 🚀 Použití

### Varianta 1: Manuální Check (Single Run)

```bash
# Zkontroluj open trades TEĎ
./monitor.sh

# Output:
🔍 MONITORING 3 OPEN TRADES
============================================================

Trade: SOLUSDT_20251023_123456
  LONG @ $190.38
  Current: $195.50
  SL: $185.20 | TP: $200.74
  ⏳ Still OPEN | Unrealized P&L: +$5.12 (+2.69%)

Trade: SOLUSDT_20251023_120000
  LONG @ $188.00
  Current: $195.50
  SL: $182.50 | TP: $199.50
  🎯 TAKE PROFIT HIT!
  ✅ Trade CLOSED
  Exit: $199.50
  P&L: +$11.50 (+6.12%)

============================================================
✅ Closed 1 trade(s)

📊 Updated Statistics:
   Total: 15
   Open: 2 | Closed: 13
   Win rate: 69.2%
   Total P&L: $127.80
============================================================
```

### Varianta 2: Continuous Monitoring (Recommended)

```bash
# Běží neustále, kontroluje každou minutu
./monitor.sh --continuous

# Output:
🔄 Starting continuous monitoring (checking every 60s)
Press Ctrl+C to stop

[2025-10-23 12:34:56] Checking trades...

🔍 MONITORING 3 OPEN TRADES
...
Next check in 60s...

[2025-10-23 12:35:56] Checking trades...
...
```

**Nech běžet na pozadí:**
```bash
# Linux/Mac: Run v pozadí
nohup ./monitor.sh --continuous > monitor.log 2>&1 &

# Check log
tail -f monitor.log

# Stop
pkill -f monitor_trades.py
```

### Varianta 3: Cron Job (Scheduled)

```bash
# Kontroluj každou hodinu
crontab -e

# Přidej:
0 * * * * cd /home/flow/langtest && ./monitor.sh >> monitor.log 2>&1

# Nebo každých 15 minut:
*/15 * * * * cd /home/flow/langtest && ./monitor.sh >> monitor.log 2>&1
```

---

## 🔄 Complete Trading Cycle

### Den 1: Vytvoření Trade
```bash
# 1. Spusť analýzu
./run.sh

# Output:
🎯 RECOMMENDATION: LONG
💰 Entry: $190.38
   Stop: $185.20
   TP: $200.74

💼 PAPER TRADE EXECUTION:
   Status: ✅ EXECUTED
   Trade ID: SOLUSDT_20251023_123456

→ Trade uložen jako OPEN v databázi
```

### Den 1-5: Monitoring
```bash
# Option A: Manual check (kdykoli)
./monitor.sh

# Option B: Continuous (nech běžet)
./monitor.sh --continuous

# Option C: Cron (automaticky každou hodinu)
# (nastaveno v crontab)
```

### Den X: Uzavření
```
Monitor detekuje:
  Current price: $200.74
  >= Take profit!
  
→ Automaticky uzavře trade:
  Status: CLOSED
  Exit: $200.74
  Reason: TP_HIT
  P&L: +$10.36
  
→ Aktualizuje statistiky:
  Win rate, total P&L
```

---

## 📊 Monitoring Options Comparison

### 1. Manual (./monitor.sh)
```
Použití: Když máš čas
Frequency: Několikrát denně
Pros: Žádné resources, full control
Cons: Musíš pamatovat spouštět

Good for: Swing trading (4h/1h TF)
```

### 2. Continuous (./monitor.sh --continuous)
```
Použití: Nech běžet na pozadí
Frequency: Každou minutu
Pros: Automatic, fast closure
Cons: Zabírá terminál/resources

Good for: Day trading (1h/15m TF)
```

### 3. Cron Job
```
Použití: Set & forget
Frequency: Každou hodinu (configurable)
Pros: Automatic, no manual work
Cons: Less frequent checks

Good for: Swing trading, casual
```

---

## ⚙️ Configuration

### Monitoring Interval

**V `monitor_trades.py --continuous`:**
```bash
# Default: 60 seconds
./monitor.sh --continuous

# Custom interval:
cd src
python monitor_trades.py --continuous --interval 120  # 2 minutes
python monitor_trades.py --continuous --interval 30   # 30 seconds
```

**V Cron:**
```bash
# Každou hodinu
0 * * * * ...

# Každých 30 minut
*/30 * * * * ...

# Každých 5 minut (aggressive)
*/5 * * * * ...
```

---

## 🎯 Recommended Setup

### For Day Trading (1h/15m)
```bash
# Run analysis každé ráno
./run.sh

# Start monitor v pozadí
nohup ./monitor.sh --continuous > monitor.log 2>&1 &

# Check večer
tail monitor.log
python src/trade_manager.py stats
```

### For Swing Trading (4h/1h)
```bash
# Cron job - check each hour
0 * * * * cd /path/to/langtest && ./monitor.sh >> monitor.log 2>&1

# Manual check denně
./monitor.sh
python src/trade_manager.py stats
```

---

## 📝 Monitoring Output Examples

### No Hits (All Still Open)
```
🔍 MONITORING 3 OPEN TRADES
============================================================

Trade: SOLUSDT_20251023_123456
  LONG @ $190.38
  Current: $192.50
  SL: $185.20 | TP: $200.74
  ⏳ Still OPEN | Unrealized P&L: +$2.12 (+1.11%)

Trade: SOLUSDT_20251023_120000
  LONG @ $188.00
  Current: $192.50
  SL: $182.50 | TP: $199.50
  ⏳ Still OPEN | Unrealized P&L: +$4.50 (+2.39%)

Trade: SOLUSDT_20251023_110000
  SHORT @ $195.00
  Current: $192.50
  SL: $201.00 | TP: $183.00
  ⏳ Still OPEN | Unrealized P&L: +$2.50 (+1.28%)

============================================================
ℹ️  All trades still open
============================================================
```

### TP Hit (Winner!)
```
Trade: SOLUSDT_20251023_120000
  LONG @ $188.00
  Current: $199.50
  SL: $182.50 | TP: $199.50
  🎯 TAKE PROFIT HIT!
  ✅ Trade CLOSED
  Exit: $199.50
  P&L: +$11.50 (+6.12%)

============================================================
✅ Closed 1 trade(s)

📊 Updated Statistics:
   Total: 15
   Open: 2 | Closed: 13
   Win rate: 76.9%
   Total P&L: $156.30
============================================================
```

### SL Hit (Loss)
```
Trade: SOLUSDT_20251023_110000
  LONG @ $190.00
  Current: $185.20
  SL: $185.20 | TP: $200.00
  🛑 STOP LOSS HIT!
  ✅ Trade CLOSED
  Exit: $185.20
  P&L: -$4.80 (-2.53%)

============================================================
✅ Closed 1 trade(s)

📊 Updated Statistics:
   Total: 15
   Open: 3 | Closed: 12
   Win rate: 66.7%
   Total P&L: $98.50
============================================================
```

---

## 🔧 Advanced Usage

### Quiet Mode (Only Show Closures)
```bash
cd src
python monitor_trades.py --quiet

# Output only if trade closed:
✅ Closed 1 trade(s)
Win rate: 70%
Total P&L: $145.20
```

### Background Monitoring with Notifications
```bash
# monitor_with_notify.sh
#!/bin/bash
while true; do
    result=$(cd src && python monitor_trades.py --quiet)
    if [[ $result == *"Closed"* ]]; then
        # Send notification (email, telegram, etc.)
        echo "Trade closed!" | mail -s "Trading Alert" your@email.com
    fi
    sleep 60
done
```

---

## 🎓 Best Practices

### ✅ DO:
- Run monitor regularly (continuous nebo cron)
- Let trades hit SL/TP naturally
- Check monitor.log for issues
- Backup database before manual changes
- Review stats after closures

### ❌ DON'T:
- Manually close trades unless necessary
- Skip monitoring (defeats tracking purpose)
- Change SL/TP in database directly
- Stop monitor during active trades
- Ignore SL hits (they're learning opportunities)

---

## 🔍 Troubleshooting

### Monitor není zavírá trades
```bash
# Check že monitor běží
ps aux | grep monitor_trades

# Check log
tail -f monitor.log

# Manual test
cd src
python monitor_trades.py

# Check prices manually
python -c "from utils.binance_client import BinanceClient; c = BinanceClient(); print(c.get_current_price('SOLUSDT'))"
```

### Database locked
```bash
# Stop all monitors
pkill -f monitor_trades

# Try again
./monitor.sh
```

### Trades not showing
```bash
# Check database
cd src
python trade_manager.py list --status open

# If empty, no open trades (good!)
```

---

## 📊 Complete Workflow Diagram

```
DAY 1 - Morning:
  User: ./run.sh
    ↓
  System: Analysis + AI Decision
    ↓
  Paper Trading Agent: Create OPEN trade
    ↓
  Database: SOLUSDT_20251023_123456 (OPEN)

DAY 1 - Setup Monitor:
  User: ./monitor.sh --continuous &
    ↓
  Monitor: Checks every 60s
    ↓
  Loop: Check price vs SL/TP

DAY 1-5 - Monitoring:
  Every minute:
    Monitor checks price
    If SL/TP hit → Close trade
    Else → Wait
    
DAY 3 - TP Hit:
  Price reaches $200.74
    ↓
  Monitor detects: price >= TP
    ↓
  Database: Close trade
    - exit_price: $200.74
    - exit_reason: TP_HIT
    - pnl: +$10.36
    - status: CLOSED
    ↓
  Stats updated: Win rate +, P&L +

DAY 7 - Review:
  User: python src/trade_manager.py stats
    ↓
  See results:
    - 10 trades closed
    - 70% win rate
    - +$127.50 P&L
```

---

## 🎯 Two-Part System

### Part 1: Trade Creation (main.py)
```
./run.sh
  ↓
Creates OPEN trades
  ↓
Stores in database
```

### Part 2: Trade Closing (monitor_trades.py)
```
./monitor.sh --continuous
  ↓
Checks OPEN trades
  ↓
Closes when SL/TP hit
  ↓
Updates database
```

**Oba jsou potřeba pro kompletní cycle!**

---

## 📚 Quick Commands

### Start Everything
```bash
# Terminal 1: Run analysis (when you want)
./run.sh

# Terminal 2: Start monitor (keep running)
./monitor.sh --continuous
```

### Check Status Anytime
```bash
# Terminal 3: Check stats
cd src
python trade_manager.py stats
python trade_manager.py list --status open
```

### Stop Monitor
```bash
# Ctrl+C v monitor terminal
# Or
pkill -f monitor_trades
```

---

## 🔔 Future: Notifications

### Email on TP/SL Hit
```python
# In monitor_trades.py (future enhancement)
if should_close:
    db.close_trade(...)
    
    # Send email
    send_email(
        subject=f"{exit_reason}: {trade_id}",
        body=f"Trade closed at ${exit_price}, P&L: {pnl}"
    )
```

### Telegram Bot
```python
# Send telegram message
telegram_bot.send_message(
    f"🎯 TP Hit!\n"
    f"Trade: {trade_id}\n"
    f"P&L: +${pnl:.2f}"
)
```

---

## 💡 Pro Tips

### 1. Always Run Monitor
```bash
# Add to startup
echo "./monitor.sh --continuous &" >> ~/.bashrc

# Or systemd service (Linux)
# Or Task Scheduler (Windows)
```

### 2. Log Everything
```bash
./monitor.sh --continuous > monitor.log 2>&1 &

# Review later
grep "CLOSED" monitor.log
grep "P&L" monitor.log
```

### 3. Multiple Terminals
```
Terminal 1: Analysis (./run.sh když chceš)
Terminal 2: Monitor (./monitor.sh --continuous)
Terminal 3: Stats & management
```

### 4. Backup Before Manual Close
```bash
# If you need to manually close
cp data/paper_trades.db data/backup.db

# Then
cd src
python trade_manager.py close --trade-id XXX --price 195.50
```

---

## ⚠️ Important Notes

### Monitor MUSÍ běžet!
```
❌ Bez monitoru:
  - Trades zůstanou OPEN navždy
  - Nikdy se nezavřou
  - Žádné P&L statistiky

✅ S monitorem:
  - Auto-close při SL/TP
  - Accurate P&L tracking
  - Real performance stats
```

### Frequency Matters
```
1h TF trading:
  → Monitor každou hodinu stačí (cron)

15m TF trading:
  → Monitor continuous (každou minutu)
  
1m TF scalping:
  → Monitor každých 30s
```

### API Rate Limits
```
Binance limit: 1200 requests/minute
Monitor: 1 request per trade per check

Example:
  5 open trades × 1 check/min = 5 requests/min
  → Well within limits ✅
```

---

## 📊 Statistics Example

### After 1 Week:
```bash
python src/trade_manager.py stats

Total Trades: 25
  Open: 3
  Closed: 22

Performance:
  Wins: 16
  Losses: 6
  Win Rate: 72.73%
  Total P&L: $287.50
  Avg P&L: 2.85%
  Rating: 🌟 Excellent
```

**This is only possible with monitoring!**

---

## 🚀 Setup Instructions

### Quick Setup (5 minutes)

```bash
# 1. Already have system running trades
./run.sh  # Creates trades

# 2. Start monitor
./monitor.sh --continuous &

# 3. Done! Monitor runs in background

# 4. Check anytime
python src/trade_manager.py stats
```

### Production Setup (Cron)

```bash
# 1. Create cron job
crontab -e

# 2. Add (check every hour)
0 * * * * cd /home/flow/langtest && source venv/bin/activate && ./monitor.sh >> monitor.log 2>&1

# 3. Save and exit

# 4. Verify
crontab -l

# 5. Check log later
tail -f /home/flow/langtest/monitor.log
```

---

## ✅ Verification

### Test Monitor Works:

```bash
# 1. Create a test trade (run analysis)
./run.sh

# 2. Check it's OPEN
cd src
python trade_manager.py list --status open

# 3. Run monitor
cd ..
./monitor.sh

# 4. Should see trade being monitored
# 5. Wait for SL/TP to hit (or test manually)
```

---

## 📝 Summary

**Trade Monitoring System:**

✅ **monitor_trades.py** - Core monitoring logic  
✅ **monitor.sh / monitor.bat** - Helper scripts  
✅ **Automatic closure** - When SL/TP hit  
✅ **P&L calculation** - Accurate tracking  
✅ **Statistics update** - Real-time  
✅ **Multiple modes** - Single/Continuous/Cron  

**Essential for:**
- Complete trading cycle
- Accurate performance tracking
- Automated trade management
- Hands-off operation

---

## 🎯 Key Takeaway

```
Trade Creation (run.sh)
     +
Trade Monitoring (monitor.sh)
     =
Complete Paper Trading System! 💼
```

**Without monitor = Incomplete system**  
**With monitor = Professional trading tracker** ✅

---

**Start monitoring your trades today! 🔍📊**

