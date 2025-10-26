# ATR-Based Risk Management 💰

## Co je ATR?

**Average True Range (ATR)** = měří volatilitu trhu.

- **Vysoká ATR**: Volatilní trh, velké price swings
- **Nízká ATR**: Klidný trh, malé pohyby

**Proč používat ATR pro stops?**
✅ Dynamické (adjust to volatility)  
✅ Ne arbitrary fixed stops  
✅ Respektuje market conditions  
✅ Lepší R/R ratio  

---

## Implementace v Systému

### Výpočet ATR

```python
ATR(14) = Average of True Range over 14 periods

True Range = max of:
- High - Low
- |High - Previous Close|
- |Low - Previous Close|
```

**Příklad:**
```
SOLUSDT Current: $190.38
ATR(14): $3.45
ATR%: 1.81% of price
```

---

## Stop Loss & Take Profit

### Formule

```python
LONG:
  Entry = Current Price
  Stop Loss = Entry - (1.5 × ATR)
  Take Profit = Entry + (3.0 × ATR)

SHORT:
  Entry = Current Price
  Stop Loss = Entry + (1.5 × ATR)
  Take Profit = Entry - (3.0 × ATR)
```

### Proč 1.5x a 3.0x?

**Stop Loss: 1.5x ATR**
- Dává pozici "breathing room"
- Není hit při normal volatility
- Ne příliš wide (acceptable risk)

**Take Profit: 3.0x ATR**
- R/R ratio = 3.0 / 1.5 = **2.0** (1:2)
- Professional standard
- Dosažitelný target

---

## Příklady

### Low Volatility Market
```
SOLUSDT @ $190
ATR: $2.00 (1.05% volatility)

LONG Entry:
  Entry: $190.00
  Stop:  $187.00 (-$3.00, -1.58%)
  TP:    $196.00 (+$6.00, +3.16%)
  R/R:   1:2.0

Risk: Tight stop (1.58%)
Reward: Modest target (3.16%)
```

### High Volatility Market
```
SOLUSDT @ $190
ATR: $6.00 (3.16% volatility)

LONG Entry:
  Entry: $190.00
  Stop:  $181.00 (-$9.00, -4.74%)
  TP:    $208.00 (+$18.00, +9.47%)
  R/R:   1:2.0

Risk: Wide stop (4.74%)
Reward: Large target (9.47%)
```

**Důležité:** R/R ratio je stejný (1:2), ale dollar amounts jsou adjusted k volatilitě!

---

## Výhody ATR-Based Stops

### 1. Volatility-Adjusted
```
Klidný trh (ATR 1%):
  Stop: -1.5% | TP: +3.0%
  → Tight, efektivní

Volatilní trh (ATR 4%):
  Stop: -6.0% | TP: +12.0%
  → Wide, ale nutné
```

### 2. Market Context Aware
- **Bull run s vysokou volatilitou**: Wide stops ne vyhodí
- **Ranging market s low volatilitou**: Tight stops chrání capital
- **Crash (extreme ATR)**: Velmi wide stops = možná better skip

### 3. Consistent R/R
- Vždy minimálně 1:2 R/R ratio
- Scales s market conditions
- Professional standard

### 4. Ne Arbitrary
- ❌ "Stop na $185" - proč? Arbitrary
- ✅ "Stop na 1.5x ATR" - based on volatility

---

## Risk Management v Systému

### Automatický Výpočet

Systém **automaticky** vypočítá při LONG/SHORT:

```python
if action == "LONG":
    calculate_stop_take_profit(
        df=candles_15m,  # Lower TF pro responsive stops
        direction='bullish',
        atr_multiplier_stop=1.5,
        atr_multiplier_tp=3.0
    )
```

### Output

```
💰 RISK MANAGEMENT (ATR-Driven):
   Entry Price:   $190.38
   Stop Loss:     $185.20 (-2.72%)
   Take Profit:   $200.74 (+5.44%)
   
   Risk:   $5.18 (2.72%)
   Reward: $10.36 (5.44%)
   R/R Ratio: 1:2.0
   
   ATR (14): $3.45 (1.81% of price)
   Stop: 1.5x ATR | Target: 3.0x ATR
```

---

## Position Sizing (Example)

### 1% Risk Rule

```
Account: $10,000
Risk per trade: 1% = $100

Entry: $190.38
Stop: $185.20
Risk per unit: $5.18

Position Size = $100 / $5.18 = 19.3 units
→ Buy ~19 SOL

Max loss if stopped: $100 (1% of account)
Potential profit: $200 (2% of account)
```

### Výpočet v systému

```python
# V calculate_stop_take_profit():
account_size = 10000  # Example
risk_percentage = 0.01  # 1%
risk_amount = account_size * risk_percentage  # $100
position_size = risk_amount / risk  # Units to buy
```

---

## ATR Interpretace

### ATR Percentage Ranges

**Very Low Volatility** (< 1%)
```
ATR: 0.8%
Stop: -1.2% | TP: +2.4%
→ Tight, ale můžou být whipsaws
→ Menší profit potential
```

**Low Volatility** (1-2%)
```
ATR: 1.5%
Stop: -2.25% | TP: +4.5%
→ Good balance
→ Reasonable targets
```

**Medium Volatility** (2-3%)
```
ATR: 2.5%
Stop: -3.75% | TP: +7.5%
→ Wider stops needed
→ Good profit potential
```

