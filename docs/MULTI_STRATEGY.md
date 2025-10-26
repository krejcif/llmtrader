# Multi-Strategy System 🆚

## 🎯 Koncept

Systém běží **2 strategie PARALELNĚ** pro A/B testing:

### 📐 STRUCTURED Strategy
- Detailní prompt s pravidly
- Examples kdy vstoupit/nevstoupit
- Entry setup guidelines
- Reversal thresholds
- Safe, consistent
- **Prompt: 200+ řádků instrukcí**

### 🤖 MINIMAL Strategy  
- Minimální prompt, jen surová data
- Žádné rules, žádné examples
- AI rozhoduje samostatně
- Kreativnější, adaptivnější
- **Prompt: ~50 řádků pure data**

---

## 🔄 Jak to funguje

### Workflow

```
START
  ↓
[Data Collector]
  ↓
[Analysis] (1x pro obě)
  ↓
[Decision STRUCTURED] → recommendation_structured
  ↓
[Decision MINIMAL] → recommendation_minimal
  ↓
[Paper Trading]
  ├─→ If STRUCTURED = LONG/SHORT → Create trade_structured
  └─→ If MINIMAL = LONG/SHORT → Create trade_minimal
  ↓
END (0-2 trades created)
```

### Možné výsledky:

**Obě NEUTRAL:**
```
STRUCTURED: NEUTRAL
MINIMAL: NEUTRAL
→ 0 trades created
```

**Jedna LONG, jedna NEUTRAL:**
```
STRUCTURED: LONG @ $190
MINIMAL: NEUTRAL
→ 1 trade created (structured)
```

**Obě LONG (agreement):**
```
STRUCTURED: LONG @ $190
MINIMAL: LONG @ $190
→ 2 trades created (same entry, different strategy tags)
```

**Disagreement:**
```
STRUCTURED: LONG @ $190
MINIMAL: SHORT @ $190
→ 2 opposite trades (interesting for comparison!)
```

---

## 📊 Trade Tagging

### Database

Každý trade má pole `strategy`:
```sql
trade_id: SOLUSDT_20251023_143000_structured
strategy: structured

trade_id: SOLUSDT_20251023_143000_minimal
strategy: minimal
```

### Trade ID Format

```
{SYMBOL}_{TIMESTAMP}_{STRATEGY}

Examples:
SOLUSDT_20251023_143000_structured
SOLUSDT_20251023_143000_minimal
```

---

## 📈 Viewing Results

### All Trades
```bash
cd src
python trade_manager.py list

# Output:
📐 Trade ID: SOLUSDT_20251023_143000_structured
  Strategy: STRUCTURED
  Action: LONG
  ...

🤖 Trade ID: SOLUSDT_20251023_143000_minimal
  Strategy: MINIMAL
  Action: LONG
  ...
```

### Filter by Strategy
```bash
# Structured only
python trade_manager.py list --strategy structured

# Minimal only
python trade_manager.py list --strategy minimal
```

### Statistics with Comparison
```bash
python trade_manager.py stats

# Output:
================================================================================
📊 MULTI-STRATEGY TRADING STATISTICS (ALL)
================================================================================

OVERALL:
  Total Trades: 24
  Open: 6 | Closed: 18
  Wins: 13 | Losses: 5
  Win Rate: 72.22%
  Total P&L: $287.50

📐 STRUCTURED STRATEGY (Detailed Prompts):
  Trades: 12
  Closed: 9 (7W / 2L)
  Win Rate: 77.78%
  Total P&L: $156.30
  Avg P&L: 2.85%
  Rating: 🌟

🤖 MINIMAL STRATEGY (AI Independent):
  Trades: 12
  Closed: 9 (6W / 3L)
  Win Rate: 66.67%
  Total P&L: $131.20
  Avg P&L: 2.35%
  Rating: ✅

🆚 STRATEGY COMPARISON:
  Win Rate: STRUCTURED better (+11.1%) 📐
  P&L: STRUCTURED better ($+25.10) 📐
```

### Direct Comparison
```bash
python trade_manager.py compare

# Table format comparison
```

---

## 🎓 Interpreting Results

### Po 30+ closed trades (per strategy):

**Structured vyhrává:**
```
STRUCTURED: 75% win rate, $350 P&L
MINIMAL: 65% win rate, $280 P&L

→ Structured pravidla fungují lépe
→ Keep structured, or refine minimal prompt
```

**Minimal vyhrává:**
```
STRUCTURED: 68% win rate, $290 P&L
MINIMAL: 78% win rate, $450 P&L

→ AI samostatně rozhoduje lépe!
→ Rules omezují performance
→ Consider switching to minimal
```

**Similar performance:**
```
STRUCTURED: 70% win rate, $320 P&L
MINIMAL: 72% win rate, $310 P&L

→ Both work well
→ Different decisions, same results
→ Diversification benefit
```

---

## 💡 Learning Opportunities

### Analyze Disagreements

```bash
# Find where strategies disagreed
grep "STRUCTURED: LONG" logs/trading_bot.log | grep -A1 "MINIMAL: SHORT"
grep "STRUCTURED: NEUTRAL" logs/trading_bot.log | grep -A1 "MINIMAL: LONG"
```

**Questions:**
- Kdy minimal našel opportunity kterou structured missed?
- Kdy structured correctly avoidl risk kterou minimal vzal?
- Které disagreements byly profitable?

