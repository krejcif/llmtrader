#!/usr/bin/env python3
"""Test loading symbols from strategies"""
import sys
sys.path.insert(0, '/home/flow/deeptrader/src')

from strategy_config import STRATEGIES
from utils.binance_client import BinanceClient
from datetime import datetime

print(f"\n{'='*80}")
print(f"TESTING STRATEGY SYMBOLS")
print(f"{'='*80}\n")

# Step 1: Get symbols from strategies
print("STEP 1: Extract symbols from active strategies")
strategy_symbols = set()
for strategy in STRATEGIES:
    enabled = strategy.enabled
    symbol = strategy.symbol.upper() if strategy.symbol else ''
    print(f"   {strategy.name}:")
    print(f"      Enabled: {enabled}")
    print(f"      Symbol: {symbol if symbol else 'N/A (uses default)'}")
    
    if enabled and symbol:
        strategy_symbols.add(symbol)

print(f"\n✅ Active strategy symbols: {sorted(strategy_symbols)}\n")

# Step 2: Check for trades on these symbols
client = BinanceClient()

print(f"{'='*80}")
print("STEP 2: Check for trades on strategy symbols")
print(f"{'='*80}\n")

for symbol in sorted(strategy_symbols):
    try:
        trades = client.client.futures_account_trades(
            symbol=symbol,
            limit=1000
        )
        if trades:
            total_pnl = sum(float(t.get('realizedPnl', 0)) for t in trades)
            total_commission = sum(abs(float(t.get('commission', 0))) for t in trades)
            last_trade = datetime.fromtimestamp(trades[-1]['time'] / 1000)
            print(f"✅ {symbol}: {len(trades)} trades, P&L=${total_pnl:.2f}, last trade: {last_trade}")
        else:
            print(f"   {symbol}: No trades")
    except Exception as e:
        print(f"   {symbol}: Error - {e}")

print(f"\n{'='*80}")
print("TEST COMPLETE")
print(f"{'='*80}\n")

