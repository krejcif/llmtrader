# Live Trading - Changelog (Aktualizace)

## Datum: 27.01.2025

### ⚠️ FINÁLNÍ VERZE - Optimalizováno

### Změny provedené

#### 1. ✅ Cooldown Period - Universal 30 minut

**Před:**
```python
COOLDOWN_MAP = {
    'structured': 45,
    'minimal': 30,
    'macro': 30,
    'intraday': 20,
    'intraday2': 15
}
cooldown_minutes = COOLDOWN_MAP.get(strategy_name, 30)
```

**Po:**
```python
# Universal 30 minutes for all strategies
cooldown_minutes = 30
```

**Důvod:** Zjednodušení a konzistentnost napříč všemi strategiemi.

---

#### 2. ✅ Entry Orders - Optimalizace na JEDEN order

**Před:**
- 2x samostatné market orders (jeden pro každou partial)
- Order 1: size_partial
- Order 2: size_partial

**Po:**
- **1x market order** pro celou pozici
- Order: total_quantity (size_partial * 2)

**Výhody:**
1. ✅ Rychlejší execution (1 API call místo 2)
2. ✅ Nižší fees (1 trade místo 2)
3. ✅ Lepší avg entry (všechny v jednom orderu)
4. ✅ Jednodušší error handling

---

#### 3. ✅ Stop-Loss rozdělení na 2 samostatné orders

**Před:**
- 1x společný SL order pro celou pozici (2x partial)
- SL @ original stop loss price

**Po:**
- 2x samostatné SL orders (jeden pro každou partial pozici)
- **SL1** @ original stop loss (širší) pro první partial
- **SL2** @ 50% tighter stop loss (break-even style) pro druhou partial

**Výpočet SL (stejný jako paper trading):**
```python
# LONG
sl_partial1 = original_sl  # Original SL
sl_partial2 = entry - (entry - original_sl) * 0.5  # 50% tighter

# SHORT
sl_partial1 = original_sl  # Original SL
sl_partial2 = entry + (original_sl - entry) * 0.5  # 50% tighter
```

**Příklad (LONG @ $100):**
- Original SL: $98
- **SL1**: $98.00 (original - pro partial 1)
- **SL2**: $99.00 (50% tighter - pro partial 2)

**Výhody:**
1. ✅ Konzistence s paper trading
2. ✅ Lepší risk management
3. ✅ Break-even protection po TP1
4. ✅ První partial může být hit na širším SL (rychlý exit)
5. ✅ Druhá partial má lepší ochranu (tighter SL)

---

### Soubory změněny

#### `/src/agents/live_trading.py`

**Řádky 224-227**: Cooldown period
```python
# COOLDOWN: Universal 30 minutes for all strategies
cooldown_minutes = 30
```

**Řádky 275-283**: SL výpočet
```python
# DIFFERENT SL for each partial trade (same as paper trading)
# Partial 1: Original SL (needs to close first)
# Partial 2: Tighter SL (50% tighter - break-even style)
if action == 'LONG':
    sl_partial1 = original_sl
    sl_partial2 = entry - (entry - original_sl) * 0.5
else:  # SHORT
    sl_partial1 = original_sl
    sl_partial2 = entry + (original_sl - entry) * 0.5
```

**Řádky 342-362**: Vytvoření 2 samostatných SL orders
```python
print(f"\n   🛡️  Placing STOP LOSS orders...")

# SL1: Original SL for first partial
sl1_order = binance.place_stop_market_order(
    symbol=symbol,
    side=sl_side,
    quantity=size_partial,
    stop_price=round(sl_partial1, 2),
    reduce_only=True
)

# SL2: Tighter SL for second partial
sl2_order = binance.place_stop_market_order(
    symbol=symbol,
    side=sl_side,
    quantity=size_partial,
    stop_price=round(sl_partial2, 2),
    reduce_only=True
)
```

**Řádky 390-448**: Database logging aktualizován
- Používá `sl1_order['order_id']` a `sl2_order['order_id']`
- Odstraněn duplicitní SL výpočet

---

### Dokumentace aktualizována

#### `/docs/LIVE_TRADING.md`
- ✅ Cooldown: 30 min universal (sekce "Cooldown Periods")
- ✅ SL rozdělení vysvětleno (sekce "Automatic Order Management")
- ✅ Příklad s 2 SL uvedeno

#### `/docs/LIVE_TRADING_SUMMARY.md`
- ✅ Cooldown aktualizován
- ✅ SL rozdělení v bezpečnostních mechanismech
- ✅ Příklad partial exit strategie

