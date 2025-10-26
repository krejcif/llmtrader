# 📊 Live P&L Feature

## Overview
Real-time P&L calculation for open positions displayed in the web dashboard.

## Backend Implementation

### API Endpoint: `/api/trades`
```python
# Fetches current prices from Binance
# Calculates live P&L % for OPEN positions
# LONG: ((current - entry) / entry) * 100
# SHORT: ((entry - current) / entry) * 100
```

**Response Format:**
```json
{
  "status": "OPEN",
  "entry_price": 192.42,
  "current_price": 192.79,
  "live_pnl_dollars": 0.37,      // +$0.37
  "live_pnl_percentage": 0.19,   // +0.19%
  "action": "LONG"
}
```

## Frontend Display

### Open Positions
- ✅ Shows **live P&L $ and %** (same format as closed)
- 🟢 Green color for profit (+$)
- 🔴 Red color for loss (-$)
- 📊 Live indicator emoji

**Display Format:**
```
+$0.27 (+0.14%) 📊  (profit, green)
-$0.15 (-0.08%) 📊  (loss, red)
```

### Closed Positions
```
+$2.34 (+1.21%)  (final P&L)
-$1.45 (-0.75%)  (final P&L)
```

## Features

### Auto-Refresh
- Dashboard refreshes every 15 seconds
- Live P&L updates automatically
- No manual refresh needed

### Performance
- Efficient batch price fetching
- Only queries open positions
- Refreshes every 15s (optimal for live trading)

## Example

**Trade Entry:**
- Entry: $192.42
- Action: LONG

**Current Status:**
- Current Price: $192.79
- Live P&L: **+$0.37 (+0.19%)** 📊 (in green)

**At TP ($193.74):**
- Would show: **+$1.32 (+0.69%)** 📊

**At SL ($191.76):**
- Would show: **-$0.66 (-0.34%)** 📊

## Usage

1. Start web server:
```bash
cd /home/flow/langtest
python3 src/web_api.py
```

2. Open browser:
```
http://localhost:5000
```

3. View trades table:
- Open positions show live P&L $ and %
- Auto-updates every 15s
- Color-coded profit/loss

## Benefits

✅ Real-time position monitoring  
✅ Quick profit/loss assessment  
✅ Better risk management  
✅ No need to calculate manually  
✅ Color-coded for quick scanning  

## Technical Notes

- Uses Binance public API (no auth needed)
- Graceful error handling (shows "Open" if price fetch fails)
- Minimal performance impact
- Works with all strategies

