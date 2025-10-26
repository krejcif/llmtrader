# ⏳ Trade Cooldown Mechanism

## Problem Identified

**Scenario:**
```
12:16 - Trade #1 opens at $192.42
12:30 - Trade #1 hits TP at $193.74 ✅ +$1.32
12:31 - Bot runs again (15min interval)
12:31 - Trade #2 opens at $195.74 🚨 ($2 higher!)
12:33 - Trade #2 hits SL at $194.78 ❌ -$0.96
```

**Root Cause:**
- No cooldown period after trade closes
- Bot can re-enter immediately if analysis runs soon after close
- Price may have moved significantly → poor entry → quick SL

---

## Solution: 30-Minute Cooldown

### Implementation

**File: `src/agents/paper_trading.py`**

```python
# After checking for open trades, check cooldown:
if last_trade_closed and time_since_exit < 30 minutes:
    SKIP re-entry
    WAIT until cooldown expires
```

### Logic Flow

```
1. Strategy has LONG signal
2. ✅ Check: No open trades
3. ✅ Check: Last trade closed time
4. ⏰ IF closed < 30min ago → SKIP (cooldown)
5. ✅ IF closed > 30min ago → ALLOW entry
```

---

## Benefits

### 1. Prevents Chasing
```
Before Cooldown:
  TP @ $193.74 → Immediately re-enter @ $195.74 ❌
  
After Cooldown:
  TP @ $193.74 → Wait 30min → Better entry or skip ✅
```

### 2. Allows Market Settle
- Price can consolidate after TP/SL
- Avoids entering in momentum spike
- Better quality entries

### 3. Reduces Overtrading
- Natural brake on trade frequency
- Protects capital
- More selective entries

---

## Example Timeline

```
12:00 - Trade opens at $192.00
12:25 - Trade closes (TP) at $194.00 ✅
12:30 - Bot runs: COOLDOWN active (5min since close)
       "⏳ [MACRO] COOLDOWN - Last trade closed 5.0min ago"
       "Waiting 25.0min more before re-entry"
12:45 - Bot runs: COOLDOWN active (20min since close)
       "⏳ [MACRO] COOLDOWN - Last trade closed 20.0min ago"
       "Waiting 10.0min more before re-entry"
13:00 - Bot runs: COOLDOWN expired (35min since close)
       ✅ Can enter new trade if signal present
```

---

## Configuration

### Current Settings (Strategy-Specific)
```python
COOLDOWN_MAP = {
    'structured': 45,   # Swing: longer cooldown for quality
    'minimal': 30,      # Medium: balanced approach
    'macro': 30,        # Swing: medium cooldown
    'intraday': 20,     # Intraday: shorter for more opportunities
    'intraday2': 15     # Mean reversion: shortest (frequent trades)
}
```

### Rationale by Strategy

**📐 STRUCTURED (45 min):**
- Swing trading strategy
- Needs quality setups
- Longer cooldown prevents overtrading

**🤖 MINIMAL (30 min):**
- AI-driven, balanced approach
- Standard cooldown period

**🌍 MACRO (30 min):**
- News + BTC correlation
- Medium cooldown for macro shifts

**⚡ INTRADAY (20 min):**
- Session-based scalping
- More frequent opportunities
- Shorter cooldown appropriate

**🔄 INTRADAY2 (15 min):**
- Mean reversion on BB extremes
- Highest trade frequency
- Shortest cooldown allows multiple setups per day

---

## Log Output

**When cooldown active:**
```
⏳ [MACRO] COOLDOWN (30min) - Last trade closed 5.2min ago
   Waiting 24.8min more before re-entry

⏳ [INTRADAY2] COOLDOWN (15min) - Last trade closed 8.1min ago
   Waiting 6.9min more before re-entry

⏳ [STRUCTURED] COOLDOWN (45min) - Last trade closed 12.3min ago
   Waiting 32.7min more before re-entry
```

**When cooldown expired:**
```
✅ [MACRO] Cooldown expired (32min since last close)
   Evaluating new entry...
```

---

## Testing Scenarios

### Scenario 1: Rapid TP Hit
```
Entry: $100
TP hit: $102 after 5 minutes
Bot runs 2min later:
  → COOLDOWN (only 7min since close)
  → Skips entry
```

### Scenario 2: Normal Trade Duration
```
Entry: $100
TP hit: $102 after 45 minutes
Bot runs 15min later:
  → NO COOLDOWN (60min since entry, 15min since close)
  → But cooldown still active (need 30min from close)
  → Skips entry
```

### Scenario 3: Cooldown Expired
```
Entry: $100
TP hit: $102 after 30 minutes
Bot runs 40min later:
  → COOLDOWN expired (40min > 30min)
  → Can enter new trade ✅
```

---

## Impact on Problem Trade

**Before (Without Cooldown):**
```
12:30:50 - Trade #1 closes (TP) at $193.74
12:31:52 - Trade #2 opens at $195.74 ❌
           (Only 1min gap - bad entry)
```

**After (With Cooldown):**
```
12:30:50 - Trade #1 closes (TP) at $193.74
12:31:52 - Bot runs → COOLDOWN ⏳
           "Last trade closed 1.0min ago"
           "Waiting 29.0min more"
12:46:52 - Bot runs → COOLDOWN ⏳
           "Last trade closed 16.0min ago"
           "Waiting 14.0min more"
13:01:52 - Bot runs → Cooldown expired ✅
           Can evaluate new entry
```

---

## Statistics Improvement Expected

**Before Cooldown:**
- Multiple quick re-entries
- Some poor entry prices
- Lower win rate on follow-up trades

**After Cooldown:**
- Fewer but better entries
- Higher quality setups
- Better overall P&L
- Reduced drawdown

---

## Monitoring

Check logs for cooldown activity:
```bash
grep "COOLDOWN" logs/trading_bot.log
```

Expected output:
```
⏳ [MACRO] COOLDOWN - Last trade closed 5.2min ago
⏳ [INTRADAY] COOLDOWN - Last trade closed 12.8min ago
```

---

## Summary

✅ **30-minute cooldown** after any trade closes  
✅ Prevents rapid re-entry at poor prices  
✅ Allows market to settle  
✅ Improves entry quality  
✅ Configurable per strategy  
✅ Logged for monitoring  

**Result:** Better risk management, fewer bad trades, higher win rate.