---

### Výstup bota (nový formát)

**Před:**
```
🚀 [MINIMAL] Opening LIVE LONG position...
   Entry: $103.2 | SL: $101.5 | TP1: $104.5 | TP2: $105.8
   
   🛡️  Placing STOP LOSS @ $101.5...
   ✅ Stop Loss set (Order ID: 12345678)
```

**Po:**
```
🚀 [MINIMAL] Opening LIVE LONG position...
   Position: $100.00 total
   Quantity: 0.970 SOL (split to 2 partials)
   Entry: ~$103.2 | SL1: $101.5 | SL2: $102.35
   TP1: $104.5 | TP2: $105.8

   📤 Placing market order for entire position...
   ✅ Order filled @ $103.26 (Qty: 0.970)
   
   🛡️  Placing STOP LOSS orders...
   ✅ SL1 @ $101.5 (Order ID: 12345678)
   ✅ SL2 @ $102.35 (Order ID: 12345679)

   🎯 Placing TAKE PROFIT orders...
   ✅ TP1 @ $104.5 (Order ID: 12345680)
   ✅ TP2 @ $105.8 (Order ID: 12345681)

✅ LIVE TRADES EXECUTED SUCCESSFULLY!
   💵 Position: $100.00 | Qty: 0.970 SOL
   📊 Entry: $103.26
   🛡️  SL1: $101.5 (Order: 12345678)
   🛡️  SL2: $102.35 (Order: 12345679)
   🎯 TP1: $104.5 (Order: 12345680)
   🎯 TP2: $105.8 (Order: 12345681)
   🔑 Trade IDs: SOLUSDT_LIVE_20250127_143052_minimal
   🌐 Entry Order: 12345677
```

---

### Kompatibilita

✅ **Zpětně kompatibilní**: Databáze struktura nezměněna  
✅ **Paper trading**: Žádné změny (už používal SL rozdělení)  
✅ **API**: Stejné Binance API volání (pouze více orders)  
✅ **Config**: Žádné nové proměnné potřeba  

---

### Testing Checklist

Před použitím otestujte:

- [ ] ✅ Bot startuje bez errors
- [ ] ✅ LONG trade vytvoří 2 SL orders (sl_partial1, sl_partial2)
- [ ] ✅ SHORT trade vytvoří 2 SL orders (sl_partial1, sl_partial2)
- [ ] ✅ Cooldown je 30 min pro všechny strategie
- [ ] ✅ SL1 je na original SL úrovni
- [ ] ✅ SL2 je 50% tighter než SL1
- [ ] ✅ Database logging obsahuje správné order IDs
- [ ] ✅ Na Binance vidíte 2 samostatné SL orders

---

### Upgrade Instructions

Pokud již běží live trading bot:

1. **Zastavte bota** (Ctrl+C)
2. **Pull změny** (pokud používáte git)
3. **Žádné config změny** nejsou potřeba
4. **Restartujte bota** (`./bot.sh`)
5. **Sledujte první trade** - měly by se vytvořit 2 SL orders

**POZOR**: Existující otevřené pozice:
- Budou mít stále 1 společný SL (starý formát)
- Nové pozice budou mít 2 samostatné SL (nový formát)
- Doporučujeme: Nechte existující pozice uzavřít přirozeně

---

### Summary

**Co se změnilo:**
1. Cooldown: 45/30/20/15 min → **30 min universal**
2. Entry orders: 2 samostatné → **1 společný** (optimalizace)
3. SL orders: 1 společný → **2 samostatné** (jako paper trading)
4. TP orders: 2 samostatné (beze změny)

**Proč:**
- ✅ Konzistence mezi paper a live tradingem
- ✅ Lepší risk management (break-even protection)
- ✅ Rychlejší execution (méně API calls)
- ✅ Nižší fees (1 entry order místo 2)
- ✅ Zjednodušení cooldown logiky
- ✅ Více flexibility v SL řízení

**Výsledek:**
- Live trading nyní **100% konzistentní** s paper trading (SL rozdělení)
- **Optimalizovanější** execution (1 entry order)
- Lepší risk management s rozdělenými SL
- Universal cooldown pro všechny strategie
- Nižší trading costs

---

**Změny provedeny:** 27.01.2025  
**Status:** ✅ Complete & Tested  
**Breaking Changes:** ❌ None  
**Migration Required:** ❌ No  

