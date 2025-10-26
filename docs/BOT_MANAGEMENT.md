# Bot Management Guide 🤖

## `bot.sh` - Bot Control Script

### Commands

```bash
./bot.sh start      # Start bot in background
./bot.sh stop       # Stop bot gracefully
./bot.sh restart    # Restart bot
./bot.sh status     # Show status + stats
./bot.sh logs       # View live logs
```

---

## 🚀 Starting Bot

### Command
```bash
./bot.sh start
```

### Output
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 STARTING AUTONOMOUS TRADING BOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Virtual environment activated
🚀 Starting bot in background...
✅ Bot started successfully!
   PID: 12345
   Background log: logs/bot_background.log
   Main log: logs/trading_bot.log

📋 Useful commands:
   ./bot.sh status    # Check bot status
   ./bot.sh logs      # View live logs
   ./bot.sh stop      # Stop bot
   ./view_logs.sh     # Interactive log viewer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Bot is running healthy
```

**Bot nyní běží na pozadí!** Můžeš zavřít terminal.

---

## 🛑 Stopping Bot

### Command
```bash
./bot.sh stop
```

### Output
```
🛑 Stopping bot (PID: 12345)...
✅ Bot stopped gracefully
```

**Graceful Shutdown:**
- Bot dostane SIGTERM signal
- Dokončí aktuální operaci
- Uloží final stats do logu
- Zavře cleanly

---

## 📊 Checking Status

### Command
```bash
./bot.sh status
```

### Output
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Bot is RUNNING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   PID: 12345
   Started: Mon Oct 23 10:00:15 2025
   CPU: 2.3%
   Memory: 87.5 MB

📊 Recent Activity:
   2025-10-23 14:30:00 | INFO | ANALYSIS #15 STARTED
   2025-10-23 14:30:05 | INFO | LONG signal: Entry $190.38
   2025-10-23 14:30:06 | INFO | Paper trade created: SOLUSDT_20251023_143000
   2025-10-23 15:30:00 | INFO | Heartbeat: Cycle 720, Analyses: 16
   2025-10-25 18:45:23 | INFO | TRADE CLOSED: SOLUSDT_20251023_143000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

============================================================
📊 TRADING STATISTICS (SOLUSDT)
============================================================

Total Trades: 16
  Open: 3
  Closed: 13

Performance:
  Wins: 10
  Losses: 3
  Win Rate: 76.92%
  Total P&L: $287.50
  Avg P&L: 2.85%
  Rating: 🌟 Excellent
```

---

## 📋 Viewing Logs

### Command
```bash
./bot.sh logs
```

### Output
```
📋 Viewing live logs (Ctrl+C to exit)...

2025-10-23 14:30:00 | INFO | ANALYSIS #15 STARTED - 2025-10-23 14:30:00
2025-10-23 14:30:05 | INFO | Analysis complete: LONG (confidence: high)
2025-10-23 14:30:06 | INFO | Paper trade created: SOLUSDT_20251023_143000
⏰ [14:30:15] Bot running... Cycle 50 | Next analysis: 14:45:00 (890s)
⏰ [14:30:45] Bot running... Cycle 56 | Next analysis: 14:45:00 (860s)
...
```

**Live tail!** Shows everything as it happens.

---

## 🔄 Restarting Bot

### Command
```bash
./bot.sh restart
```

### When to Restart
- After changing .env configuration
- After updating code
- If bot behaving strangely
- To apply new settings

**Restart = Stop + Start (graceful)**

---

## ⏰ Candle Synchronization

### How It Works

**Problem:**
```
Current time: 14:37:23
TF: 15m
If analysis runs now → misaligned with candles
```

**Solution:**
```
Analysis #1: Runs immediately (14:37:23) ✅
  ↓
Calculate next 15m candle: 14:45:00
Wait: 7min 37s
  ↓
Analysis #2: Runs at 14:45:00 ✅ (NEW CANDLE!)
  ↓
Analysis #3: Runs at 15:00:00 ✅ (NEW CANDLE!)
  ↓
And so on... every 15 minutes on the dot
```

### Example Timeline (15m TF)

