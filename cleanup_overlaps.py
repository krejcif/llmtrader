#!/usr/bin/env python
"""Clean up overlapping trades from database"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
from datetime import datetime

def cleanup_overlapping_trades():
    """Remove trades that were created while another trade was still open"""
    
    db_path = 'data/paper_trades.db'
    
    print("\n" + "="*80)
    print("🧹 CLEANING UP OVERLAPPING TRADES")
    print("="*80 + "\n")
    
    # Backup first
    import shutil
    backup_path = f'data/paper_trades_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    shutil.copy(db_path, backup_path)
    print(f"✅ Database backed up to: {backup_path}\n")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all trades ordered by strategy and entry time
    cursor.execute('''
        SELECT trade_id, symbol, strategy, entry_time, exit_time, status
        FROM trades 
        ORDER BY strategy, entry_time
    ''')
    
    all_trades = cursor.fetchall()
    
    # Group by strategy
    trades_by_strategy = {}
    for trade in all_trades:
        strategy = trade['strategy']
        if strategy not in trades_by_strategy:
            trades_by_strategy[strategy] = []
        trades_by_strategy[strategy].append(trade)
    
    # Find overlapping trades to delete
    trades_to_delete = []
    
    for strategy, trades in trades_by_strategy.items():
        print(f"Checking {strategy.upper()} strategy ({len(trades)} trades)...")
        
        for i, trade in enumerate(trades):
            # Skip first trade (always keep)
            if i == 0:
                continue
            
            # Skip if no exit time (still open)
            if not trade['exit_time']:
                continue
            
            entry_current = datetime.fromisoformat(trade['entry_time'])
            
            # Check all previous trades
            for prev_trade in trades[:i]:
                # Skip if previous trade has no exit
                if not prev_trade['exit_time']:
                    continue
                
                entry_prev = datetime.fromisoformat(prev_trade['entry_time'])
                exit_prev = datetime.fromisoformat(prev_trade['exit_time'])
                
                # If current trade entered BEFORE previous trade exited = OVERLAP
                if entry_current < exit_prev:
                    # This trade overlaps with previous one
                    if trade['trade_id'] not in [t['trade_id'] for t in trades_to_delete]:
                        trades_to_delete.append(trade)
                        print(f"  ❌ Overlapping: {trade['trade_id']}")
                        print(f"     Entered: {entry_current.strftime('%H:%M:%S')}")
                        print(f"     While {prev_trade['trade_id'][:40]} still open until {exit_prev.strftime('%H:%M:%S')}")
                    break
    
    print(f"\nTotal overlapping trades to delete: {len(trades_to_delete)}\n")
    
    if trades_to_delete:
        # Ask for confirmation
        print("⚠️  This will DELETE the following trades:")
        for trade in trades_to_delete[:10]:  # Show first 10
            print(f"   - {trade['trade_id']}")
        if len(trades_to_delete) > 10:
            print(f"   ... and {len(trades_to_delete) - 10} more")
        
        print()
        response = input("Are you sure you want to delete these trades? (yes/no): ")
        
        if response.lower() == 'yes':
            # Delete overlapping trades
            for trade in trades_to_delete:
                cursor.execute('DELETE FROM trades WHERE trade_id = ?', (trade['trade_id'],))
            
            conn.commit()
            print(f"\n✅ Deleted {len(trades_to_delete)} overlapping trades")
            
            # Show new stats
            cursor.execute('SELECT COUNT(*) FROM trades')
            remaining = cursor.fetchone()[0]
            print(f"✅ Remaining trades: {remaining}")
            
            # Show by strategy
            cursor.execute('SELECT strategy, COUNT(*) FROM trades GROUP BY strategy')
            print("\n📊 Trades by strategy:")
            for row in cursor.fetchall():
                print(f"   {row[0]}: {row[1]} trades")
        else:
            print("\n❌ Cleanup cancelled")
    else:
        print("✅ No overlapping trades found - database is clean!")
    
    conn.close()
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    cleanup_overlapping_trades()

