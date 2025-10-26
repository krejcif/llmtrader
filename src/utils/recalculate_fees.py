#!/usr/bin/env python
"""Recalculate fees for existing trades in database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import config
from database import TradingDatabase

def recalculate_fees():
    """Recalculate fees for all existing trades"""
    db = TradingDatabase()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    fee_rate = config.TRADING_FEE_RATE
    
    print(f"🔧 Recalculating fees for existing trades...")
    print(f"📊 Fee rate: {fee_rate*100}% ({fee_rate})")
    
    # Get all trades
    cursor.execute('SELECT trade_id, entry_price, exit_price, status, action, pnl FROM trades')
    trades = cursor.fetchall()
    
    updated_count = 0
    
    for trade in trades:
        trade_id, entry_price, exit_price, status, action, old_pnl = trade
        
        # Calculate entry fee
        entry_fee = entry_price * fee_rate
        
        # Calculate exit fee if closed
        exit_fee = 0
        total_fees = entry_fee
        new_pnl = old_pnl  # Keep old P&L for open trades
        
        if status == 'CLOSED' and exit_price:
            exit_fee = exit_price * fee_rate
            total_fees = entry_fee + exit_fee
            
            # Recalculate P&L with fees
            if action == 'LONG':
                pnl_before_fees = exit_price - entry_price
            else:  # SHORT
                pnl_before_fees = entry_price - exit_price
            
            new_pnl = pnl_before_fees - total_fees
            new_pnl_percentage = (new_pnl / entry_price) * 100
            
            # Update with new P&L
            cursor.execute('''
                UPDATE trades 
                SET entry_fee = ?,
                    exit_fee = ?,
                    total_fees = ?,
                    pnl = ?,
                    pnl_percentage = ?
                WHERE trade_id = ?
            ''', (entry_fee, exit_fee, total_fees, new_pnl, new_pnl_percentage, trade_id))
        else:
            # Open trades - just update fees
            cursor.execute('''
                UPDATE trades 
                SET entry_fee = ?,
                    exit_fee = ?,
                    total_fees = ?
                WHERE trade_id = ?
            ''', (entry_fee, exit_fee, total_fees, trade_id))
        
        updated_count += 1
        
        if status == 'CLOSED':
            old_pnl_val = old_pnl or 0
            pnl_diff = new_pnl - old_pnl_val
            print(f"  ✓ {trade_id[:40]}... | Fees: ${total_fees:.3f} | P&L: ${old_pnl_val:.2f} → ${new_pnl:.2f} (diff: {pnl_diff:+.3f})")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Updated {updated_count} trades with fees")
    print(f"💡 All P&L values now include trading fees deduction")

if __name__ == '__main__':
    recalculate_fees()


