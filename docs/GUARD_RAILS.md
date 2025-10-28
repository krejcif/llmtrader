# 🛡️ GUARD RAILS DOCUMENTATION

**Strategy:** MINIMAL  
**Date Added:** 2025-10-27  
**Purpose:** Prevent AI from making trades against obvious market momentum

---

## 📋 Active Guard Rails

### Guard Rail #1: Momentum Alignment Check

**Location:** `decision_minimal.py` (lines 167-201)

**When:** After AI makes recommendation, before risk management calculation

**Logic:**
```python
# Check last 2 candles momentum
last_3_closes = [close[-3], close[-2], close[-1]]

# Determine momentum direction
momentum_bullish = close[-1] > close[-2] AND close[-2] > close[-3]
momentum_bearish = close[-1] < close[-2] AND close[-2] < close[-3]

# Override if misaligned
if AI says LONG and momentum_bearish:
    → Change to NEUTRAL
    
if AI says SHORT and momentum_bullish:
    → Change to NEUTRAL
```

**Example Scenarios:**

✅ **ALLOWED:**
- AI: LONG, Market: $100 → $101 → $102 (2 green candles) ✅
- AI: SHORT, Market: $102 → $101 → $100 (2 red candles) ✅
- AI: LONG, Market: $100 → $99 → $100.5 (mixed) ✅

❌ **BLOCKED:**
- AI: LONG, Market: $102 → $101 → $100 (2 red) → **NEUTRAL**
- AI: SHORT, Market: $100 → $101 → $102 (2 green) → **NEUTRAL**

**Reasoning:**
- Prevents counter-trend entries (fighting momentum)
- Allows trades only when price momentum supports the direction
- Reduces losses from poor timing
- Mixed momentum (1 up, 1 down) is allowed (not clearly opposite)

---

## 📊 Impact Tracking

To track guard rail effectiveness, check strategy logs:

```sql
SELECT 
    COUNT(*) as overrides,
    reasoning
FROM strategy_runs
WHERE strategy = 'minimal' 
    AND reasoning LIKE '%GUARD RAIL OVERRIDE%'
GROUP BY reasoning;
```

---

## 🔮 Future Guard Rails (Planned)

### Guard Rail #2: Volume Confirmation
- Require minimum volume on breakouts
- Prevent trades on thin volume

### Guard Rail #3: Support/Resistance Respect
- Block LONG near strong resistance
- Block SHORT near strong support

### Guard Rail #4: Volatility Filter
- Skip trades when ATR too high (choppy)
- Skip trades when ATR too low (range-bound)

### Guard Rail #5: Time-based Filter
- Avoid trading during known bad hours (e.g., 02:00-03:00 UTC)

---

## 🎯 Design Principles

1. **After AI, not instead of AI:** Guard rails check AI output, don't replace AI
2. **Clear logic:** Each guard rail has simple, testable logic
3. **Override to NEUTRAL:** Don't flip direction, just stay out
4. **Logged:** All overrides are logged for analysis
5. **Removable:** Each guard rail can be disabled independently

---

## 📈 Performance Monitoring

Monitor these metrics to evaluate guard rails:

- **Override Rate:** % of AI recommendations overridden
- **Avoided Losses:** Compare P&L of overridden signals
- **False Positives:** Good trades that were blocked
- **Win Rate Impact:** Before/after guard rail implementation

---

**Last Updated:** 2025-10-27  
**Next Review:** After 100 trades with Guard Rail #1

