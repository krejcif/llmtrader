# Live Trading System

## Overview

DeepTrader now supports **per-strategy live trading** with Binance Futures. Each strategy can independently run in either **paper trading** or **live trading** mode.

## Features

- ✅ **Per-strategy configuration**: Enable/disable live trading for each strategy independently
- ✅ **Demo mode (Testnet)**: Test live trading on Binance Futures Testnet before going live
- ✅ **Web UI**: Toggle live trading on/off directly from dashboard
- ✅ **Persistent configuration**: Settings saved across bot restarts
- ✅ **Risk management**: Position sizing, leverage, and stop-loss from AI recommendations
- ✅ **Safety features**: Position conflict detection, minimum position size checks

## Setup

### 1. Get Binance API Keys

#### For Demo Trading (TESTNET - Recommended First!)
1. Go to https://testnet.binancefuture.com/
2. Login with GitHub/Google account
3. Generate API Key & Secret
4. Fund your testnet account with fake USDT (use the "Get Test Funds" button)

#### For Real Trading (USE WITH CAUTION!)
1. Go to https://www.binance.com/
2. Create account and complete KYC
3. Go to API Management
4. Create API Key with Futures permissions
5. Save API Key and Secret

### 2. Configure Environment

Edit your `.env` file:

```bash
# Binance API Configuration
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# Demo Mode (TESTNET)
# Set to "true" to use Binance Testnet (demo account)
# Set to "false" to use REAL account (BE CAREFUL!)
BINANCE_DEMO=true
```

### 3. Enable Live Trading for Strategies

You can enable live trading in two ways:

#### Option A: Via Web Dashboard (Recommended)
1. Open dashboard: http://localhost:5000
2. Scroll to "Live Trading Configuration" section
3. Toggle "Enable Live Trading" for desired strategies
4. Settings are saved automatically

#### Option B: Via Configuration File
Edit `data/live_trading_config.json`:
```json
{
  "sol": true,
  "sol_fast": false,
  "eth": true,
  "eth_fast": false
}
```

### 4. Start Bot

```bash
./bot.sh start-all
```

The bot will:
- Show which strategies are in PAPER mode
- Show which strategies are in LIVE mode
- Indicate if using DEMO (Testnet) or REAL account

## How It Works

### Trade Execution Flow

1. **Analysis**: Bot analyzes market using configured strategies
2. **Decision**: AI generates trading recommendations (LONG/SHORT/NEUTRAL)
3. **Execution Split**:
   - Strategies with `live_trading=False` → Paper trading (database only)
   - Strategies with `live_trading=True` → Live trading (Binance API)

### Live Trading Process

For strategies with live trading enabled:

1. **Check Existing Positions**: Query Binance for open positions
2. **Position Conflicts**: 
   - If opposite direction → Close existing, open new
   - If same direction → Skip (already in position)
3. **Calculate Position Size**: 
   - Based on risk management from AI (default 10% of balance)
   - Apply leverage from recommendation
4. **Execute Order**: Market order via Binance API
5. **Database Logging**: Store trade in database with `live_trade=True`

### Risk Management

Live trading uses AI-generated risk management:
- **Position Size**: 10% of available balance (default)
- **Leverage**: From AI recommendation (default 1x)
- **Stop Loss**: AI-calculated stop loss price
- **Take Profit**: AI-calculated take profit price

## Safety Features

### Built-in Protections

1. **Minimum Position Size**: $10 minimum (prevents dust trades)
2. **Position Conflict Detection**: Prevents multiple positions in same symbol
3. **Symbol Precision**: Automatic rounding to exchange requirements
4. **Demo Mode Badge**: UI clearly shows if using Testnet or Real account
5. **Disabled Strategy Protection**: Can't enable live trading for disabled strategies

### Best Practices

1. **Start with Testnet**: Always test with `BINANCE_DEMO=true` first
2. **Small Positions**: Start with small position sizes (5-10%)
3. **Monitor Closely**: Watch first few trades carefully
4. **One Strategy at a Time**: Enable live trading for one strategy, verify it works
5. **Check Logs**: Monitor `logs/trading_bot.log` for execution details

## Monitoring

### Dashboard

- **Live Trading Configuration**: Shows all strategies with live trading toggles
- **Recent Trades**: Shows both paper and live trades
- **Live Dashboard** (`/live`): Real-time Binance account overview

### Logs

```bash
# Main bot log
tail -f logs/trading_bot.log

# Look for:
# 🔴 Live Trading (N strategies, DEMO/TESTNET): strategy_name
# 🚀 [STRATEGY_NAME] Executing LONG: quantity symbol @ $price
# ✅ Order placed: order_id (Trade ID: trade_id)
```

### Database

Live trades are marked with `live_trade=True`:

```bash
sqlite3 data/trading.db "SELECT * FROM trades WHERE live_trade = 1;"
```

## Architecture

### Files

- `src/agents/live_trading.py` - Live trading execution logic
- `src/agents/paper_trading.py` - Paper trading execution logic
- `src/strategy_config.py` - Strategy configuration with `live_trading` parameter
- `src/trading_bot_dynamic.py` - Main bot loop (splits paper/live execution)
- `src/web_api.py` - API endpoints for strategy management
- `data/live_trading_config.json` - Persistent live trading configuration

### API Endpoints

```
GET  /api/strategies
     → List all strategies with live_trading status

POST /api/strategies/<strategy_name>/live-trading
     Body: {"live_trading": true/false}
     → Toggle live trading for strategy
```

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ANALYSIS CYCLE - 15 min interval - 2025-01-28 10:45:00
⚡ Running 2 strategies in PARALLEL: sol, eth
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💼 Executing trades...

📝 Paper Trading (1 strategies): eth
ℹ️  [ETH] No trade - NEUTRAL

🔴 Live Trading (1 strategies, DEMO/TESTNET): sol
🧪 Using Binance TESTNET (Demo Mode)
🚀 [SOL] Executing LONG: 10.5 SOLUSDT @ $142.3450 ($1,494.62)
   Leverage: 1x, Position Size: 10.0%
   ✅ Order placed: 12345678 (Trade ID: 142)

✅ Executed 1 LIVE trade(s)
```

## Troubleshooting

### "API Secret required for private endpoints"
- Add `BINANCE_API_KEY` and `BINANCE_API_SECRET` to `.env`

### "APIError(code=-2014): API-key format invalid"
- Check that API keys are correct (no spaces, full string)
- For testnet: Keys must be from https://testnet.binancefuture.com/

### "Position value too small"
- Minimum position is $10
- Increase position size or account balance

### Live trading not executing
- Check strategy is enabled: `strategy.enabled=True`
- Check live trading enabled: Toggle in UI or check `data/live_trading_config.json`
- Check Binance API credentials are correct
- Check logs for error messages

### "Symbol not found on exchange"
- Verify symbol exists on Binance Futures
- Check symbol spelling (e.g., "SOLUSDT" not "SOL/USDT")

## Warnings

⚠️ **LIVE TRADING USES REAL MONEY!**

- Always start with `BINANCE_DEMO=true` (Testnet)
- Test thoroughly before switching to real account
- Start with small position sizes
- Monitor trades closely
- Understand the risks of automated trading
- Never invest more than you can afford to lose

## License & Disclaimer

This software is provided "as is", without warranty of any kind. Trading cryptocurrencies
 carries risk. The developers are not responsible for any financial losses incurred 
through use of this software.

**Use at your own risk. Always do your own research.**
