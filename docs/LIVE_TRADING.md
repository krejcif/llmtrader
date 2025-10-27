# Live Trading Guide

## Přehled

Live trading agent (`agents/live_trading.py`) umožňuje automatické provádění **skutečných obchodů** na Binance Futures paralelně s paper tradingem.

## ⚠️ Varování

**POZOR: Live trading provádí skutečné obchody s reálnými penězi!**

- Používejte pouze s penězi, které si můžete dovolit ztratit
- Důrazně doporučujeme začít s malými částkami ($10-$100 za trade)
- Testujte strategii nejdříve v paper trading režimu (několik týdnů)
- Nikdy nepoužívejte všechny své prostředky na jeden trade
- Live trading je ve výchozím stavu **VYPNUTÝ** pro bezpečnost

## Klíčové funkce

### Bezpečnostní mechanismy

1. **API Credentials Check**: Ověří, že máte platné API klíče
2. **Balance Check**: Zkontroluje dostupný zůstatek před obchodem
3. **Position Conflict Detection**: Detekuje otevřené pozice před novým obchodem
4. **Cooldown Periods**: Zabraňuje příliš častému obchodování (15-45 min dle strategie)
5. **Automatic Stop-Loss**: Automaticky nastaví SL objednávky na Binance
6. **Automatic Take-Profit**: Nastaví TP objednávky (2 partial exits)
7. **Position Sizing**: Konfigurovatelná velikost pozice (default: $100)
8. **Database Logging**: Všechny live trades se logují do databáze pro tracking

### Rozdíly oproti Paper Trading

| Feature | Paper Trading | Live Trading |
|---------|--------------|--------------|
| Execution | Simulované | Skutečné na Binance |
| Position Size | $10,000 | $100 (konfigurovatelné) |
| Order Fills | Okamžité @ TP/SL | Skutečné market orders |
| Slippage | Žádný | Reálný (malý na likvidních trzích) |
| Fees | Zahrnuté v kalkulaci | Skutečné poplatky Binance |
| SL/TP | Monitorováno botem | Skutečné Binance orders |
| Risk | Žádné | Reálné riziko ztráty |

## Konfigurace

### 1. API klíče (povinné)

V `.env` souboru nastavte:

```bash
# Binance API credentials (REQUIRED for live trading)
BINANCE_API_KEY="your_api_key_here"
BINANCE_API_SECRET="your_api_secret_here"
```

**Jak získat API klíče:**

