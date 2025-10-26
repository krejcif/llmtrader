# Bot Logging System 📋

## Přehled

Autonomous Trading Bot má **profesionální logging systém** se třemi úrovněmi logů:

1. **Main Log** - Důležité události
2. **Detailed Log** - Kompletní debug info
3. **Error Log** - Pouze chyby

---

## 📁 Log Files

### 1. `logs/trading_bot.log` - Main Log

**Obsah:**
- ✅ Bot start/stop
- ✅ Analysis runs (#1, #2, #3...)
- ✅ AI decisions (LONG/SHORT/NEUTRAL)
- ✅ Trade creation
- ✅ Trade closures (TP/SL hits)
- ✅ P&L updates
- ✅ Statistics updates
- ✅ Hourly heartbeats

**Rotation:** 10MB max, keeps 10 files  
**Level:** INFO  
**Use:** Daily review, performance tracking  

**Example:**
```
2025-10-23 14:30:00 |     INFO |        run_analysis | ANALYSIS #15 STARTED - 2025-10-23 14:30:00
2025-10-23 14:30:00 |     INFO |        run_analysis | Symbol: SOLUSDT, TF: 1h/15m
2025-10-23 14:30:05 |     INFO |        run_analysis | Analysis complete: LONG (confidence: high)
2025-10-23 14:30:05 |     INFO |        run_analysis | LONG signal: Entry $190.38, SL $185.20, TP $200.74, R/R 1:2.0
2025-10-23 14:30:06 |     INFO |        run_analysis | Paper trade created: SOLUSDT_20251023_143000
2025-10-23 14:30:06 |     INFO |        run_analysis |   Entry setup: pullback_reversal
2025-10-23 14:30:06 |     INFO |        run_analysis |   Reversal: bullish_reversal (strength: strong)
2025-10-23 14:30:06 |     INFO |        run_analysis | Analysis #15 finished. Next in 900s
2025-10-23 15:30:00 |     INFO |                  run | Heartbeat: Cycle 720, Analyses: 16, Trades created: 8, Trades closed: 5
2025-10-25 18:45:23 |     INFO |       monitor_trades | TRADE CLOSED: SOLUSDT_20251023_143000
2025-10-25 18:45:23 |     INFO |       monitor_trades |   Action: LONG @ $190.38
2025-10-25 18:45:23 |     INFO |       monitor_trades |   Exit: $200.74 (TP_HIT)
2025-10-25 18:45:23 |     INFO |       monitor_trades |   P&L: +$10.36 (+5.44%)
2025-10-25 18:45:23 |     INFO |       monitor_trades |   Setup: pullback_reversal
2025-10-25 18:45:23 |     INFO |       monitor_trades |   Updated stats: Win rate 75.0%, Total P&L $234.50
```

---

### 2. `logs/bot_detailed.log` - Detailed Debug Log

**Obsah:**
- ✅ Všechno z main log
- ✅ DEBUG level messages
- ✅ Agent internal operations
- ✅ API calls details
- ✅ Data processing steps
- ✅ Indicator calculations

**Rotation:** 50MB max, keeps 5 files  
**Level:** DEBUG  
**Use:** Deep debugging, understanding bot behavior  

---

### 3. `logs/bot_errors.log` - Error Log

**Obsah:**
- ❌ ERROR level only
- ❌ Stack traces
- ❌ API failures
- ❌ Database errors
- ❌ Network issues

**Rotation:** 5MB max, keeps 5 files  
**Level:** ERROR  
**Use:** Troubleshooting, finding issues  

**Example:**
```
2025-10-23 16:45:00 |    ERROR |        run_analysis | Error during analysis: HTTPSConnectionPool
Traceback (most recent call last):
  File "src/trading_bot.py", line 165, in run_analysis
  ...
requests.exceptions.ConnectionError: HTTPSConnectionPool...
```

---

## 🔍 Viewing Logs

### Interactive Viewer

```bash
./view_logs.sh

# Menu appears:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 BOT LOG VIEWER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1) Live main log (tail -f)
2) Live errors only
3) Show recent analyses
4) Show trade closures
5) Show winning trades
6) Show losing trades
7) Show TP hits
8) Show SL hits
9) Count statistics
0) Exit

Select option: _
```

### Quick Commands

```bash
# Live follow main log
./view_logs.sh live

# Show errors
./view_logs.sh errors

# Recent analyses
./view_logs.sh analyses

# All closures
./view_logs.sh closures

# Winners only
./view_logs.sh wins

# Losers only
./view_logs.sh losses

# Statistics
./view_logs.sh stats
```

---

## 📊 Log Analysis

### Find Specific Events

```bash
cd logs

# All LONG signals
grep "LONG signal" trading_bot.log

# All SHORT signals
grep "SHORT signal" trading_bot.log

# All reversals detected
grep "Reversal:" trading_bot.log

# Pullback entries
grep "pullback_reversal" trading_bot.log

# TP hits only
grep "TP_HIT" trading_bot.log

# SL hits only
grep "SL_HIT" trading_bot.log

# High confidence trades
grep "confidence: high" trading_bot.log
```

### Calculate Win Rate from Logs

```bash
cd logs

# Total trades closed
CLOSED=$(grep -c "TRADE CLOSED:" trading_bot.log)

# Winning trades
WINS=$(grep "TRADE CLOSED" trading_bot.log | grep -c "P&L: +")

# Losing trades
LOSSES=$(grep "TRADE CLOSED" trading_bot.log | grep -c "P&L: -")

# Calculate
WIN_RATE=$(echo "scale=2; $WINS / $CLOSED * 100" | bc)

echo "Closed: $CLOSED"
echo "Wins: $WINS"
echo "Losses: $LOSSES"
echo "Win Rate: $WIN_RATE%"
```

### Find Best/Worst Trades

```bash
# Best trades (sorted by P&L)
grep "P&L: +" trading_bot.log | sort -t'$' -k2 -n | tail -5

# Worst trades
grep "P&L: -" trading_bot.log | sort -t'$' -k2 -n | head -5

# Largest TP hits
grep "TP_HIT" trading_bot.log | grep "P&L: +" | sort -t'$' -k2 -n | tail -10
```

---

## 🎯 What Gets Logged

### Bot Lifecycle

**Start:**
```
2025-10-23 10:00:00 | INFO | Logging system initialized
2025-10-23 10:00:00 | INFO | Main log: logs/trading_bot.log
2025-10-23 10:00:01 | INFO | BOT STARTING
2025-10-23 10:00:01 | INFO | Symbol: SOLUSDT
2025-10-23 10:00:01 | INFO | Timeframes: 1h / 15m
```

**Every Analysis:**
```
2025-10-23 14:30:00 | INFO | ANALYSIS #15 STARTED
2025-10-23 14:30:05 | INFO | Analysis complete: LONG (confidence: high)
2025-10-23 14:30:06 | INFO | Paper trade created: SOLUSDT_xxx
2025-10-23 14:30:06 | INFO |   Entry setup: pullback_reversal
```

**Every Trade Closure:**
```
2025-10-25 18:45:23 | INFO | TRADE CLOSED: SOLUSDT_xxx
2025-10-25 18:45:23 | INFO |   Action: LONG @ $190.38
2025-10-25 18:45:23 | INFO |   Exit: $200.74 (TP_HIT)
2025-10-25 18:45:23 | INFO |   P&L: +$10.36 (+5.44%)
2025-10-25 18:45:23 | INFO |   Updated stats: Win rate 75.0%, Total P&L $234.50
```

**Hourly Heartbeat:**
```
2025-10-23 15:00:00 | INFO | Heartbeat: Cycle 720, Analyses: 16, Trades created: 8, Trades closed: 5
```

**Shutdown:**
```
2025-10-23 18:00:00 | WARNING | Shutdown signal received
2025-10-23 18:00:01 | INFO | BOT SHUTDOWN INITIATED
2025-10-23 18:00:01 | INFO | Total analyses run: 32
2025-10-23 18:00:01 | INFO | Total trades created: 12
2025-10-23 18:00:01 | INFO | Final stats: Win rate 70.0%, P&L $156.80
```

---

## 🔧 Log Management

### Rotation

Logs **automaticky rotují**:
```
trading_bot.log         (current, up to 10MB)
trading_bot.log.1       (previous, up to 10MB)
trading_bot.log.2       (older)
...
trading_bot.log.10      (oldest)
```

Když `trading_bot.log` dosáhne 10MB:
1. Rename: log.9 → log.10 (delete), log.8 → log.9, ..., log.1 → log.2
2. Rename: log → log.1
3. Create new empty log

**= Žádný manual cleanup!**

### Disk Usage

**Typical after 1 month:**
```
logs/
├── trading_bot.log     (8.5 MB)
├── trading_bot.log.1   (10 MB)
├── trading_bot.log.2   (10 MB)
├── bot_detailed.log    (45 MB)
├── bot_errors.log      (0.2 MB)
└── Total: ~84 MB
```

Max possible: ~200MB (all logs full + rotations)

### Manual Cleanup

```bash
# Backup before cleanup
cd logs
tar -czf backup_$(date +%Y%m%d).tar.gz *.log*

# Delete old rotated logs
rm -f *.log.[5-9] *.log.10

# Or start fresh (careful!)
rm -f *.log*
# Logs recreate on next bot start
```

---

## 📈 Log Analysis Examples

### Daily Review

```bash
# Morning: Check what happened overnight
cd logs
grep "TRADE CLOSED" trading_bot.log | tail -20

# How many analyses?
grep -c "ANALYSIS.*STARTED" trading_bot.log

# Any errors?
wc -l bot_errors.log
```

### Weekly Performance

```bash
# All trade closures this week
grep "TRADE CLOSED:" trading_bot.log | grep "2025-10-2[0-6]"

# Win rate calculation
WINS=$(grep "2025-10-2[0-26]" trading_bot.log | grep "TRADE CLOSED" | grep -c "P&L: +")
TOTAL=$(grep "2025-10-2[0-26]" trading_bot.log | grep -c "TRADE CLOSED:")
echo "$WINS / $TOTAL = $(echo "scale=1; $WINS*100/$TOTAL" | bc)%"
```

### Find Patterns

```bash
# Which entry setups worked best?
grep "Entry setup: pullback_reversal" trading_bot.log | wc -l
grep "Entry setup: aligned_running" trading_bot.log | wc -l

# Reversal trades performance
grep "Reversal: bullish_reversal" trading_bot.log | wc -l
grep "Reversal: bearish_reversal" trading_bot.log | wc -l

# Time of day analysis
grep "TRADE CLOSED" trading_bot.log | cut -d' ' -f2 | cut -d':' -f1 | sort | uniq -c
```

---

## 🚨 Error Monitoring

### Check for Issues

```bash
# Any errors today?
grep $(date +%Y-%m-%d) logs/bot_errors.log

# Common errors
grep -o "Error.*:" logs/bot_errors.log | sort | uniq -c | sort -rn

# Last 10 errors
tail -20 logs/bot_errors.log
```

### Alert on Errors

```bash
# Create alert script
cat > check_errors.sh << 'SCRIPT'
#!/bin/bash
ERROR_COUNT=$(wc -l < logs/bot_errors.log)
if [ $ERROR_COUNT -gt 10 ]; then
    echo "⚠️  Warning: $ERROR_COUNT errors in log!"
    # Send notification
fi
SCRIPT

# Run hourly in cron
0 * * * * cd /path/to/langtest && bash check_errors.sh
```

---

## 🎓 Understanding Logs

### Log Levels

```
DEBUG   - Detailed traces (bot_detailed.log only)
INFO    - Normal operations (all logs)
WARNING - Warnings (all logs)
ERROR   - Errors (all logs, highlighted in bot_errors.log)
```

### Log Format

```
TIMESTAMP           | LEVEL  | FUNCTION             | MESSAGE
2025-10-23 14:30:00 | INFO   | run_analysis         | ANALYSIS #15 STARTED
```

**Fields:**
- **Timestamp**: Exact time (YYYY-MM-DD HH:MM:SS)
- **Level**: INFO/WARNING/ERROR
- **Function**: Which function logged this
- **Message**: What happened

---

## 💡 Pro Tips

### Tip 1: Tail Multiple Logs

```bash
# Watch main log and errors simultaneously
tail -f logs/trading_bot.log logs/bot_errors.log
```

### Tip 2: Filter Noise

```bash
# Only show important events
grep -E "ANALYSIS.*STARTED|TRADE CLOSED|ERROR" logs/trading_bot.log
```

### Tip 3: Export for Analysis

```bash
# Export to CSV for Excel/analysis
grep "TRADE CLOSED:" logs/trading_bot.log | \
  sed 's/.*TRADE CLOSED: //' | \
  sed 's/|/,/g' > trades.csv
```

### Tip 4: Monitor in Real-Time

```bash
# Color-coded live view (if have ccze)
tail -f logs/trading_bot.log | ccze -A

# Or use grep with color
tail -f logs/trading_bot.log | grep --color=auto -E "LONG|SHORT|CLOSED|ERROR"
```

---

## 🔍 Troubleshooting with Logs

### Bot Not Creating Trades?

```bash
# Check analyses running
grep "ANALYSIS.*STARTED" logs/trading_bot.log | tail -5

# Check decisions
grep "Analysis complete:" logs/trading_bot.log | tail -10

# Are they all NEUTRAL?
grep "NEUTRAL:" logs/trading_bot.log | tail -10
```

### Trades Not Closing?

```bash
# Check monitoring
grep "Monitoring.*open" logs/bot_detailed.log | tail -10

# Check prices being fetched
grep "Current:" logs/bot_detailed.log | tail -10

# Any monitor errors?
grep "Error checking trade" logs/trading_bot.log
```

### Performance Issues?

```bash
# Count operations per hour
grep "$(date +%Y-%m-%d)" logs/trading_bot.log | cut -d' ' -f2 | cut -d':' -f1 | uniq -c

# API errors?
grep "BinanceAPIException" logs/bot_errors.log

# Slow analyses?
# (would need timestamp diff calculation)
```

---

## 📊 Log-Based Reporting

### Daily Report Script

```bash
#!/bin/bash
# daily_report.sh

TODAY=$(date +%Y-%m-%d)
LOG=logs/trading_bot.log

echo "📊 Daily Report - $TODAY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Analyses
ANALYSES=$(grep "$TODAY" $LOG | grep -c "ANALYSIS.*STARTED")
echo "Analyses run: $ANALYSES"

# Trades
CREATED=$(grep "$TODAY" $LOG | grep -c "Paper trade created")
CLOSED=$(grep "$TODAY" $LOG | grep -c "TRADE CLOSED:")
echo "Trades created: $CREATED"
echo "Trades closed: $CLOSED"

# Results
if [ $CLOSED -gt 0 ]; then
    WINS=$(grep "$TODAY" $LOG | grep "TRADE CLOSED" | grep -c "P&L: +")
    LOSSES=$(grep "$TODAY" $LOG | grep "TRADE CLOSED" | grep -c "P&L: -")
    WIN_RATE=$(echo "scale=1; $WINS*100/$CLOSED" | bc)
    echo "Wins: $WINS | Losses: $LOSSES"
    echo "Win rate: $WIN_RATE%"
fi

# Errors
ERRORS=$(grep -c "$TODAY" logs/bot_errors.log 2>/dev/null || echo 0)
echo "Errors: $ERRORS"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

Run automatically:
```bash
# Cron: Daily at 23:59
59 23 * * * cd /path/to/langtest && ./daily_report.sh | mail -s "Trading Bot Daily Report" your@email.com
```

---

## 🔔 Notifications from Logs

### Email on Trade Closure

```python
# Add to trading_bot.py (future)
import smtplib

def send_email_notification(subject, body):
    # Send email on important events
    ...

# In monitor_trades after closure:
if should_close:
    ...
    send_email_notification(
        f"Trade Closed: {exit_reason}",
        f"P&L: {pnl_sign}${pnl:.2f}"
    )
```

### Telegram Notifications

```python
# Using python-telegram-bot
def send_telegram(message):
    bot.send_message(chat_id, message)

# On TP hit
send_telegram(f"🎯 TP Hit! P&L: +${pnl:.2f}")
```

---

## 📁 Log Organization

### Directory Structure

```
logs/
├── trading_bot.log       # Current main log
├── trading_bot.log.1     # Previous (rotated)
├── trading_bot.log.2
├── bot_detailed.log      # Current detailed
├── bot_detailed.log.1
├── bot_errors.log        # Current errors
└── README.md
```

### Archiving

```bash
# Monthly archive
cd logs
DATE=$(date -d "last month" +%Y%m)
tar -czf archive_${DATE}.tar.gz *.log.[5-9] *.log.10
rm -f *.log.[5-9] *.log.10
```

---

## 🎯 Best Practices

### ✅ DO:
- Check logs daily (at least errors)
- Use `./view_logs.sh` for quick review
- Archive old logs monthly
- Monitor error log growth
- Use logs for performance analysis

### ❌ DON'T:
- Delete logs without backup
- Ignore growing error log
- Let logs fill disk (rotation handles this)
- Edit logs manually
- Rely only on console (console output limited)

---

## 📚 Log Queries Cheatsheet

```bash
# Quick stats
./view_logs.sh stats

# Today's activity
grep $(date +%Y-%m-%d) logs/trading_bot.log | grep "ANALYSIS\|TRADE CLOSED"

# Last hour
grep $(date +%Y-%m-%d\ %H) logs/trading_bot.log

# Last 100 lines
tail -100 logs/trading_bot.log

# Specific trade
grep "SOLUSDT_20251023_143000" logs/trading_bot.log

# All from specific hour
grep "2025-10-23 14:" logs/trading_bot.log

# P&L over time
grep "Total P&L" logs/trading_bot.log | tail -20
```

---

## 🎊 Summary

**Professional Logging System provides:**

✅ **3-tier logging** (main, detailed, errors)  
✅ **Automatic rotation** (no manual cleanup)  
✅ **Searchable history** (grep, analysis)  
✅ **Performance tracking** (from logs)  
✅ **Error detection** (dedicated error log)  
✅ **Interactive viewer** (./view_logs.sh)  
✅ **Heartbeat monitoring** (bot alive checks)  

**Benefits:**
- Know exactly what bot did
- Troubleshoot issues fast
- Analyze performance from logs
- Audit trail for all decisions
- Never lose track of bot activity

---

**Logs = Bot's Memory! 📋🧠**

Check them regularly to understand and improve your trading system!

