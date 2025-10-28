# 📡 Live Trading Dashboard - Binance Futures

## Overview

Live Trading Dashboard poskytuje real-time přehled tvého Binance Futures účtu přímo v browseru.

## ✨ Features

### 📊 Account Summary
- **Total Wallet Balance** - Celková hodnota účtu
- **Unrealized P&L** - Nerealizovaný zisk/ztráta z otevřených pozic
- **Available Balance** - Dostupný zůstatek pro nové pozice
- **Margin Balance** - Celkový margin balance

### 📈 Active Positions
- Real-time přehled všech otevřených pozic
- Symbol, Side (LONG/SHORT), Size, Entry/Mark Price
- Live Unrealized P&L s barevným rozlišením
- Leverage, Margin Type, Liquidation Price

### 📝 Open Orders
- Všechny aktivní příkazy (pending orders)
- Side (BUY/SELL), Type, Price, Quantity
- Status a čas vytvoření

### 💎 Assets
- Přehled všech aktiv s nenulovou hodnotou
- Wallet Balance, Unrealized Profit
- Margin Balance, Available Balance

## 🔧 Nastavení

### 1. Získání Binance API Klíčů

#### Pro TESTNET (Demo účet - doporučeno pro začátek):
1. Jdi na: https://testnet.binancefuture.com/
2. Přihlas se pomocí GitHub nebo email
3. Přejdi na API Management
4. Vytvoř nový API klíč
5. Zkopíruj **API Key** a **Secret Key**

#### Pro REAL účet (skutečné peníze):
1. Jdi na: https://www.binance.com/en/my/settings/api-management
2. Vytvoř nový API klíč (pojmenuj např. "Trading Bot")
3. **DŮLEŽITÉ**: Zapni oprávnění **"Enable Futures"**
4. **DOPORUČENO**: Nastav IP whitelist (pouze tvá IP adresa)
5. Zkopíruj **API Key** a **Secret Key**

### 2. Konfigurace `.env` souboru

Uprav `/home/flow/langtest/.env`:

```bash
# Binance Futures API
BINANCE_API_KEY=tvůj_api_key_zde
BINANCE_API_SECRET=tvůj_api_secret_zde

# Demo Mode
# true = Testnet (fake money, safe for testing)
# false = Real account (real money, be careful!)
BINANCE_DEMO=true
```

### 3. Restart Dashboardu

```bash
cd /home/flow/langtest
./start_dashboard.sh
```

### 4. Otevři v browseru

```
http://localhost:5000/live
```

## 🔐 Bezpečnost

### ⚠️ DŮLEŽITÉ UPOZORNĚNÍ

1. **NIKDY nesdílej své API klíče!**
2. **Pro testování VŽDY používej TESTNET** (`BINANCE_DEMO=true`)
3. **IP Whitelist**: V Binance API nastavení povol pouze svou IP adresu
4. **Oprávnění**: Pro začátek zapni pouze "Enable Reading" (bez trading)
5. **2FA**: Vždy používej 2FA autentizaci na Binance účtu

### Demo vs Real Mode

| Feature | DEMO (Testnet) | REAL |
|---------|----------------|------|
| Money | ❌ Fake (testovací) | ✅ Real |
| Risk | ✅ Zero risk | ⚠️ Real risk |
| Testing | ✅ Perfect | ❌ Not recommended |
| API Keys | testnet.binancefuture.com | binance.com |
| Badge | 🧪 TESTNET MODE | (none) |

## 📱 UI Features

### Auto-refresh
- Data se automaticky obnovují každých **10 sekund**
- Manuální refresh pomocí tlačítka 🔄 Refresh

### Demo Mode Indicator
- Když je aktivní testnet (`BINANCE_DEMO=true`), zobrazí se žlutý badge:
  ```
  🧪 TESTNET MODE
  ```

### Color Coding
- **Zelená** - Profit / Positive P&L
- **Červená** - Loss / Negative P&L
- **LONG pozice** - Zelený badge
- **SHORT pozice** - Červený badge
- **BUY orders** - Modrý badge
- **SELL orders** - Žlutý badge

### Empty States
- "No active positions" - Když nemáš otevřené pozice
- "No open orders" - Když nemáš aktivní příkazy
- "No assets" - Když nemáš žádná aktiva

## 🚀 Usage

### Workflow

1. **Start with TESTNET**
   ```bash
   BINANCE_DEMO=true
   ```
   
2. **Test your strategies**
   - Otevři pozice na testnet účtu
   - Sleduj live P&L na dashboardu
   - Ověř správnost dat

3. **Switch to REAL** (když jsi připraven)
   ```bash
   BINANCE_DEMO=false
   ```
   
4. **Monitor live trades**
   - Sleduj své pozice v real-time
   - Kontroluj P&L
   - Reaguj na market changes

## 🔗 Navigation

Dashboard obsahuje navigační tlačítka:
- **🏠 Dashboard** - Hlavní přehled (paper trading)
- **📡 Live** - Binance Futures účet (tato stránka)
- **📋 Strategy Logs** - Historie AI rozhodnutí
- **🔄 Refresh** - Manuální refresh dat

## 📊 API Endpoints

Pro programový přístup:

```bash
# Get account info
curl http://localhost:5000/api/binance-account

# Response format:
{
  "success": true,
  "demo_mode": true,
  "account": {
    "total_wallet_balance": 4996.58,
    "total_unrealized_profit": 17.28,
    "available_balance": 4539.93,
    "total_margin_balance": 5013.86
  },
  "positions": [...],
  "orders": [...],
  "assets": [...]
}
```

## ❓ Troubleshooting

### Error: "API-key format invalid"
- **Příčina**: Špatný formát API klíčů
- **Řešení**: Zkontroluj, že API klíče jsou správně zkopírované bez mezer

### Error: "API Secret required for private endpoints"
- **Příčina**: Chybí API credentials v `.env`
- **Řešení**: Přidej `BINANCE_API_KEY` a `BINANCE_API_SECRET` do `.env`

### Error: Connection timeout
- **Příčina**: Špatná URL nebo network problém
- **Řešení**: Zkontroluj `BINANCE_DEMO` flag (true=testnet, false=mainnet)

### Data se nezobrazují
1. Zkontroluj že dashboard běží: `ps aux | grep web_api`
2. Zkontroluj logy: `tail -f /home/flow/langtest/logs/web_api.log`
3. Zkontroluj API credentials: `grep BINANCE /home/flow/langtest/.env`

## 📚 Related Docs

- [LIVE_TRADING.md](LIVE_TRADING.md) - Live trading implementation
- [LIVE_TRADING_QUICKSTART.md](LIVE_TRADING_QUICKSTART.md) - Quick start guide
- [WEB_DASHBOARD.md](../WEB_DASHBOARD.md) - Dashboard overview

## 🎯 Next Steps

1. ✅ Set up Testnet account
2. ✅ Configure `.env` with testnet credentials
3. ✅ Test dashboard with fake money
4. ⏳ When ready, switch to real account
5. ⏳ Implement live trading strategies

---

**Remember**: Always test on TESTNET first! 🧪