1. Přihlaste se na [Binance](https://www.binance.com)
2. Jděte do Account → API Management
3. Vytvořte nový API klíč
4. **DŮLEŽITÉ**: Při vytváření API klíče:
   - ✅ Povolte "Enable Futures" (pro futures trading)
   - ✅ Povolte "Enable Reading" (pro načítání dat)
   - ❌ NEPOVOLUJTE "Enable Withdrawals" (bezpečnost!)
   - ❌ NEPOVOLUJTE "Enable Internal Transfer"
5. Zapište si API Key a Secret Key (secret se zobrazí pouze jednou!)
6. **BEZPEČNOST**: IP Whitelist - přidejte IP adresu vašeho serveru

### 2. Aktivace Live Trading

V `.env` souboru:

```bash
# Live Trading Configuration
ENABLE_LIVE_TRADING=true              # Zapne live trading
LIVE_POSITION_SIZE=100                # Velikost pozice v USD (default: $100)
```

**Doporučené position sizes:**

- **Začátečníci**: $10-50 per trade
- **Pokročilí**: $100-500 per trade
- **Zkušení**: $500+ per trade (pouze pokud máte dostatečný kapitál)

**Pravidlo:** Position size by měla být max 1-2% vašeho celkového kapitálu!

### 3. Trading Fee Rate

```bash
TRADING_FEE_RATE=0.0005  # 0.05% (Binance Futures taker fee)
```

Binance Futures fees:
- **Maker**: 0.02% (0.0002) - pokud přidáváte likviditu (limit orders)
- **Taker**: 0.05% (0.0005) - pokud odebíráte likviditu (market orders)

Live trading používá **market orders** (okamžité vykonání), proto platíte taker fee.

## Jak to funguje

### 1. Trade Execution Flow

```
Recommendation (LONG/SHORT)
    ↓
Check API Credentials ✓
    ↓
Check Account Balance ✓
    ↓
Check Existing Positions ✓
    ↓
Check Cooldown Period ✓
    ↓
Calculate Position Size
    ↓
Place 2x Market Orders (partial positions)
    ↓
Place Stop-Loss Order (Binance)
    ↓
Place Take-Profit Orders (2 partials)
    ↓
Log to Database ✓
    ↓
SUCCESS! 🎉
```

### 2. Partial Exit Strategy

Live trading používá stejnou **partial exit strategii** jako paper trading:

- **Trade 1/2**: 50% pozice → TP1 @ 50% distance (rychlý profit)
- **Trade 2/2**: 50% pozice → TP2 @ 100% distance (maximální profit)

**Příklad:**
- Position size: $100
- Partial 1: $50 → TP @ $120 (quick profit) + SL @ $95 (original)
- Partial 2: $50 → TP @ $140 (full profit) + SL @ $97.50 (50% tighter)

### 3. Automatic Order Management

Po otevření pozice bot automaticky:

1. **Stop-Loss 1**: STOP_MARKET @ original SL pro první partial (širší)
2. **Stop-Loss 2**: STOP_MARKET @ 50% tighter SL pro druhou partial (break-even style)
3. **Take-Profit 1**: TAKE_PROFIT_MARKET @ 50% distance
4. **Take-Profit 2**: TAKE_PROFIT_MARKET @ 100% distance

Tyto objednávky běží **na Binance serveru** a jsou vykonány automaticky, i když bot spadne!

**SL rozdělení** (stejné jako paper trading):
- **Partial 1**: Original SL - rychlý exit při problémech
- **Partial 2**: 50% tighter SL - break-even protection

### 4. Position Monitoring

Bot **nemusí** manuálně monitorovat SL/TP, protože:
- SL/TP jsou nastaveny jako skutečné Binance orders
- Binance server je vykoná automaticky při dosažení ceny
- Bot pouze loguje a sleduje otevřené pozice

## Spuštění Live Trading

### Před spuštěním

**DŮLEŽITÁ KONTROLA:**

1. ✅ API klíče správně nastaveny v `.env`
2. ✅ ENABLE_LIVE_TRADING=true v `.env`
3. ✅ LIVE_POSITION_SIZE nastavena na bezpečnou hodnotu
4. ✅ Máte dostatečný balance na Binance Futures účtu
5. ✅ Testovali jste strategii v paper trading (min 2 týdny)
6. ✅ Znáte risk management (max 1-2% kapitálu per trade)

### Spuštění botu

```bash
cd /home/flow/langtest
./bot.sh
```

Bot vypíše na začátku:

```
🤖 DYNAMIC AUTONOMOUS TRADING BOT STARTED
...
🔄 Bot will:
  1. Run strategies at exact UTC time marks
  2. Monitor open trades every 60 seconds
  3. Auto-execute PAPER trades (always)
  4. Auto-execute LIVE trades (REAL MONEY - $100 per trade) ⚠️
  5. Auto-close trades when SL/TP hit (via Binance orders)
```

### Pozorování live trades

Bot bude vypisovat:

```
💰 Live Trading (ENABLED - Real Money!):
   Position size: $100.00 per trade

🚀 [MINIMAL] Opening LIVE LONG position...
   Position: 2x $50.00 = $100.00 total
   Quantity: 0.485 SOL per partial
   Entry: $103.2 | SL: $101.5 | TP1: $104.5 | TP2: $105.8

   📤 Placing order 1/2 (Partial TP)...
   ✅ Order 1 filled @ $103.25

   📤 Placing order 2/2 (Full TP)...
   ✅ Order 2 filled @ $103.28

   🛡️  Placing STOP LOSS @ $101.5...
   ✅ Stop Loss set (Order ID: 12345678)

   🎯 Placing TAKE PROFIT orders...
   ✅ TP1 @ $104.5 (Order ID: 12345679)
   ✅ TP2 @ $105.8 (Order ID: 12345680)

✅ [MINIMAL] LIVE TRADES EXECUTED SUCCESSFULLY!
   💵 Position: $100.00 | Qty: 0.970 SOL
   📊 Entry: $103.26 | SL: $101.5 | TP1: $104.5 | TP2: $105.8
   🌐 Binance Orders: 12345677, 12345678
```

## Paralelní provoz: Paper vs Live

Bot může běžet **současně** v obou režimech:

### Paper Trading
- **Vždy aktivní** (nelze vypnout)
- Velikost pozice: $10,000 (simulace velké pozice)
- Účel: Testování strategií bez rizika
- Výkon: Win rate, P&L, statistiky

### Live Trading
- **Volitelně aktivní** (ENABLE_LIVE_TRADING=true)
- Velikost pozice: $100 (konfigurovatelné)
- Účel: Skutečné obchodování s reálnými penězi
- Výkon: Skutečný profit/loss na Binance účtu

**Benefit**: Můžete porovnat výkonnost paperu vs live a identifikovat slippage/fees impact.

## Monitoring & Statistics

### Database Tracking

Všechny live trades se logují do databáze s označením:

```python
"analysis_data": {
    "live_trade": True,
    "binance_order_id": 12345677,
    "sl_order_id": 12345678,
    "tp_order_id": 12345679
}
```

### Viewing Trades

```bash
# Zobrazit všechny trades (paper + live)
python src/utils/database.py stats

# Filtrace live trades v databázi
sqlite3 trading_data.db
SELECT * FROM trades WHERE analysis_data LIKE '%"live_trade": true%';
```

### Binance Web Interface

Můžete také sledovat pozice přímo na Binance:

1. Futures → Positions (otevřené pozice)
2. Futures → Orders (aktivní SL/TP orders)
3. Futures → Order History (vyplněné objednávky)
4. Futures → Transaction History (P&L historie)

## Risk Management

### Position Sizing

**Zlaté pravidlo**: Nikdy neriskujte více než 1-2% kapitálu per trade!

```
Kapitál: $10,000
Max risk per trade: 1% = $100
Position size: $100-200 (dle R:R ratio)
```

### Stop-Loss Distance

Bot automaticky vypočítá SL based on ATR:

```
SL Distance = ATR * 1.5  (typicky 2-4% z entry)
```

Pokud vám to připadá moc široké nebo úzké, upravte risk management v decision funkcích.

### Cooldown Periods

Po uzavření trade nelze znovu vstoupit po dobu:

- **Všechny strategie**: 30 min (universal cooldown)

## Troubleshooting

### "No API credentials"

**Problém**: Bot nemůže provádět live trades.

**Řešení**:
1. Zkontrolujte `.env` soubor
2. Ujistěte se, že máte `BINANCE_API_KEY` a `BINANCE_API_SECRET`
3. Restartujte bota

### "Insufficient balance"

**Problém**: Nedostatečný zůstatek na účtu.

**Řešení**:
1. Zkontrolujte balance: `python -c "from utils.binance_client import BinanceClient; print(BinanceClient().get_account_balance())"`
2. Vložte více prostředků na Binance Futures
3. Nebo snižte `LIVE_POSITION_SIZE` v `.env`

### "Error placing order"

**Možné příčiny**:
- **Precision error**: Quantity má moc decimals (zkontrolujte symbol info)
- **Min notional**: Position je příliš malá (min ~$10 na Binance)
- **API permissions**: API klíč nemá povolené Futures trading
- **Rate limit**: Příliš mnoho requestů (bot čeká cooldown)

**Řešení**:
1. Zkontrolujte API permissions (Enable Futures)
2. Zvyšte LIVE_POSITION_SIZE (min $20-50)
3. Počkejte cooldown period

### "Position already open"

**Problém**: Bot neotevře nový trade, protože už máte otevřenou pozici.

**Důvod**: Bezpečnostní funkce - zabraňuje double-up pozicím.

**Řešení**: 
- Počkejte, až se pozice uzavře (SL/TP hit)
- Nebo manuálně zavřete pozici na Binance, pokud chcete force exit

### "Cooldown period"

**Problém**: Bot čeká X minut před dalším trade.

**Důvod**: Risk management - zabraňuje příliš častému obchodování.

**Řešení**: Počkejte cooldown period. Je to zamýšlené chování!

## Best Practices

1. **Start Small**: Začněte s $10-50 per trade
2. **Test First**: Minimálně 2 týdny paper trading před live
3. **Monitor Closely**: První týden kontrolujte bota denně
4. **Set Alerts**: Nastavte notifikace pro large losses (TODO: implement)
5. **Review Stats**: Pravidelně kontrolujte win rate a P&L
6. **Adjust Strategies**: Vypněte neúspěšné strategie v `strategy_config.py`
7. **Keep Logs**: Archivujte log soubory pro analýzu
8. **Use IP Whitelist**: Na Binance API klíči povolte pouze vaši IP

## Vypnutí Live Trading

Pokud chcete vypnout live trading:

```bash
# V .env souboru
ENABLE_LIVE_TRADING=false
```

A restartujte bota. Paper trading bude nadále běžet.

## FAQ

**Q: Můžu provozovat live a paper trading současně?**  
A: Ano! To je zamýšlené použití. Paper běží vždy, live je volitelný.

**Q: Co když bot spadne během otevřené pozice?**  
A: Bezpečné! SL/TP jsou nastaveny jako Binance orders, takže fungují i bez bota.

**Q: Můžu manuálně ovládat pozice na Binance?**  
A: Ano, ale může to zmást bot tracking. Doporučujeme nechat bota samotného.

**Q: Kolik můžu vydělat?**  
A: Závisí na strategii, market conditions a risk management. **Žádné záruky!**

**Q: Můžu ztratit všechny peníze?**  
A: Ano. Trading je rizikové. Používejte pouze peníze, které si můžete dovolit ztratit.

**Q: Jak často bot obchoduje?**  
A: Závisí na strategii a market podmínkách. Typicky 2-10 trades denně (všechny strategie dohromady).

## Další kroky

1. **Notifications**: Přidat Discord/Telegram notifikace pro trade alerts
2. **Portfolio Tracking**: Sledování celkového portfolio performance
3. **Dynamic Position Sizing**: Upravit velikost pozice dle account size
4. **Advanced Orders**: Trailing stop, limit entries, etc.
5. **Multi-Symbol**: Live trading pro více symbolů současně

---

**Poslední upozornění**: Live trading je **na vlastní riziko**. Autor systému neručí za žádné ztráty. Trading je rizikové a většina traderů ztrácí peníze. Investujte zodpovědně!

