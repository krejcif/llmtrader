#!/usr/bin/env python3
"""Debug script to find ALL symbols with trades"""
import sys
sys.path.insert(0, '/home/flow/deeptrader/src')

from utils.binance_client import BinanceClient
from datetime import datetime, timedelta

client = BinanceClient()
now = datetime.now()

print(f"\n{'='*80}")
print(f"CHECKING ALL SYMBOLS WITH TRADES")
print(f"{'='*80}\n")

# Get all positions (open and closed)
print("STEP 1: Get all positions from Binance")
positions = client.client.futures_position_information()
print(f"✅ Total positions returned: {len(positions)}")

open_positions = [p for p in positions if float(p['positionAmt']) != 0]
print(f"✅ Open positions: {len(open_positions)}")
for p in open_positions:
    print(f"   - {p['symbol']}: {p['positionAmt']} @ ${p['entryPrice']}, PnL: ${p['unRealizedProfit']}")

# Get list of ALL available symbols from exchange info
print(f"\n{'='*80}")
print("STEP 2: Get exchange info to find tradeable symbols")
exchange_info = client.client.futures_exchange_info()
all_symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING' and 'USDT' in s['symbol']]
print(f"✅ Total tradeable USDT symbols: {len(all_symbols)}")

# Try to get trades for top symbols and any that had recent activity
print(f"\n{'='*80}")
print("STEP 3: Check trades for symbols (limited to common ones)")

# Common symbols to check
common_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 
                  'DOGEUSDT', 'MATICUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'ATOMUSDT']

# Add any open position symbols
for p in open_positions:
    if p['symbol'] not in common_symbols:
        common_symbols.append(p['symbol'])

symbols_with_trades = {}

for symbol in common_symbols:
    try:
        # Get last 1000 trades for this symbol (no time filter)
        trades = client.client.futures_account_trades(
            symbol=symbol,
            limit=1000
        )
        
        if trades:
            # Calculate aggregated stats
            total_pnl = sum(float(t.get('realizedPnl', 0)) for t in trades)
            total_commission = sum(abs(float(t.get('commission', 0))) for t in trades)
            first_trade = datetime.fromtimestamp(trades[0]['time'] / 1000)
            last_trade = datetime.fromtimestamp(trades[-1]['time'] / 1000)
            
            symbols_with_trades[symbol] = {
                'count': len(trades),
                'realized_pnl': total_pnl,
                'commission': total_commission,
                'net_pnl': total_pnl - total_commission,
                'first_trade': first_trade,
                'last_trade': last_trade,
                'duration_hours': (trades[-1]['time'] - trades[0]['time']) / (1000 * 3600)
            }
            
    except Exception as e:
        # Symbol not traded or error
        pass

print(f"\n✅ Found {len(symbols_with_trades)} symbols with trades:\n")

# Sort by last trade time
sorted_symbols = sorted(symbols_with_trades.items(), key=lambda x: x[1]['last_trade'], reverse=True)

for i, (symbol, data) in enumerate(sorted_symbols, 1):
    print(f"{i}. {symbol}:")
    print(f"   Trades: {data['count']}")
    print(f"   Realized P&L: ${data['realized_pnl']:.2f}")
    print(f"   Commission: ${data['commission']:.2f}")
    print(f"   Net P&L: ${data['net_pnl']:.2f}")
    print(f"   First trade: {data['first_trade']}")
    print(f"   Last trade: {data['last_trade']}")
    print(f"   Duration: {data['duration_hours']:.1f}h")
    print()

# Check filter logic
print(f"{'='*80}")
print("STEP 4: Apply dashboard filter (realized_pnl != 0 OR trade_count >= 2)")
print(f"{'='*80}\n")

filtered = {
    sym: data for sym, data in symbols_with_trades.items()
    if data['realized_pnl'] != 0 or data['count'] >= 2
}

print(f"✅ After filter: {len(filtered)} symbols would be shown\n")

for symbol, data in sorted(filtered.items(), key=lambda x: x[1]['last_trade'], reverse=True):
    print(f"   ✅ {symbol}: P&L=${data['realized_pnl']:.2f}, Trades={data['count']}")

if len(filtered) < len(symbols_with_trades):
    print(f"\n❌ FILTERED OUT {len(symbols_with_trades) - len(filtered)} symbols:")
    filtered_out = {sym: data for sym, data in symbols_with_trades.items() if sym not in filtered}
    for symbol, data in filtered_out.items():
        print(f"   ❌ {symbol}: P&L=${data['realized_pnl']:.2f}, Trades={data['count']}")

print(f"\n{'='*80}")
print("DEBUG COMPLETE")
print(f"{'='*80}\n")

