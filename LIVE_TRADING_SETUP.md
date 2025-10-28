# 🔴 Live Trading Setup - Quick Start

## ✅ Co jsem implementoval

1. **Per-strategy live trading**: Každá strategie může mít zapnutý/vypnutý live trading
2. **Demo mód (Testnet)**: Můžeš testovat na Binance Testnet před ostrým nasazením
3. **Web UI**: Zapínání/vypínání live tradingu přímo z dashboardu
4. **Persistentní config**: Nastavení se ukládá přes restarty
5. **Safety features**: Detekce konfliktů pozic, minimální velikost pozice, atd.

## 🚀 Jak to spustit

### Krok 1: Nastav Binance API klíče

#### Pro DEMO (Testnet - doporučeno začít tady!)

1. Jdi na: https://testnet.binancefuture.com/
2. Přihlas se přes GitHub/Google
3. Vygeneruj API Key & Secret
4. Doplň si testovací USDT (tlačítko "Get Test Funds")

#### Pro REAL trading (POZOR!)

1. Jdi na: https://www.binance.com/
2. Vytvoř účet a dokonči KYC
3. Jdi do API Management
4. Vytvoř API Key s Futures permissions
5. Ulož API Key a Secret

### Krok 2: Uprav .env soubor

```bash
# Přidej do .env:
BINANCE_API_KEY=tvůj_api_key
BINANCE_API_SECRET=tvůj_api_secret

# DEMO režim (TESTNET)
BINANCE_DEMO=true   # Pro demo účet
# BINANCE_DEMO=false  # Pro REÁLNÝ účet (POZOR!)
```

### Krok 3: Zapni live trading pro strategie

**Způsob A: Přes Dashboard (doporučeno)**

1. Otevři dashboard: http://localhost:5000
2. Sroluj na sekci "🔴 Live Trading Configuration"
3. Zaškrtni "Enable Live Trading" u strategií, které chceš
4. Nastavení se uloží automaticky

**Způsob B: Editace JSON**

Vytvoř/edituj `data/live_trading_config.json`:
```json
{
  "sol": true,
  "eth": false
}
```

### Krok 4: Restart bota

```bash
./bot.sh restart-all
```

## 📊 Co uvidíš v logu

```
🔴 Live Trading (1 strategies, DEMO/TESTNET): sol
🧪 Using Binance TESTNET (Demo Mode)
🚀 [SOL] Executing LONG: 10.5 SOLUSDT @ $142.34 ($1,494.62)
   Leverage: 1x, Position Size: 10.0%
   ✅ Order placed: 12345678 (Trade ID: 142)
```

## ⚠️ DŮLEŽITÉ!

1. **Začni s DEMO**: Vždy nejdřív otestuj s `BINANCE_DEMO=true`
2. **Malé pozice**: Začni s malými pozicemi (5-10% účtu)
3. **Jedna strategie**: Zapni live trading pro jednu strategii, ověř že funguje
4. **Sleduj logy**: První obchody pečlivě monitoruj
5. **Rozumíš rizikům**: Live trading = reálné peníze = reálné ztráty možné

## 📚 Podrobná dokumentace

Viz: `docs/LIVE_TRADING.md`

## 🆘 Troubleshooting

**"API Secret required"**
→ Přidej BINANCE_API_KEY a BINANCE_API_SECRET do .env

**"API-key format invalid"**
→ Zkontroluj, že klíče jsou správně (bez mezer, celý string)
→ Pro testnet: Klíče musí být z https://testnet.binancefuture.com/

**Live trading se nespouští**
→ Zkontroluj že strategie je enabled (zelená)
→ Zkontroluj že máš zaškrtnuté "Enable Live Trading"
→ Podívej se do logů na chybové hlášky

---

**⚠️ DISCLAIMER: Live trading = reálné peníze. Používej na vlastní riziko!**