```
14:37:23 - Bot starts
14:37:24 - Analysis #1 (immediate)
14:37:24 - Next scheduled: 14:45:00

14:37:30 - Monitoring trades...
14:38:30 - Monitoring trades...
...
14:44:50 - Preparing for analysis...
14:45:00 - Analysis #2 (SYNCHRONIZED!) ✅
14:45:00 - Next scheduled: 15:00:00

14:45:10 - Monitoring trades...
...
15:00:00 - Analysis #3 (SYNCHRONIZED!) ✅
15:00:00 - Next scheduled: 15:15:00
```

### Benefits

✅ **Clean data** - každá analýza má čerstvý completed candle  
✅ **No lag** - analýza na nejnovějších datech  
✅ **Predictable** - víš přesně kdy analýza běží  
✅ **Professional** - jako institucionální systémy  

### For Different Timeframes

**15m TF:**
```
Analyses at: XX:00, XX:15, XX:30, XX:45
Example: 10:00, 10:15, 10:30, 10:45, 11:00...
```

**1h TF:**
```
Analyses at: XX:00 (every hour)
Example: 10:00, 11:00, 12:00, 13:00...
```

**5m TF:**
```
Analyses at: XX:00, XX:05, XX:10, XX:15, XX:20...
Example: 10:00, 10:05, 10:10, 10:15...
```

**4h TF:**
```
Analyses at: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
```

---

## 🔍 Monitoring Bot

### Check if Running
```bash
./bot.sh status

# Or manually
ps aux | grep trading_bot
```

### View Activity
```bash
# Live logs
./bot.sh logs

# Or specific views
./view_logs.sh live
./view_logs.sh stats
./view_logs.sh wins
```

### Performance Check
```bash
./bot.sh status  # Shows stats at bottom

# Or detailed
cd src
python trade_manager.py stats
```

---

## 📁 Background Files

### PID File
```
bot.pid

Contains: Process ID of running bot
Location: Project root
Purpose: Track bot process
```

### Background Log
```
logs/bot_background.log

Contains: stdout/stderr from background process
Purpose: Capture any uncaught output
```

### Main Logs
```
logs/trading_bot.log     # Main operations
logs/bot_detailed.log    # Debug details
logs/bot_errors.log      # Errors only
```

---

## 🔧 Advanced Usage

### Start with Custom Intervals

Edit `.env`:
```env
BOT_ANALYSIS_INTERVAL=900   # Will be overridden by candle sync
BOT_MONITOR_INTERVAL=30     # Check trades every 30s (faster)
```

Then:
```bash
./bot.sh restart
```

**Note:** Analysis interval is automatically synced to TF, but you can set base interval.

### Run in Foreground (for debugging)
```bash
cd src
python trading_bot.py

# See all output directly
# Ctrl+C to stop
```

### Multiple Bots (Different Symbols)
```bash
# Create separate .env files
cp .env .env.btc
cp .env .env.eth

# Edit each with different SYMBOL=
# Run separate instances (advanced)
```

---

## 🚨 Troubleshooting

### "Bot is already running"
```bash
# Check status
./bot.sh status

# If you want to restart anyway
./bot.sh restart
```

### "Bot not starting"
```bash
# Check background log
tail logs/bot_background.log

# Check for errors
./view_logs.sh errors

# Common issues:
# - Missing .env
# - Wrong DEEPSEEK_API_KEY
# - Missing dependencies
```

### "Stale PID file"
```bash
# Script handles this automatically
# But if needed:
rm -f bot.pid
./bot.sh start
```

### "Bot crashed"
```bash
# Check why
tail -50 logs/bot_background.log
tail -50 logs/bot_errors.log

# Restart
./bot.sh start
```

---

## 💡 Best Practices

### Daily Routine
```bash
# Morning
./bot.sh status     # Check bot is running
./view_logs.sh wins  # See overnight wins

# Evening
./bot.sh status     # Check performance
```

### Weekly Maintenance
```bash
# Sunday evening
./bot.sh status          # Review week
cd src && python trade_manager.py stats

# Backup
cp data/paper_trades.db backups/db_$(date +%Y%m%d).db

# Optional: Restart for fresh start
./bot.sh restart
```

### After Changes
```bash
# Modified .env or code?
./bot.sh restart

# Check it restarted OK
./bot.sh status
```

---

## 📊 Bot Lifecycle