**High Volatility** (3-5%)
```
ATR: 4.0%
Stop: -6.0% | TP: +12.0%
→ Very wide stops
→ High profit potential, high risk
```

**Extreme Volatility** (> 5%)
```
ATR: 6.0%
Stop: -9.0% | TP: +18.0%
→ Příliš risky pro většinu traders
→ Consider avoiding or reduce position size
```

---

## Adjusting ATR Multipliers

### Conservative (Risk-Averse)
```env
Stop: 2.0x ATR
TP:   4.0x ATR
R/R:  1:2

→ Wider stops (less hit)
→ Larger targets
→ Lower win rate, but better R/R
```

### Standard (Balanced) - Default
```env
Stop: 1.5x ATR
TP:   3.0x ATR
R/R:  1:2

→ Balance between whipsaws a targets
→ Good for most conditions
```

### Aggressive (Risk-Seeking)
```env
Stop: 1.0x ATR
TP:   2.5x ATR
R/R:  1:2.5

→ Tight stops (more whipsaws)
→ Closer targets (hit faster)
→ Higher win rate, but more stopped
```

---

## Praktický Příklad

### Scenario: SOLUSDT Pullback Entry

**Setup:**
```
1h: bullish trend
15m: pullback reversal
MACD: bullish crossover
Orderbook: 58% buy pressure
RSI: 52 (healthy)
```

**ATR Analysis:**
```
Current Price: $190.38
ATR (14 na 15m): $3.45
ATR%: 1.81% (normal volatility)
```

**Risk Management:**
```
Entry:  $190.38
Stop:   $185.20 (1.5 × $3.45 = $5.18 below)
TP:     $200.74 (3.0 × $3.45 = $10.36 above)

Risk:   $5.18 (-2.72%)
Reward: $10.36 (+5.44%)
R/R:    1:2.0
```

**Position Sizing:**
```
Account: $10,000
Risk: 1% = $100
Position: $100 / $5.18 = 19.3 SOL

Max loss: $100 (-1% account)
Potential profit: $200 (+2% account)
```

**Execution:**
```
BUY 19 SOL @ $190.38
Stop Loss Order @ $185.20
Take Profit Order @ $200.74
```

---

## Výhody vs Fixed Stops

### ❌ Fixed Stops
```
"Vždy stop na -3%"

Problémy:
- V low volatility: zbytečně wide
- V high volatility: příliš tight (hit často)
- Ignoruje market conditions
```

### ✅ ATR Stops
```
"Stop na 1.5x ATR"

Výhody:
- Adjust to current volatility
- Respektuje market rhythm
- Consistent risk across conditions
- Professional approach
```

---

## Integration s Entry Setups

### Pullback Reversal
```
Entry: Better (early in move)
Stop: Tight (pod pullback low)
ATR: Normal spacing
R/R: Often >1:2 (excellent)
```

### Aligned Running
```
Entry: Later (trend running)
Stop: Normal ATR-based
ATR: Same spacing
R/R: 1:2 (acceptable if strong confirmation)
```

**ATR ensures consistent risk regardless of entry type!**

---

## Monitoring & Adjustment

### During Trade

**If price moves in your favor:**
```
Price: $190 → $195 (halfway to TP)
Option: Move stop to breakeven ($190.38)
→ Risk-free trade
```

**If volatility increases:**
```
ATR: 1.8% → 3.5% (doubled)
Option: Recalculate nebo accept wider stop
→ Don't adjust mid-trade usually
```

**If near TP:**
```
Price: $199 (close to $200.74 TP)
Option: Partial profit (50%) + let rest run
→ Lock gains
```

---

## Best Practices

### ✅ DO:
- Use ATR from entry timeframe (15m)
- Respect the calculated stops
- Don't move stop against you
- Consider partial profits
- Recalculate for each new trade

### ❌ DON'T:
- Use fixed percentage stops
- Move stop closer "to be safe"
- Ignore high ATR warnings
- Override ATR with emotions
- Set unrealistic targets

---

## System Implementation

### Files Modified:
- ✅ `utils/indicators.py` - ATR calculation & SL/TP logic
- ✅ `agents/decision_maker.py` - Auto-calculate after AI decision
- ✅ `main.py` - Display risk management
- ✅ README.md - Documentation

### Usage:
```bash
./run.sh

→ System automatically calculates:
   - ATR on 15m timeframe
   - Stop Loss (1.5x ATR)
   - Take Profit (3.0x ATR)
   - R/R ratio
   - Risk in $ and %
```

---

## Konfigurace (Advanced)

Pokud chceš upravit ATR multipliers, edituj `src/agents/decision_maker.py`:

```python
risk_mgmt = calculate_stop_take_profit(
    candles_lower, 
    direction,
    atr_multiplier_stop=2.0,  # ← Change here (conservative)
    atr_multiplier_tp=4.0     # ← Change here
)
```

Default (1.5, 3.0) je dobrý pro většinu traderů.

---

## Summary

**ATR-Driven Risk Management poskytuje:**

✅ **Dynamic stops** adjusted to volatility  
✅ **Consistent R/R** ratio (min 1:2)  
✅ **Professional approach** used by institutions  
✅ **Better risk control** než fixed stops  
✅ **Automatic calculation** - žádný manual work  

**"Let volatility guide your risk, not arbitrary percentages!" 📊**

---

Systém nyní automaticky vypočítá a zobrazí ATR-based stop loss a take profit pro každé LONG/SHORT doporučení! 🎯

