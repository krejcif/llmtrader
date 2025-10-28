# Web Dashboard 🌐

## 🎯 Trading Bot Web UI

Beautiful web interface pro sledování trades, strategií a performance.

---

## 🚀 Start Dashboard

```bash
./start_dashboard.sh

# Output:
🌐 Starting Trading Dashboard...
📊 Dashboard: http://localhost:5000
⏹️  Press Ctrl+C to stop
```

Otevři browser: **http://localhost:5000**

---

## 📊 Features

### 1. **Real-time Statistics**
- Overall performance (win rate, P&L, ROI)
- Per-strategy breakdown:
  - 📐 STRUCTURED (detailed prompts)
  - 🤖 MINIMAL (AI independent)
  - 🌍 MACRO (news + IXIC)

### 2. **Trade List**
- Recent trades (last 50)
- Strategy badges
- Entry/SL/TP prices
- Status (OPEN/CLOSED)
- P&L (profit green, loss red)
- Timestamps

### 3. **Filtering**
- All trades
- By strategy (structured/minimal/macro)
- By status (open/closed)
- Click to filter instantly

### 4. **Bot Status**
- ✅ Bot Running (PID)
- ⏸️  Bot Stopped
- Real-time check

### 5. **Auto-Refresh**
- Stats refresh every 30s
- Manual refresh button
- Live updates

---

## 🎨 UI Design

**Modern, Clean Interface:**
- Gradient purple background
- White cards with shadows
- Color-coded strategies
- Responsive layout
- Professional typography

**Color Coding:**
- 📐 Structured: Blue
- 🤖 Minimal: Yellow/Orange
- 🌍 Macro: Green
- Profit: Green
- Loss: Red

---

## 📡 API Endpoints

### GET `/api/stats`
```
Returns:
{
  "overall": {...},
  "strategies": {
    "structured": {...},
    "minimal": {...},
    "macro": {...}
  }
}
```

### GET `/api/trades`
```
Params:
  ?status=open|closed
  &strategy=structured|minimal|macro
  &limit=50

Returns:
{
  "trades": [...],
  "count": 50
}
```

### GET `/api/bot-status`
```
Returns:
{
  "running": true,
  "pid": "12345"
}
```

---

## 🔧 Usage

### Start Dashboard
```bash
# Terminal 1: Start dashboard
./start_dashboard.sh

# Opens on http://localhost:5000
```

### Start Bot (separate terminal)
```bash
# Terminal 2: Start trading bot
./bot.sh start

# Bot status will show on dashboard ✅
```

### Access
```bash
# Local
http://localhost:5000

# Remote (if on server)
http://your-server-ip:5000
```

---

## 📊 Example View

```
┌──────────────────────────────────────────────────┐
│  🤖 Trading Bot Dashboard                        │
│  ✅ Bot Running (PID: 12345)      🔄 Refresh    │
└──────────────────────────────────────────────────┘

┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│📊 Overall   │ │📐 Structured│ │🤖 Minimal   │ │🌍 Macro     │
│             │ │             │ │             │ │             │
│  67.5%      │ │  71.2%      │ │  58.3%      │ │  75.0%      │
│ Win Rate    │ │ Win Rate    │ │ Win Rate    │ │ Win Rate    │
│ P&L: $287.5 │ │ P&L: $156.3 │ │ P&L: $85.2  │ │ P&L: $46.0  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘

📋 Recent Trades

[All] [📐 Structured] [🤖 Minimal] [🌍 Macro] [⏳ Open] [✅ Closed]

Strategy    Action  Entry    SL/TP              Status   P&L           Time
────────────────────────────────────────────────────────────────────────────
📐 STRUCTURED  LONG   $190.38  $185.20/$200.74  ✅ CLOSED +$10.36(+5.4%) 10/23 14:30
🤖 MINIMAL     LONG   $190.38  $185.20/$200.74  ⏳ OPEN   Open          10/23 14:30
🌍 MACRO       NEUTRAL  -      -                -         -             10/23 14:30
...
```

---

## 🎯 Benefits

### vs CLI:
- ✅ Visual overview
- ✅ Easy filtering
- ✅ Real-time updates
- ✅ Beautiful UI
- ✅ Shareable (via URL)

### Use Cases:
- Daily performance check
- Strategy comparison
- Share with team
- Mobile-friendly
- Professional presentation

---

## 🔧 Customization

### Change Port
Edit `src/web_api.py`:
```python
app.run(host='0.0.0.0', port=8080)  # Change port
```

### Add Features
API je extensible:
- Add charts (chart.js)
- Add filters
- Export to CSV
- Email alerts
- More stats

---

## 📱 Mobile Responsive

Dashboard works on:
- ✅ Desktop
- ✅ Tablet
- ✅ Mobile
- ✅ Any screen size

---

## ✅ Quick Start

```bash
# 1. Install dependencies (if not done)
pip install flask flask-cors

# 2. Start dashboard
./start_dashboard.sh

# 3. Open browser
http://localhost:5000

# 4. Done! ✨
```

---

**Professional web dashboard for your trading bot! 🌐📊**

