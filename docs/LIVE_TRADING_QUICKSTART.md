# Live Trading - Quick Start Guide

## 🚀 Rychlý start (5 minut)

### 1. Získej Binance API klíče

1. Jdi na https://www.binance.com/en/my/settings/api-management
2. Vytvoř nový API klíč
3. ✅ Zapni "Enable Futures"
4. ❌ VYPNI "Enable Withdrawals" (bezpečnost!)
5. Zkopíruj API Key a Secret Key

### 2. Nastav .env

```bash
cd /home/flow/langtest
nano .env
```

Přidej:
```bash
BINANCE_API_KEY="tvuj_api_key"
BINANCE_API_SECRET="tvuj_secret_key"
ENABLE_LIVE_TRADING=true
LIVE_POSITION_SIZE=50  # Start small!
```

### 3. Test připojení

```bash
python3 << 'EOF'
from src.utils.binance_client import BinanceClient
bc = BinanceClient()
balance = bc.get_account_balance()
print(f"✅ Balance: ${balance['total_balance']:.2f} USDT")
EOF
```

### 4. Spusť bota

```bash
./bot.sh
```

Bot vypíše:
```
🤖 DYNAMIC AUTONOMOUS TRADING BOT STARTED
...
  4. Auto-execute LIVE trades (REAL MONEY - $50 per trade) ⚠️
```

### 5. Sleduj trades

```bash
# Logs
tail -f logs/trading_bot.log | grep LIVE

# Binance web
# Futures → Positions → Open
```

## ⚠️ Bezpečnostní checklist

Před zapnutím live trading:

- [ ] ✅ Testoval jsem paper trading min 2 týdny
- [ ] ✅ LIVE_POSITION_SIZE je max 2% mého kapitálu
- [ ] ✅ API klíč NEMÁ "Enable Withdrawals"
- [ ] ✅ Mám dostatečný balance (min 50x position size)
- [ ] ✅ Rozumím, že můžu ztratit peníze

## 📊 Monitoring

### Console
```
💰 Live Trading (ENABLED)
🚀 [MINIMAL] Opening LIVE LONG...
   ✅ Order filled @ $103.25
   ✅ Stop Loss set
   ✅ Take Profit set
✅ LIVE TRADES EXECUTED!
```

### Binance
- Positions: https://www.binance.com/en/futures/SOLUSDT
- Orders: Futures → Open Orders

### Database
```bash
python src/utils/database.py stats
```

## 🛑 Vypnutí

```bash
# V .env
ENABLE_LIVE_TRADING=false

# Restart bota
./bot.sh
```

## 📖 Dokumentace

- **Kompletní průvodce**: `docs/LIVE_TRADING.md`
- **Konfigurace**: `docs/LIVE_TRADING_CONFIG.md`
- **Souhrn**: `docs/LIVE_TRADING_SUMMARY.md`

## 💡 Tipy

1. **Start small**: Začni s $10-50 per trade
2. **Watch first week**: První týden kontroluj denně
3. **Risk 1-2%**: Position size = max 2% kapitálu
4. **Monitor stats**: Pravidelně check win rate
5. **Disable bad strategies**: V `strategy_config.py`

## ⚠️ Varování

**TRADING JE RIZIKOVÉ!**
- Můžeš ztratit všechny peníze
- Většina traderů ztrácí
- Používej pouze peníze, které si můžeš dovolit ztratit
- Live trading je na vlastní riziko

## 🆘 Problémy?

### "No API credentials"
→ Check `.env` má `BINANCE_API_KEY` a `BINANCE_API_SECRET`

### "Insufficient balance"
→ Vlož víc na Binance nebo sniž `LIVE_POSITION_SIZE`

### "API permissions"
→ Na Binance API zapni "Enable Futures"

### "Position already open"
→ Počkej, až se uzavře (bezpečnostní funkce)

## 📞 Support

- README: `/home/flow/langtest/README.md`
- Docs: `/home/flow/langtest/docs/LIVE_TRADING.md`
- Config: `/home/flow/langtest/docs/LIVE_TRADING_CONFIG.md`

---

**Ready to trade? Good luck! 🚀💰**

*(But remember: Trading is risky!)*

