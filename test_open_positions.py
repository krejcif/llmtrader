#!/usr/bin/env python3
"""Test script to check open positions and their trades"""
import sys
sys.path.insert(0, '/home/flow/deeptrader/src')

from utils.binance_client import BinanceClient
from datetime import datetime, timedelta

client = BinanceClient()
now = datetime.now()

print(f"\n{'='*60}")
print(f"OPEN POSITIONS & TRADES TEST")
print(f"{'='*60}\n")

# Test 1: Get open positions
print("TEST 1: Open Positions")
print(f"{'='*60}")
try:
    positions = client.client.futures_position_information()
    open_positions = [p for p in positions if float(p['positionAmt']) != 0]
    
    print(f"✅ Found {len(open_positions)} open positions\n")
    
    for pos in open_positions[:5]:
        print(f"📊 {pos['symbol']}:")
        print(f"   Position Amt: {pos['positionAmt']}")
        print(f"   Entry Price: {pos['entryPrice']}")
        print(f"   Mark Price: {pos['markPrice']}")
        print(f"   Unrealized P&L: {pos['unRealizedProfit']}")
        print(f"   Leverage: {pos.get('leverage', 'N/A')}")
        print()
    
    # Test 2: Get ALL trades for symbols with open positions
    if open_positions:
        print(f"\n{'='*60}")
        print("TEST 2: All Trades for Open Position Symbols")
        print(f"{'='*60}\n")
        
        for pos in open_positions[:3]:
            symbol = pos['symbol']
            try:
                # Get ALL trades (no time limit) to see trade history
                print(f"📊 Fetching all trades for {symbol}...")
                trades = client.client.futures_account_trades(
                    symbol=symbol,
                    limit=1000  # Last 1000 trades
                )
                
                if trades:
                    print(f"   ✅ Found {len(trades)} trades")
                    print(f"   First trade: {datetime.fromtimestamp(trades[0]['time']/1000)}")
                    print(f"   Last trade: {datetime.fromtimestamp(trades[-1]['time']/1000)}")
                    
                    # Show some trade details
                    for i, trade in enumerate(trades[:3]):
                        print(f"\n   Trade {i+1}:")
                        print(f"     Time: {datetime.fromtimestamp(trade['time']/1000)}")
                        print(f"     Side: {trade['side']}")
                        print(f"     Qty: {trade['qty']}")
                        print(f"     Price: {trade['price']}")
                        print(f"     Realized P&L: {trade.get('realizedPnl', 0)}")
                        print(f"     Commission: {trade.get('commission', 0)}")
                    
                    # Calculate totals
                    total_pnl = sum(float(t.get('realizedPnl', 0)) for t in trades)
                    total_commission = sum(abs(float(t.get('commission', 0))) for t in trades)
                    
                    print(f"\n   📈 Totals:")
                    print(f"     Realized P&L: ${total_pnl:.4f}")
                    print(f"     Commission: ${total_commission:.4f}")
                    print(f"     Net P&L: ${total_pnl - total_commission:.4f}")
                else:
                    print(f"   ⚠️  No trades found")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()
    
except Exception as e:
    print(f"❌ Error: {e}\n")

print(f"{'='*60}")
print("TEST COMPLETE")
print(f"{'='*60}\n")

