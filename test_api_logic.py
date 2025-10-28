#!/usr/bin/env python3
"""Test the exact logic from get_binance_analytics"""
import sys
sys.path.insert(0, '/home/flow/deeptrader/src')

from utils.binance_client import BinanceClient
from datetime import datetime, timedelta

client = BinanceClient()
now = datetime.now()
month_ago = int((now - timedelta(days=30)).timestamp() * 1000)

print(f"\n{'='*60}")
print(f"TESTING EXACT API LOGIC")
print(f"{'='*60}\n")

# Step 1: Get positions (this is available in the real API)
print("STEP 1: Get positions")
positions = client.client.futures_position_information()
print(f"✅ Got {len(positions)} positions")
open_positions = [p for p in positions if float(p['positionAmt']) != 0]
print(f"✅ {len(open_positions)} open positions")
for p in open_positions:
    print(f"   - {p['symbol']}: {p['positionAmt']}")
print()

# Step 2: Get income history
print("STEP 2: Get income history")
income_items = client.client.futures_income_history(
    startTime=month_ago,
    limit=1000
)
print(f"✅ Got {len(income_items)} income items")
print()

# Step 3: Extract symbols from income history
print("STEP 3: Extract symbols from income history")
active_symbols = set()
for item in income_items:
    if item.get('symbol'):
        active_symbols.add(item['symbol'])
    elif item.get('asset') and item.get('asset') != 'USDT':
        active_symbols.add(item['asset'] + 'USDT')

print(f"✅ Found {len(active_symbols)} symbols: {list(active_symbols)}")
print()

# Step 4: Fallback to open positions
print("STEP 4: Fallback if no symbols")
if not active_symbols:
    print("⚠️  No symbols in income history, using open positions")
    for pos in positions:
        if float(pos['positionAmt']) != 0:
            active_symbols.add(pos['symbol'])
    print(f"✅ After fallback: {len(active_symbols)} symbols: {list(active_symbols)}")
else:
    print(f"✅ Skipping fallback, already have {len(active_symbols)} symbols")
print()

# Step 5: Fetch trades for each symbol
print("STEP 5: Fetch trades for active symbols")
all_trades = []
for symbol in active_symbols:
    try:
        trades = client.client.futures_account_trades(
            symbol=symbol,
            startTime=month_ago,
            limit=1000
        )
        all_trades.extend(trades)
        print(f"   ✅ {symbol}: {len(trades)} trades")
    except Exception as e:
        print(f"   ❌ {symbol}: {e}")

print(f"\n✅ Total: {len(all_trades)} trades")
print()

# Step 6: Aggregate trades
print("STEP 6: Aggregate trades by symbol")
closed_positions = {}
for trade in all_trades:
    symbol = trade['symbol']
    realized_pnl = float(trade.get('realizedPnl', 0))
    commission = float(trade.get('commission', 0))
    timestamp = trade['time']
    
    if symbol not in closed_positions:
        closed_positions[symbol] = {
            'symbol': symbol,
            'realized_pnl': 0,
            'total_commission': 0,
            'trade_count': 0,
            'last_trade_time': timestamp,
            'first_trade_time': timestamp
        }
    
    closed_positions[symbol]['realized_pnl'] += realized_pnl
    closed_positions[symbol]['total_commission'] += abs(commission)
    closed_positions[symbol]['trade_count'] += 1
    closed_positions[symbol]['last_trade_time'] = max(
        closed_positions[symbol]['last_trade_time'], 
        timestamp
    )
    closed_positions[symbol]['first_trade_time'] = min(
        closed_positions[symbol]['first_trade_time'], 
        timestamp
    )

print(f"✅ Aggregated {len(closed_positions)} positions (before filter)")
for sym, data in closed_positions.items():
    print(f"   - {sym}: P&L=${data['realized_pnl']:.2f}, Comm=${data['total_commission']:.2f}, Trades={data['trade_count']}")
print()

# Step 7: Apply filter
print("STEP 7: Apply filter (pnl != 0 or trade_count >= 2)")
closed_positions_filtered = {
    sym: data for sym, data in closed_positions.items()
    if data['realized_pnl'] != 0 or data['trade_count'] >= 2
}

print(f"✅ After filter: {len(closed_positions_filtered)} positions")
for sym, data in closed_positions_filtered.items():
    print(f"   - {sym}: P&L=${data['realized_pnl']:.2f}, Comm=${data['total_commission']:.2f}, Trades={data['trade_count']}")
print()

print(f"{'='*60}")
print("TEST COMPLETE")
print(f"{'='*60}\n")

