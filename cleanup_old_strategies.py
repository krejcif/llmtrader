#!/usr/bin/env python3
"""Clean up trades from old/removed strategies"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
from utils.database import TradingDatabase

# Current active strategies (from strategy_config.py)
ACTIVE_STRATEGIES = ['sol', 'sol_fast', 'eth', 'eth_fast']

def preview_cleanup():
    """Preview what will be deleted"""
    db = TradingDatabase()
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all strategies in database
    cursor.execute("SELECT DISTINCT strategy FROM trades ORDER BY strategy")
    all_strategies = [row['strategy'] for row in cursor.fetchall()]
    
    print("="*70)
    print("CLEANUP OLD STRATEGIES - PREVIEW")
    print("="*70)
    print(f"\nActive strategies: {', '.join(ACTIVE_STRATEGIES)}")
    print(f"\nAll strategies in database: {', '.join(all_strategies)}")
    
    # Find strategies to delete
    to_delete = [s for s in all_strategies if s not in ACTIVE_STRATEGIES]
    
    if not to_delete:
        print("\n✅ No old strategies found. Database is clean!")
        conn.close()
        return False
    
    print(f"\n⚠️  Strategies to DELETE: {', '.join(to_delete)}")
    
    # Count trades per strategy
    print(f"\n📊 Trade counts:")
    for strategy in all_strategies:
        cursor.execute("SELECT COUNT(*) as count FROM trades WHERE strategy = ?", (strategy,))
        count = cursor.fetchone()['count']
        
        status = "✅ KEEP" if strategy in ACTIVE_STRATEGIES else "❌ DELETE"
        print(f"   {status} - {strategy}: {count} trades")
    
    # Total to delete
    cursor.execute(
        f"SELECT COUNT(*) as count FROM trades WHERE strategy NOT IN ({','.join('?'*len(ACTIVE_STRATEGIES))})",
        ACTIVE_STRATEGIES
    )
    total_to_delete = cursor.fetchone()['count']
    
    print(f"\n🗑️  Total trades to DELETE: {total_to_delete}")
    
    # Show some examples
    if total_to_delete > 0:
        print(f"\n📋 Examples of trades to be deleted:")
        cursor.execute(
            f"""SELECT trade_id, symbol, strategy, action, entry_time, status 
               FROM trades 
               WHERE strategy NOT IN ({','.join('?'*len(ACTIVE_STRATEGIES))})
               ORDER BY entry_time DESC
               LIMIT 5""",
            ACTIVE_STRATEGIES
        )
        
        for row in cursor.fetchall():
            print(f"   - {row['trade_id'][:50]}... ({row['strategy']}, {row['status']})")
    
    conn.close()
    return total_to_delete > 0

def delete_old_strategies():
    """Delete trades from old strategies"""
    db = TradingDatabase()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # Count before
    cursor.execute("SELECT COUNT(*) as count FROM trades")
    count_before = cursor.fetchone()[0]
    
    # Delete trades from old strategies
    cursor.execute(
        f"DELETE FROM trades WHERE strategy NOT IN ({','.join('?'*len(ACTIVE_STRATEGIES))})",
        ACTIVE_STRATEGIES
    )
    
    deleted_count = cursor.rowcount
    conn.commit()
    
    # Count after
    cursor.execute("SELECT COUNT(*) as count FROM trades")
    count_after = cursor.fetchone()[0]
    
    print(f"\n✅ Cleanup complete!")
    print(f"   Trades before: {count_before}")
    print(f"   Trades deleted: {deleted_count}")
    print(f"   Trades remaining: {count_after}")
    
    # Also clean up strategy_runs table
    cursor.execute(
        f"DELETE FROM strategy_runs WHERE strategy NOT IN ({','.join('?'*len(ACTIVE_STRATEGIES))})",
        ACTIVE_STRATEGIES
    )
    
    runs_deleted = cursor.rowcount
    conn.commit()
    
    if runs_deleted > 0:
        print(f"   Strategy runs deleted: {runs_deleted}")
    
    conn.close()
    
    print(f"\n🎉 Database cleaned successfully!")

def main():
    """Main cleanup script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up trades from old strategies')
    parser.add_argument('--confirm', action='store_true', 
                       help='Confirm deletion without prompt')
    parser.add_argument('--preview', action='store_true',
                       help='Only show preview, do not delete')
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("DATABASE CLEANUP - Remove trades from old strategies")
    print("="*70)
    
    # Preview what will be deleted
    has_old_trades = preview_cleanup()
    
    if not has_old_trades:
        return
    
    # If preview only, exit
    if args.preview:
        print("\n👀 Preview only - no changes made.")
        return
    
    # Ask for confirmation
    print("\n" + "="*70)
    print("⚠️  WARNING: This will PERMANENTLY delete trades!")
    print("="*70)
    
    if not args.confirm:
        print("\n💡 To proceed, run with --confirm flag:")
        print("   python3 cleanup_old_strategies.py --confirm")
        return
    
    # Delete
    print("\n🗑️  Deleting old trades...")
    delete_old_strategies()

if __name__ == "__main__":
    main()