### Review Reasoning

```bash
# Compare reasoning
cd results
cat result_SOLUSDT_20251023_143000.json | jq '.recommendation_structured.reasoning'
cat result_SOLUSDT_20251023_143000.json | jq '.recommendation_minimal.reasoning'
```

**Insights:**
- Jak AI uvažuje bez rules?
- Jaké faktory AI prioritizuje?
- Je reasoning logical?

---

## 🔬 A/B Test Protocol

### Week 1-2: Collect Data
```
Let both strategies run
Accumulate 20+ trades each
Don't interfere
```

### Week 3: Analyze
```bash
python trade_manager.py compare

Questions:
- Which has higher win rate?
- Which has better P&L?
- Which has better R/R?
- Consistency?
```

### Week 4: Decision
```
If STRUCTURED clearly better:
→ Disable minimal, use structured

If MINIMAL clearly better:
→ Disable structured, use minimal only

If SIMILAR:
→ Keep both (diversification)
→ Or pick based on preference
```

---

## ⚙️ Configuration

### Enable/Disable Strategies

Currently both run. To disable one, comment out in `trading_bot.py`:

```python
# Disable minimal strategy
# workflow.add_node("decide_minimal", make_decision_minimal)
# workflow.add_edge("decide_structured", "decide_minimal")
# workflow.add_edge("decide_minimal", "execute_trade")

# Direct edge instead:
workflow.add_edge("decide_structured", "execute_trade")
```

---

## 📊 Example Bot Output

### Analysis Complete:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 MULTI-STRATEGY ANALYSIS COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STRUCTURED] LONG (high)
[MINIMAL] LONG (medium)

✅ 2 trade(s) executed

📊 Multi-Strategy Performance:
   OVERALL: 24 trades total
      Win rate: 72.2% | P&L: $287.50
   STRUCTURED: 12 trades | Win: 77.8% | P&L: $156.30
   MINIMAL: 12 trades | Win: 66.7% | P&L: $131.20
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Trade List:
```
📐 Trade ID: SOLUSDT_20251023_143000_structured
  Strategy: STRUCTURED
  Action: LONG @ $190.38
  ...

🤖 Trade ID: SOLUSDT_20251023_143000_minimal
  Strategy: MINIMAL
  Action: LONG @ $190.38
  ...
```

---

## 🎯 Use Cases

### 1. A/B Testing
```
Run both for 30 days
Compare performance
Choose winner
```

### 2. Diversification
```
Keep both strategies
Different decisions = different opportunities
Portfolio effect
```

### 3. Learning
```
See how AI thinks without constraints
Understand what rules help/hurt
Improve prompt engineering
```

### 4. Risk Management
```
If both agree (LONG/LONG):
→ High confidence setup

If disagree (LONG/NEUTRAL):
→ Medium confidence

If opposite (LONG/SHORT):
→ Avoid or reduce size
```

---

## 💰 Performance Tracking

### Commands:
```bash
# Overall stats
python trade_manager.py stats

# Structured only
python trade_manager.py list --strategy structured --status closed

# Minimal only
python trade_manager.py list --strategy minimal --status closed

# Direct comparison
python trade_manager.py compare
```

### Log Analysis:
```bash
cd logs

# Structured signals
grep "STRUCTURED:" trading_bot.log | grep -c "LONG"
grep "STRUCTURED:" trading_bot.log | grep -c "SHORT"
grep "STRUCTURED:" trading_bot.log | grep -c "NEUTRAL"

# Minimal signals
grep "MINIMAL:" trading_bot.log | grep -c "LONG"
grep "MINIMAL:" trading_bot.log | grep -c "SHORT"
grep "MINIMAL:" trading_bot.log | grep -c "NEUTRAL"

# Agreement rate
grep -A1 "STRUCTURED: LONG" trading_bot.log | grep -c "MINIMAL: LONG"
```

---

## 🏆 Benefits

### Multi-Strategy Provides:

✅ **A/B Testing** - Which prompt style works better?  
✅ **Learning** - How does AI think independently?  
✅ **Comparison** - Side-by-side performance  
✅ **Diversification** - Different decisions = more opportunities  
✅ **Confidence** - Agreement = stronger signal  
✅ **Insights** - Understand AI reasoning  

---

## ⚠️ Considerations

### Costs:
- **2x API calls** to DeepSeek (one per strategy)
- **~2x trades** created (if both signal)
- **Slightly slower** analysis (~5s extra)

### Benefits:
- **Data-driven decision** which prompt better
- **No guessing** - let results speak
- **Educational** - see AI capabilities
- **Optimal strategy** selection after testing

**Trade-off: Worth it for finding best approach!**

---

## 🎯 Recommendation

### Run Multi-Strategy For:
- **30+ days** minimum
- **50+ closed trades** per strategy
- **Statistical significance**

### Then:
- Compare results
- Choose winner
- Optionally disable weaker strategy
- Or keep both for diversification

---

**Multi-strategy = scientific approach to finding optimal trading logic! 🔬📊**

**Commands:**
```bash
./bot.sh start                    # Run both strategies
python trade_manager.py stats     # Compare performance
python trade_manager.py compare   # Detailed comparison
```

**Let data decide which approach is better! 📈🤖**

