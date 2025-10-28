#!/usr/bin/env python3
"""Test script to debug Binance API responses"""
import sys
sys.path.insert(0, '/home/flow/deeptrader/src')

from utils.binance_client import BinanceClient
from datetime import datetime, timedelta

client = BinanceClient()
now = datetime.now()
month_ago = int((now - timedelta(days=30)).timestamp() * 1000)

print(f"\n{'='*60}")
print(f"BINANCE API DEBUG TEST")
print(f"{'='*60}\n")
print(f"📅 Testing period: Last 30 days")
print(f"   From: {datetime.fromtimestamp(month_ago/1000)}")
print(f"   To: {now}\n")

# Test 1: Income history
print(f"{'='*60}")
print("TEST 1: Income History")
print(f"{'='*60}")
try:
    income_items = client.client.futures_income_history(
        startTime=month_ago,
        limit=1000
    )
    print(f"✅ Received {len(income_items)} income items\n")
    
    # Show first 5 items
    for i, item in enumerate(income_items[:5]):
        print(f"Item {i+1}:")
        print(f"  Time: {datetime.fromtimestamp(item['time']/1000)}")
        print(f"  Type: {item['incomeType']}")
        print(f"  Income: {item['income']}")
        print(f"  Asset: {item.get('asset', 'N/A')}")
        print(f"  Symbol: {item.get('symbol', 'N/A')}")
        print()
    
    # Extract active symbols
    active_symbols = set()
    for item in income_items:
        if item.get('symbol'):
            active_symbols.add(item['symbol'])
        elif item.get('asset') and item.get('asset') != 'USDT':
            active_symbols.add(item['asset'] + 'USDT')
    
    print(f"🎯 Found {len(active_symbols)} active symbols: {list(active_symbols)}\n")
    
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 2: Account trades for each symbol
print(f"{'='*60}")
print("TEST 2: Account Trades per Symbol")
print(f"{'='*60}")
if active_symbols:
    for symbol in list(active_symbols)[:3]:  # Test first 3 symbols
        try:
            trades = client.client.futures_account_trades(
                symbol=symbol,
                startTime=month_ago,
                limit=1000
            )
            print(f"\n📊 {symbol}: {len(trades)} trades")
            
            if trades:
                # Show first 2 trades
                for i, trade in enumerate(trades[:2]):
                    print(f"\n  Trade {i+1}:")
                    print(f"    Time: {datetime.fromtimestamp(trade['time']/1000)}")
                    print(f"    Side: {trade['side']}")
                    print(f"    Qty: {trade['qty']}")
                    print(f"    Price: {trade['price']}")
                    print(f"    Realized P&L: {trade.get('realizedPnl', 0)}")
                    print(f"    Commission: {trade.get('commission', 0)}")
                
                # Calculate total P&L
                total_pnl = sum(float(t.get('realizedPnl', 0)) for t in trades)
                total_commission = sum(abs(float(t.get('commission', 0))) for t in trades)
                print(f"\n  📈 Summary:")
                print(f"    Total Realized P&L: ${total_pnl:.2f}")
                print(f"    Total Commission: ${total_commission:.2f}")
                print(f"    Net P&L: ${total_pnl - total_commission:.2f}")
                
        except Exception as e:
            print(f"\n❌ Error for {symbol}: {e}")
else:
    print("\n⚠️  No active symbols found to test")

print(f"\n{'='*60}")
print("TEST COMPLETE")
print(f"{'='*60}\n")