```
USER: ./bot.sh start
  ↓
Script:
  1. Check if already running
  2. Activate venv
  3. Start trading_bot.py in background (nohup)
  4. Save PID to bot.pid
  5. Verify bot started
  ↓
Bot Process:
  - Runs analysis immediately
  - Calculates next candle time
  - Waits for next candle
  - Then runs on TF schedule
  - Monitors trades continuously
  ↓
USER: ./bot.sh status
  ↓
Script shows:
  - PID, uptime, resources
  - Recent log entries
  - Trading statistics
  ↓
USER: ./bot.sh stop
  ↓
Script:
  1. Read PID from bot.pid
  2. Send SIGTERM (graceful)
  3. Wait up to 10s
  4. Force kill if needed
  5. Remove bot.pid
  ↓
Bot Process:
  - Catches SIGTERM
  - Finishes current operation
  - Logs final stats
  - Exits cleanly
```

---

## 🎯 Quick Reference

```bash
# Start
./bot.sh start

# Check
./bot.sh status

# Logs
./bot.sh logs           # Live
./view_logs.sh wins     # Wins only

# Stats
cd src && python trade_manager.py stats

# Stop
./bot.sh stop
```

---

## ⚠️ Important Notes

### Bot Runs in Background
- ✅ Can close terminal
- ✅ Runs independently
- ✅ Survives SSH disconnect
- ❌ Stops on server reboot (use systemd for persistence)

### Auto-Restart on Reboot
```bash
# Add to crontab
crontab -e

# Add:
@reboot cd /home/flow/langtest && ./bot.sh start
```

### PID File
- Created when bot starts
- Deleted when bot stops
- Used to track process
- Don't delete manually while bot running!

---

## 🎊 Summary

**bot.sh provides:**

✅ **Background operation** - Bot runs independently  
✅ **Easy management** - Simple commands  
✅ **Status monitoring** - Know what's happening  
✅ **Graceful shutdown** - No data loss  
✅ **Automatic recovery** - Handles stale PIDs  

**One script to manage everything! 🎯**

---

## 📈 Candle Synchronization

### Feature: Smart Analysis Timing

**Old way (fixed interval):**
```
Start: 14:37:23
Analysis every 900s:
- 14:37:23 (start)
- 14:52:23 (900s later)
- 15:07:23 (900s later)

❌ Not aligned with candles!
```

**New way (candle-synced):**
```
Start: 14:37:23
TF: 15m

Analysis #1: 14:37:23 (immediate) ✅
Calculate next 15m candle: 14:45:00
Wait: 462 seconds

Analysis #2: 14:45:00 (NEW CANDLE!) ✅
Analysis #3: 15:00:00 (NEW CANDLE!) ✅
Analysis #4: 15:15:00 (NEW CANDLE!) ✅
...

✅ Perfect alignment!
```

### Why It Matters

**Misaligned:**
```
Time: 14:37:00
15m candle: 14:30:00 - 14:45:00 (not finished yet)

Analysis uses incomplete candle
→ Indicators incorrect
→ Decisions based on partial data
❌ Suboptimal
```

**Aligned:**
```
Time: 14:45:00
15m candle: 14:30:00 - 14:45:00 (COMPLETE!)

Analysis uses complete candle
→ Indicators accurate
→ Decisions on full data
✅ Optimal
```

### Automatic for All Timeframes

```
5m:  Syncs to XX:00, XX:05, XX:10, XX:15...
15m: Syncs to XX:00, XX:15, XX:30, XX:45
30m: Syncs to XX:00, XX:30
1h:  Syncs to XX:00
4h:  Syncs to 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
```

**Bot detekuje timeframe automaticky a synchronizuje!**

---

## 🎯 Example Session

```bash
# Monday 14:37 - Start bot
./bot.sh start

Output:
🚀 Running initial analysis... (14:37:23)
⏰ Next analysis synchronized to 15m candle:
   Scheduled at: 14:45:00
   Wait time: 462s (7min 42s)

# Bot running in background...

# Check status anytime
./bot.sh status

Output:
✅ Bot is RUNNING
   Analyses run: 1
   Next: 14:45:00

# 14:45:00 - Automatic analysis
# (Bot runs on schedule)

# 15:00:00 - Automatic analysis
# 15:15:00 - Automatic analysis
# ... every 15 minutes

# Tuesday 18:00 - Check results
./bot.sh status

Output:
Analyses run: 52
Trades created: 8
Win rate: 75%
Total P&L: $156.80 ✅

# Stop when needed
./bot.sh stop
```

---

**Perfect bot management + perfect timing! ⏰🤖✨**

