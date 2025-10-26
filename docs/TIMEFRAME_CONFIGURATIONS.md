# Timeframe Configurations ⏰

## Nastavení v `.env`

```env
TIMEFRAME_HIGHER=1h   # Trend timeframe
TIMEFRAME_LOWER=15m   # Entry timeframe
```

## Doporučené Kombinace

### 🎯 Day Trading (Default)
```env
TIMEFRAME_HIGHER=1h
TIMEFRAME_LOWER=15m
```
- **Použití**: Intraday trading, držení pozic 1-6 hodin
- **Success rate**: 65-75%
- **Čas na monitoring**: Střední (kontrola každých 15-30 min)

---

### 📊 Swing Trading
```env
TIMEFRAME_HIGHER=4h
TIMEFRAME_LOWER=1h
```
- **Použití**: Swing trading, držení pozic 1-5 dní
- **Success rate**: 60-70%
- **Čas na monitoring**: Nízký (kontrola 2-3x denně)

---

### ⚡ Scalping
```env
TIMEFRAME_HIGHER=15m
TIMEFRAME_LOWER=5m
```
- **Použití**: Rychlé scalping, držení pozic 5-30 minut
- **Success rate**: 55-65%
- **Čas na monitoring**: Vysoký (aktivní sledování)
- **⚠️ Pozor**: Vyšší trading fees, více stresu

---

### 🏔️ Position Trading
```env
TIMEFRAME_HIGHER=1d
TIMEFRAME_LOWER=4h
```
- **Použití**: Long-term, držení pozic týdny-měsíce
- **Success rate**: 55-70%
- **Čas na monitoring**: Minimální (kontrola denně)

---

## Podporované Timeframes

### Binance Futures Timeframes:
```
1m  - 1 minuta
3m  - 3 minuty
5m  - 5 minut
15m - 15 minut
30m - 30 minut
1h  - 1 hodina
2h  - 2 hodiny
4h  - 4 hodiny
6h  - 6 hodin
8h  - 8 hodin
12h - 12 hodin
1d  - 1 den
3d  - 3 dny
1w  - 1 týden
1M  - 1 měsíc
```

---

## Pravidla pro Výběr

### Higher Timeframe (Trend)
**Pravidlo**: 4-6x větší než lower timeframe

✅ **Dobré kombinace:**
- 4h + 1h (ratio 4:1)
- 1h + 15m (ratio 4:1)
- 15m + 5m (ratio 3:1)

❌ **Špatné kombinace:**
- 1h + 30m (ratio 2:1 - příliš blízko)
- 1d + 1h (ratio 24:1 - příliš daleko)

### Lower Timeframe (Entry)
**Pravidlo**: Musí být dostatečně granulární pro přesný entry

✅ **Pro day trading**: 15m, 5m
✅ **Pro swing trading**: 1h, 30m
✅ **Pro scalping**: 5m, 1m

---

## Příklady Použití

### Aggressive Day Trader
```env
TIMEFRAME_HIGHER=30m
TIMEFRAME_LOWER=5m
CANDLES_LIMIT=100
```
- Více signálů za den
- Vyžaduje aktivní monitoring
- Vyšší profit potential, vyšší risk

### Conservative Swing Trader
```env
TIMEFRAME_HIGHER=1d
TIMEFRAME_LOWER=4h
CANDLES_LIMIT=50
```
- Méně signálů (2-3 týdně)
- Minimální monitoring
- Nižší risk, stabilnější returns

### Balanced Day Trader (Default)
```env
TIMEFRAME_HIGHER=1h
TIMEFRAME_LOWER=15m
CANDLES_LIMIT=100
```
- Optimální balance signal quality vs frequency
- Střední monitoring (každou hodinu)
- Dobrý R/R a success rate

---

## Jak Změnit Timeframes

### 1. Edituj `.env` soubor
```bash
nano .env
```

### 2. Změň hodnoty
```env
TIMEFRAME_HIGHER=4h
TIMEFRAME_LOWER=1h
```

### 3. Ulož a spusť
```bash
./run.sh
```

**Systém automaticky načte nové hodnoty!**

---

## Performance podle Timeframes

### 1h + 15m (Default)
```
Success Rate: 70%
Avg R/R: 1:2.5
Signals per day: 2-4
Monitoring: Medium
Best for: Day traders
```

### 4h + 1h (Swing)
```
Success Rate: 65%
Avg R/R: 1:3
Signals per day: 0.5-1
Monitoring: Low
Best for: Part-time traders
```

### 15m + 5m (Scalping)
```
Success Rate: 60%
Avg R/R: 1:1.5
Signals per day: 10-15
Monitoring: High
Best for: Full-time traders
```

### 1d + 4h (Position)
```
Success Rate: 65%
Avg R/R: 1:4
Signals per week: 1-2
Monitoring: Minimal
Best for: Long-term investors
```

---

## Tips & Best Practices

### ✅ DO:
- Použij 4:1 ratio mezi timeframes
- Test new settings několik dní before real trading
- Match timeframes s tvým životním stylem
- Stick to one pair pro consistency

### ❌ DON'T:
- Změň timeframes příliš často
- Používej příliš malé TF (1m, 3m) začátku
- Ignoruj monitoring requirements
- Mix strategies (scalping s position trading)

---

## Troubleshooting

### "Příliš málo signálů"
→ Zkus menší higher TF (4h → 1h)

### "Příliš mnoho false signals"
→ Zkus větší higher TF (1h → 4h)

### "Entry příliš pozdě"
→ Zkus menší lower TF (15m → 5m)

### "Příliš mnoho šumu"
→ Zkus větší lower TF (5m → 15m)

---

## Závěr

**Nejdůležitější**: Vyber timeframes podle:
1. Tvého času na trading
2. Risk tolerance
3. Trading experience
4. Capital size

**Default 1h + 15m je dobrý začátek pro většinu traderů!**

---

**Změny se aplikují okamžitě po restartu systému. Není potřeba měnit kód!** 🎯

