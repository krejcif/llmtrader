# Quick Reference Guide 📖

## 🚀 Essential Commands

### Start/Stop Bot
```bash
./start_bot.sh                    # Start autonomous bot
Ctrl+C                            # Stop gracefully
pkill -f trading_bot              # Force stop
```

### View Logs
```bash
./view_logs.sh live               # Live main log
./view_logs.sh errors             # Errors only
./view_logs.sh wins               # Winning trades
./view_logs.sh stats              # Statistics
```

### Check Performance
```bash
cd src
python trade_manager.py stats     # Overall stats
python trade_manager.py list      # All trades
python trade_manager.py list --status open   # Open only
```

---

## 📁 Important Files

### Configuration
- **`.env`** - Your API keys and settings
- **`requirements.txt`** - Python dependencies

### Data
- **`data/paper_trades.db`** - All trades
- **`results/*.json`** - Analysis results
- **`logs/*.log`** - Bot activity logs

### Scripts
- **`start_bot.sh`** - Main bot launcher
- **`run.sh`** - Single analysis
- **`monitor.sh`** - Trade monitor only
- **`view_logs.sh`** - Log viewer

---

## ⚙️ Configuration (.env)

```env
# Required
DEEPSEEK_API_KEY=your_key         # Get from platform.deepseek.com

# Trading
SYMBOL=SOLUSDT                    # Trading pair
TIMEFRAME_HIGHER=1h               # Trend timeframe
TIMEFRAME_LOWER=15m               # Entry timeframe

# Bot
BOT_ANALYSIS_INTERVAL=900         # 15 min
BOT_MONITOR_INTERVAL=60           # 1 min
```

---

## 📊 Common Tasks

### Daily Check
```bash
# Morning routine
./view_logs.sh closures           # What closed overnight?
cd src && python trade_manager.py stats   # Performance check
```

### Weekly Review
```bash
cd src
python trade_manager.py stats     # Overall performance
python trade_manager.py list --limit 50   # Recent trades
cd ../logs
grep "Win rate" trading_bot.log | tail -20   # Win rate trend
```

### Troubleshooting
```bash
# Is bot running?
ps aux | grep trading_bot

# Any errors?
./view_logs.sh errors

# Check last analysis
./view_logs.sh analyses | tail -5
```

---

## 🎯 Entry Setups (What Bot Detects)

### 💎 Strong Reversal (75-100)
```
Trend změna s high confirmation
R/R: 1:4+
Confidence: HIGH
Example: Catching bottom/top
```

### 💡 Pullback Reversal
```
Korekce v trendu končí
R/R: 1:3
Confidence: HIGH
Example: Healthy pullback entry
```

### 📊 Aligned Running
```
Trend už běží
R/R: 1:2
Confidence: MEDIUM (with confirmation)
Example: Late but strong momentum
```

### ⏳ Wait / Neutral
```
Nejasné signály nebo v pullbacku
Action: NEUTRAL
Example: Patience
```

---

## 📈 Performance Metrics

### Good Performance:
```
Win Rate: >65%
Total P&L: Positive
Avg P&L: >2%
R/R Ratio: >1.5
```

### Needs Improvement:
```
Win Rate: <55%
Total P&L: Negative
Many SL hits: Review strategy
```

---

## 🔍 Log Examples

### Successful Trade
```
14:30:00 | INFO | ANALYSIS #15 STARTED
14:30:05 | INFO | LONG signal: Entry $190.38, SL $185.20, TP $200.74
14:30:06 | INFO | Paper trade created: SOLUSDT_20251023_143000
...
18:45:23 | INFO | TRADE CLOSED: SOLUSDT_20251023_143000
18:45:23 | INFO |   P&L: +$10.36 (+5.44%)
```

### Failed Trade
```
10:00:00 | INFO | SHORT signal: Entry $195.00, SL $201.00
10:00:01 | INFO | Paper trade created: SOLUSDT_xxx
...
14:22:15 | INFO | TRADE CLOSED: SOLUSDT_xxx
14:22:15 | INFO |   P&L: -$6.00 (-3.08%)
14:22:15 | INFO |   Exit: $201.00 (SL_HIT)
```

---

## ⚠️ Common Issues

### Bot not creating trades?
```
→ Check logs: ./view_logs.sh analyses
→ All NEUTRAL? Market možná ranging
→ Review AI reasoning in logs
```

### Trades not closing?
```
→ Bot must be running!
→ Check: ps aux | grep trading_bot
→ If stopped: ./start_bot.sh
```

### Too many errors?
```
→ Check: ./view_logs.sh errors
→ API issues? Network problems?
→ Review bot_errors.log
```

---

## 📚 Documentation Quick Links

- **Setup**: QUICKSTART.md
- **Bot Usage**: AUTONOMOUS_BOT.md  
- **Logging**: BOT_LOGGING.md
- **Strategy**: PULLBACK_ENTRY_STRATEGY.md
- **Full List**: README.md

---

## 🎯 Support

### Issues?
1. Check README.md
2. Check relevant guide
3. Review logs (./view_logs.sh)
4. Check bot_errors.log

### Questions?
- Read AUTONOMOUS_BOT.md
- Read BOT_LOGGING.md
- Check FINAL_SYSTEM_SUMMARY.md

---

## ✅ Checklist

### Before Starting:
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] .env configured with DEEPSEEK_API_KEY
- [ ] Understanding bot will run 24/7

### After Starting:
- [ ] Bot started: `./start_bot.sh`
- [ ] Check first analysis in logs
- [ ] Verify trade creation (if signal)
- [ ] Set up daily check routine

### Ongoing:
- [ ] Check stats daily
- [ ] Review logs weekly
- [ ] Backup database weekly
- [ ] Analyze performance monthly

---

## 🎊 Quick Win

**Get first trade in 30 minutes:**

```bash
# 1. Setup (10 min)
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Add DEEPSEEK_API_KEY

# 2. Start (1 min)
./start_bot.sh

# 3. Wait (15-20 min)
# Bot runs initial analysis
# If market has setup → Creates trade

# 4. Check (5 min)
cd src
python trade_manager.py list

# See your first paper trade! ✅
```

---

**That's all you need! Start trading autonomously! 🤖📈**

