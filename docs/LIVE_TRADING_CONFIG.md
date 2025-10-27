# Live Trading Configuration Guide

## Konfigurace .env souboru

Pro live trading musíte nastavit následující proměnné ve vašem `.env` souboru:

```bash
# =============================================================================
# BINANCE API (REQUIRED for live trading)
# =============================================================================
BINANCE_API_KEY="your_binance_api_key_here"
BINANCE_API_SECRET="your_binance_api_secret_here"

# =============================================================================
# LIVE TRADING (Optional - default OFF)
# =============================================================================
# Enable/disable live trading
ENABLE_LIVE_TRADING=false  # Set to "true" to enable

# Position size per trade in USD
LIVE_POSITION_SIZE=100     # Start with $50-100

# =============================================================================
# OTHER (Already configured)
# =============================================================================
DEEPSEEK_API_KEY="your_deepseek_key"  # Required for AI analysis
SYMBOL="SOLUSDT"                       # Trading symbol
TRADING_FEE_RATE=0.0005                # Binance taker fee (0.05%)
```

## Jak získat Binance API klíče

### Krok 1: Vytvoření API klíče

1. Přihlaste se na [Binance.com](https://www.binance.com)
2. Jděte do **Account → API Management**
3. Klikněte na **Create API**
4. Zadejte název (např. "Trading Bot")
5. Dokončete 2FA ověření

### Krok 2: Nastavení oprávnění

**KRITICKÉ - Správně nastavte oprávnění:**

✅ **POVOLIT**:
- ✅ Enable Reading (číst data)
- ✅ Enable Futures (futures trading)

❌ **NEPOVOLOVAT** (bezpečnost):
- ❌ Enable Withdrawals (výběry)
- ❌ Enable Internal Transfer (přesuny)
- ❌ Enable Margin (margin trading)
- ❌ Enable Spot & Margin Trading (spot trading)

### Krok 3: IP Whitelist (doporučeno)

Pro extra bezpečnost:

1. V API Management → Edit restrictions
2. Přidejte IP adresu vašeho serveru
3. Pouze z této IP bude možné používat API klíč

**Jak zjistit vaši IP:**
```bash
curl ifconfig.me
```

### Krok 4: Uložení klíčů

1. **API Key**: Zkopírujte do `.env` → `BINANCE_API_KEY`
2. **Secret Key**: Zkopírujte do `.env` → `BINANCE_API_SECRET`
   - ⚠️ Secret se zobrazí pouze jednou!
   - Uložte si ho bezpečně
   - Pokud ho ztratíte, musíte vytvořit nový API klíč

### Krok 5: Uložte klíče do .env

```bash
# Editujte .env soubor
nano /home/flow/langtest/.env

# Přidejte nebo upravte:
BINANCE_API_KEY="zde_vas_api_key"
BINANCE_API_SECRET="zde_vas_secret_key"
```

## Test konfigurace

Před spuštěním bota ověřte, že API klíče fungují:

```bash
cd /home/flow/langtest

# Test 1: Balance check
python3 << 'EOF'
from src.utils.binance_client import BinanceClient

try:
    client = BinanceClient()
    balance = client.get_account_balance()
    
    print("✅ API Connection successful!")
    print(f"Total Balance: ${balance['total_balance']:.2f} USDT")
    print(f"Available: ${balance['available_balance']:.2f} USDT")
    print(f"Unrealized P&L: ${balance['unrealized_pnl']:.2f}")
except Exception as e:
    print(f"❌ API Error: {e}")
    print("\nCheck:")
    print("1. API keys are correct in .env")
    print("2. 'Enable Futures' is enabled")
    print("3. IP whitelist (if configured)")
EOF
```

**Očekávaný výstup:**
```
✅ API Connection successful!
Total Balance: $1000.00 USDT
Available: $1000.00 USDT
Unrealized P&L: $0.00
```

## Aktivace Live Trading

### Krok 1: Ujistěte se, že máte dostatečný balance

```bash
# Minimum balance recommendations:
# - For $100 position size: Min $5,000 balance (2% risk rule)
# - For $50 position size: Min $2,500 balance
# - For $10 position size: Min $500 balance
```

### Krok 2: Nastavte position size

V `.env`:
```bash
LIVE_POSITION_SIZE=100  # Upravte dle vašeho kapitálu
```

**Risk Management Rule:**
Position size by měla být max **1-2% vašeho celkového kapitálu**.

Příklady:
- Balance $500 → Position $10 (2%)
- Balance $2,500 → Position $50 (2%)
- Balance $5,000 → Position $100 (2%)
- Balance $10,000 → Position $200 (2%)

### Krok 3: Zapněte live trading

V `.env`:
```bash
ENABLE_LIVE_TRADING=true
```

### Krok 4: Restartujte bota

```bash
# Zastavte bota (pokud běží)
# Ctrl+C

# Spusťte znovu
./bot.sh
```

Bot vypíše:
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

## Monitoring Live Trades

### V bot konzoli

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
```

### V logs

```bash
# Real-time log monitoring
tail -f /home/flow/langtest/logs/trading_bot.log

# Filter only live trades
tail -f logs/trading_bot.log | grep "LIVE"
```

### Na Binance

Zkontrolujte na Binance web/app:

1. **Futures → Positions**: Vidíte otevřené pozice
2. **Futures → Open Orders**: Vidíte aktivní SL/TP orders
3. **Futures → Order History**: Historie všech vyplněných orders
4. **Futures → Transaction History**: P&L historie

### V databázi

```bash
cd /home/flow/langtest

# Show all trades including live
python src/utils/database.py stats

# SQL query for live trades only
sqlite3 trading_data.db << 'EOF'
SELECT 
    trade_id,
    symbol,
    strategy,
    action,
    entry_price,
    stop_loss,
    take_profit,
    status
FROM trades
WHERE analysis_data LIKE '%"live_trade": true%'
ORDER BY entry_time DESC
LIMIT 10;
EOF
```

## Vypnutí Live Trading

### Dočasné vypnutí (paper trading pokračuje)

V `.env`:
```bash
ENABLE_LIVE_TRADING=false
```

Restartujte bota.

### Uzavření všech otevřených pozic

```bash
# Python script to close all positions
python3 << 'EOF'
from src.utils.binance_client import BinanceClient

client = BinanceClient()
positions = client.get_open_positions()

if not positions:
    print("No open positions")
else:
    for pos in positions:
        symbol = pos['symbol']
        side = 'SELL' if pos['side'] == 'LONG' else 'BUY'
        qty = abs(pos['position_amt'])
        
        print(f"Closing {pos['side']} {qty} {symbol}")
        
        try:
            order = client.place_market_order(symbol, side, qty, reduce_only=True)
            print(f"✅ Closed @ ${order['avg_price']}")
        except Exception as e:
            print(f"❌ Error: {e}")
EOF
```

### Zrušení všech open orders

```bash
python3 << 'EOF'
from src.utils.binance_client import BinanceClient

client = BinanceClient()

# Get all symbols with open orders
symbols = ['SOLUSDT', 'BTCUSDT', 'ETHUSDT']  # Add your symbols

for symbol in symbols:
    try:
        client.cancel_all_orders(symbol)
        print(f"✅ Cancelled all orders for {symbol}")
    except Exception as e:
        print(f"❌ {symbol}: {e}")
EOF
```

## Troubleshooting

### Error: "No API credentials"

**Problém**: Bot nemůže najít API klíče.

**Řešení**:
```bash
# Check if .env exists
ls -la /home/flow/langtest/.env

# Check if variables are set
grep "BINANCE_API" /home/flow/langtest/.env

# Make sure no extra spaces or quotes
# Correct: BINANCE_API_KEY="abc123"
# Wrong: BINANCE_API_KEY = "abc123" (spaces)
# Wrong: BINANCE_API_KEY=abc123 (no quotes)
```

### Error: "Insufficient balance"

**Problém**: Nedostatečný zůstatek.

**Řešení**:
1. Vložte více prostředků na Binance Futures
2. Nebo snižte `LIVE_POSITION_SIZE` v `.env`

### Error: "API permissions"

**Problém**: API klíč nemá správná oprávnění.

**Řešení**:
1. Jděte na Binance → API Management
2. Edit your API key
3. Ujistěte se, že "Enable Futures" je zaškrtnuté
4. Uložte změny
5. Možná bude nutné vytvořit nový API klíč

### Error: "IP address not whitelisted"

**Problém**: Vaše IP není na whitelistu.

**Řešení**:
1. Zjistěte vaši IP: `curl ifconfig.me`
2. Jděte na Binance → API Management
3. Edit restrictions → Add IP
4. Nebo vypněte IP whitelist (méně bezpečné)

## Bezpečnostní checklist

Před zapnutím live trading:

- [ ] ✅ API key má pouze "Enable Reading" a "Enable Futures"
- [ ] ✅ API key NEMÁ "Enable Withdrawals"
- [ ] ✅ Použil jsem IP whitelist (nebo jsem si vědom rizika)
- [ ] ✅ LIVE_POSITION_SIZE je max 1-2% mého kapitálu
- [ ] ✅ Testoval jsem strategie v paper mode min 2 týdny
- [ ] ✅ Mám dostatečný balance (min 50x position size)
- [ ] ✅ Rozumím rizikům tradingu
- [ ] ✅ Používám pouze peníze, které si mohu dovolit ztratit
- [ ] ✅ Přečetl jsem docs/LIVE_TRADING.md
- [ ] ✅ Vím, jak bota zastavit (Ctrl+C)
- [ ] ✅ Vím, jak uzavřít pozice manuálně

## Support

Pokud máte problémy:

1. Přečtěte si `/home/flow/langtest/docs/LIVE_TRADING.md`
2. Zkontrolujte logs: `tail -f logs/trading_bot.log`
3. Test API: `python -c "from utils.binance_client import BinanceClient; print(BinanceClient().get_account_balance())"`
4. Přečtěte error message pozorně - často obsahuje řešení

---

**Upozornění**: Live trading je na vlastní riziko. Autor systému neručí za žádné ztráty.

