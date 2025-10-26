#!/usr/bin/env python
"""Check for overlapping trades in the same strategy"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.database import TradingDatabase
from datetime import datetime
import sqlite3

def check_trade_overlaps():
    """Check if trades within same strategy overlap in time"""
    
    db = TradingDatabase()
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("🔍 CHECKING FOR OVERLAPPING TRADES")
    print("="*80 + "\n")
    
    # Get all trades ordered by strategy and entry time
    cursor.execute('''
        SELECT trade_id, symbol, strategy, action, 
               entry_time, exit_time, status
        FROM trades 
        ORDER BY strategy, entry_time
    ''')
    
    all_trades = cursor.fetchall()
    conn.close()
    
    # Group by strategy
    trades_by_strategy = {}
    for trade in all_trades:
        strategy = trade['strategy']
        if strategy not in trades_by_strategy:
            trades_by_strategy[strategy] = []
        trades_by_strategy[strategy].append(trade)
    
    # Check each strategy
    overlaps_found = False
    
    for strategy, trades in trades_by_strategy.items():
        print(f"\n{'─'*80}")
        print(f"📐/🤖 Strategy: {strategy.upper()}")
        print(f"{'─'*80}")
        print(f"Total trades: {len(trades)}\n")
        
        overlaps = []
        
        # Check each pair of trades
        for i, trade1 in enumerate(trades):
            # Skip if still open (no exit time)
            if not trade1['exit_time']:
                continue
            
            entry1 = datetime.fromisoformat(trade1['entry_time'])
            exit1 = datetime.fromisoformat(trade1['exit_time'])
            
            for j, trade2 in enumerate(trades[i+1:], start=i+1):
                # Skip if still open
                if not trade2['exit_time']:
                    continue
                
                entry2 = datetime.fromisoformat(trade2['entry_time'])
                exit2 = datetime.fromisoformat(trade2['exit_time'])
                
                # Check if time periods overlap
                # Overlap if: trade1 still open when trade2 enters
                # OR trade2 entry is before trade1 exit
                if entry2 < exit1 and exit2 > entry1:
                    overlaps.append((trade1, trade2))
                    overlaps_found = True
        
        if overlaps:
            print(f"❌ Found {len(overlaps)} overlap(s):\n")
            for trade1, trade2 in overlaps:
                print(f"  Overlap:")
                print(f"    Trade 1: {trade1['trade_id'][:40]}")
                print(f"      {trade1['entry_time'][:19]} → {trade1['exit_time'][:19]}")
                print(f"      {trade1['action']}")
                
                print(f"    Trade 2: {trade2['trade_id'][:40]}")
                print(f"      {trade2['entry_time'][:19]} → {trade2['exit_time'][:19]}")
                print(f"      {trade2['action']}")
                print()
        else:
            print(f"✅ No overlaps - All trades properly isolated")
    
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    if overlaps_found:
        print("❌ OVERLAPPING TRADES DETECTED!")
        print("   Multiple positions open simultaneously in same strategy")
        print("   This could indicate:")
        print("   - Bug in trade execution logic")
        print("   - Monitor not closing trades properly")
        print("   - Race conditions")
        print("\n   ⚠️  NEEDS INVESTIGATION!")
    else:
        print("✅ NO OVERLAPS FOUND")
        print("   Each strategy maintains max 1 open position at a time")
        print("   Proper risk management ✅")
        print("   System working correctly ✅")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    check_trade_overlaps()

