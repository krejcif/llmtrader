#!/usr/bin/env python
"""Automated Trade Monitor - Checks open trades and closes them if SL/TP hit"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.database import TradingDatabase
from utils.binance_client import BinanceClient
from datetime import datetime
import time


def monitor_open_trades(db: TradingDatabase, client: BinanceClient, verbose: bool = True):
    """
    Check all open trades and close them if SL or TP hit
    
    Args:
        db: Database instance
        client: Binance client instance
        verbose: Print detailed output
    """
    open_trades = db.get_open_trades()
    
    if not open_trades:
        if verbose:
            print("📊 No open trades to monitor.")
        return
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"🔍 MONITORING {len(open_trades)} OPEN TRADES")
        print(f"{'='*60}\n")
    
    trades_closed = 0
    
    for trade in open_trades:
        symbol = trade['symbol']
        trade_id = trade['trade_id']
        action = trade['action']
        entry_price = trade['entry_price']
        stop_loss = trade['stop_loss']
        take_profit = trade['take_profit']
        
        try:
            # Get current price
            current_price = client.get_current_price(symbol)
            
            if verbose:
                print(f"Trade: {trade_id}")
                print(f"  {action} @ ${entry_price}")
                print(f"  Current: ${current_price}")
                print(f"  SL: ${stop_loss} | TP: ${take_profit}")
            
            # Check if SL or TP hit
            should_close = False
            exit_price = None
            exit_reason = None
            
            if action == 'LONG':
                unrealized_pnl = current_price - entry_price
                unrealized_pct = (unrealized_pnl / entry_price) * 100
                
                if current_price <= stop_loss:
                    should_close = True
                    exit_price = stop_loss
                    exit_reason = 'SL_HIT'
                    if verbose:
                        print(f"  🛑 STOP LOSS HIT!")
                
                elif current_price >= take_profit:
                    should_close = True
                    exit_price = take_profit
                    exit_reason = 'TP_HIT'
                    if verbose:
                        print(f"  🎯 TAKE PROFIT HIT!")
                
                else:
                    if verbose:
                        pnl_sign = '+' if unrealized_pnl >= 0 else ''
                        print(f"  ⏳ Still OPEN | Unrealized P&L: {pnl_sign}${unrealized_pnl:.2f} ({pnl_sign}{unrealized_pct:.2f}%)")
            
            else:  # SHORT
                unrealized_pnl = entry_price - current_price
                unrealized_pct = (unrealized_pnl / entry_price) * 100
                
                if current_price >= stop_loss:
                    should_close = True
                    exit_price = stop_loss
                    exit_reason = 'SL_HIT'
                    if verbose:
                        print(f"  🛑 STOP LOSS HIT!")
                
                elif current_price <= take_profit:
                    should_close = True
                    exit_price = take_profit
                    exit_reason = 'TP_HIT'
                    if verbose:
                        print(f"  🎯 TAKE PROFIT HIT!")
                
                else:
                    if verbose:
                        pnl_sign = '+' if unrealized_pnl >= 0 else ''
                        print(f"  ⏳ Still OPEN | Unrealized P&L: {pnl_sign}${unrealized_pnl:.2f} ({pnl_sign}{unrealized_pct:.2f}%)")
            
            # Close trade if needed
            if should_close:
                db.close_trade(trade_id, exit_price, exit_reason)
                trades_closed += 1
                
                # Get updated trade from DB with correct P&L (including fees)
                conn = __import__('sqlite3').connect(db.db_path)
                conn.row_factory = __import__('sqlite3').Row
                cursor = conn.cursor()
                cursor.execute('SELECT pnl, pnl_percentage, total_fees FROM trades WHERE trade_id = ?', (trade_id,))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    pnl = result['pnl']
                    pnl_pct = result['pnl_percentage']
                    total_fees = result['total_fees']
                    pnl_sign = '+' if pnl >= 0 else ''
                    
                    if verbose:
                        print(f"  ✅ Trade CLOSED")
                        print(f"  Exit: ${exit_price}")
                        print(f"  Fees: ${total_fees:.4f}")
                        print(f"  P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%) [after fees]")
            
            if verbose:
                print()
        
        except Exception as e:
            if verbose:
                print(f"  ❌ Error checking {symbol}: {e}")
                print()
    
    if verbose:
        if trades_closed > 0:
            print(f"{'='*60}")
            print(f"✅ Closed {trades_closed} trade(s)")
            
            # Show updated stats
            stats = db.get_trade_stats()
            print(f"\n📊 Updated Statistics:")
            print(f"   Total: {stats['total_trades']}")
            print(f"   Open: {stats['open_trades']} | Closed: {stats['closed_trades']}")
            if stats['closed_trades'] > 0:
                print(f"   Win rate: {stats['win_rate']:.1f}%")
                print(f"   Total P&L: ${stats['total_pnl']:.2f}")
            print(f"{'='*60}")
        else:
            print(f"{'='*60}")
            print(f"ℹ️  All trades still open")
            print(f"{'='*60}")


def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor and close paper trades automatically')
    parser.add_argument('--continuous', action='store_true', help='Run continuously (check every minute)')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default 60)')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode (only show closures)')
    
    args = parser.parse_args()
    
    # Initialize
    db = TradingDatabase()
    client = BinanceClient()
    
    verbose = not args.quiet
    
    if args.continuous:
        print(f"🔄 Starting continuous monitoring (checking every {args.interval}s)")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            while True:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if verbose:
                    print(f"\n[{timestamp}] Checking trades...")
                
                monitor_open_trades(db, client, verbose)
                
                if verbose:
                    print(f"\nNext check in {args.interval}s...\n")
                
                time.sleep(args.interval)
        
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitoring stopped by user")
    
    else:
        # Single check
        monitor_open_trades(db, client, verbose)


if __name__ == "__main__":
    main()

