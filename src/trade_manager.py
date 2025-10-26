#!/usr/bin/env python
"""Trade Manager CLI - View and manage paper trades"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.database import TradingDatabase
from utils.binance_client import BinanceClient
from datetime import datetime
from openai import OpenAI
import config
import argparse


def list_trades(db: TradingDatabase, status: str = None, strategy: str = None, limit: int = 10):
    """List trades from database"""
    conn = db.conn = __import__('sqlite3').connect(db.db_path)
    conn.row_factory = __import__('sqlite3').Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM trades'
    params = []
    where_parts = []
    
    if status:
        where_parts.append('status = ?')
        params.append(status.upper())
    
    if strategy:
        where_parts.append('strategy = ?')
        params.append(strategy.lower())
    
    if where_parts:
        query += ' WHERE ' + ' AND '.join(where_parts)
    
    query += ' ORDER BY entry_time DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    trades = cursor.fetchall()
    conn.close()
    
    if not trades:
        print("No trades found.")
        return
    
    print(f"\n{'='*100}")
    print(f"📊 TRADES ({status.upper() if status else 'ALL'}) - Last {limit}")
    print(f"{'='*100}\n")
    
    for trade in trades:
        # Strategy indicator
        strategy_badge = "📐" if trade['strategy'] == 'structured' else "🤖"
        
        print(f"{strategy_badge} Trade ID: {trade['trade_id']}")
        print(f"  Strategy: {trade['strategy'].upper()}")
        print(f"  Symbol: {trade['symbol']}")
        print(f"  Action: {trade['action']} | Confidence: {trade['confidence']}")
        print(f"  Entry: ${trade['entry_price']} | SL: ${trade['stop_loss']} | TP: ${trade['take_profit']}")
        print(f"  R/R: 1:{trade['risk_reward_ratio']}")
        print(f"  Setup: {trade['entry_setup']}")
        print(f"  Status: {trade['status']}")
        print(f"  Entry Time: {trade['entry_time']}")
        
        if trade['status'] == 'CLOSED':
            pnl_sign = '+' if trade['pnl'] > 0 else ''
            win_indicator = "✅" if trade['pnl'] > 0 else "❌"
            print(f"  Exit: ${trade['exit_price']} | Reason: {trade['exit_reason']}")
            print(f"  {win_indicator} P&L: {pnl_sign}${trade['pnl']:.2f} ({pnl_sign}{trade['pnl_percentage']:.2f}%)")
        
        print()


def show_stats(db: TradingDatabase, symbol: str = None):
    """Show trading statistics with strategy comparison"""
    # Overall stats
    stats = db.get_trade_stats(symbol)
    
    # Strategy-specific stats
    stats_structured = db.get_trade_stats(symbol, 'structured')
    stats_minimal = db.get_trade_stats(symbol, 'minimal')
    
    print(f"\n{'='*80}")
    print(f"📊 MULTI-STRATEGY TRADING STATISTICS {f'({symbol})' if symbol else '(ALL)'}")
    print(f"{'='*80}\n")
    
    # Overall
    print(f"OVERALL (Valid Trades Only):")
    print(f"  Total Trades: {stats['total_trades']}")
    if stats.get('invalid_trades', 0) > 0:
        print(f"  Invalid (excluded): {stats['invalid_trades']}")
    print(f"  Open: {stats['open_trades']} | Closed: {stats['closed_trades']}")
    
    if stats['closed_trades'] > 0:
        print(f"  Wins: {stats['wins']} | Losses: {stats['losses']}")
        print(f"  Win Rate: {stats['win_rate']:.2f}%")
        print(f"  Total P&L: ${stats['total_pnl']:.2f}")
        print(f"  Cumulative ROI: {stats['cumulative_roi']:.2f}% (on $10k capital)")
        print(f"  Avg P&L: {stats['avg_pnl_percentage']:.2f}%")
        print(f"  Max Streak: {stats['max_consecutive_wins']}W / {stats['max_consecutive_losses']}L")
    
    # Structured strategy
    print(f"\n📐 STRUCTURED STRATEGY (Detailed Prompts):")
    print(f"  Trades: {stats_structured['total_trades']}")
    if stats_structured['closed_trades'] > 0:
        print(f"  Closed: {stats_structured['closed_trades']} ({stats_structured['wins']}W / {stats_structured['losses']}L)")
        print(f"  Win Rate: {stats_structured['win_rate']:.2f}%")
        print(f"  Total P&L: ${stats_structured['total_pnl']:.2f}")
        print(f"  ROI: {stats_structured['cumulative_roi']:.2f}%")
        print(f"  Avg P&L: {stats_structured['avg_pnl_percentage']:.2f}%")
        print(f"  Streak: {stats_structured['max_consecutive_wins']}W / {stats_structured['max_consecutive_losses']}L")
        
        rating_s = "🌟" if stats_structured['win_rate'] >= 60 else "✅" if stats_structured['win_rate'] >= 50 else "⚠️"
        print(f"  Rating: {rating_s}")
    else:
        print(f"  No closed trades yet")
    
    # Minimal strategy
    print(f"\n🤖 MINIMAL STRATEGY (AI Independent):")
    print(f"  Trades: {stats_minimal['total_trades']}")
    if stats_minimal['closed_trades'] > 0:
        print(f"  Closed: {stats_minimal['closed_trades']} ({stats_minimal['wins']}W / {stats_minimal['losses']}L)")
        print(f"  Win Rate: {stats_minimal['win_rate']:.2f}%")
        print(f"  Total P&L: ${stats_minimal['total_pnl']:.2f}")
        print(f"  ROI: {stats_minimal['cumulative_roi']:.2f}%")
        print(f"  Avg P&L: {stats_minimal['avg_pnl_percentage']:.2f}%")
        print(f"  Streak: {stats_minimal['max_consecutive_wins']}W / {stats_minimal['max_consecutive_losses']}L")
        
        rating_m = "🌟" if stats_minimal['win_rate'] >= 60 else "✅" if stats_minimal['win_rate'] >= 50 else "⚠️"
        print(f"  Rating: {rating_m}")
    else:
        print(f"  No closed trades yet")
    
    # Comparison
    if stats_structured['closed_trades'] > 5 and stats_minimal['closed_trades'] > 5:
        print(f"\n🆚 STRATEGY COMPARISON:")
        wr_diff = stats_minimal['win_rate'] - stats_structured['win_rate']
        pnl_diff = stats_minimal['total_pnl'] - stats_structured['total_pnl']
        
        if abs(wr_diff) < 3:
            print(f"  Win Rate: Similar ({wr_diff:+.1f}% difference)")
        elif wr_diff > 0:
            print(f"  Win Rate: MINIMAL better ({wr_diff:+.1f}%) 🤖")
        else:
            print(f"  Win Rate: STRUCTURED better ({-wr_diff:+.1f}%) 📐")
        
        if abs(pnl_diff) < 20:
            print(f"  P&L: Similar (${pnl_diff:+.2f} difference)")
        elif pnl_diff > 0:
            print(f"  P&L: MINIMAL better (${pnl_diff:+.2f}) 🤖")
        else:
            print(f"  P&L: STRUCTURED better (${-pnl_diff:+.2f}) 📐")
    
    print(f"\n{'='*80}\n")


def audit_trades(db: TradingDatabase, symbol: str = None, limit: int = 10):
    """
    Audit closed trades against actual market data to verify correctness
    """
    print(f"\n{'='*80}")
    print(f"🔍 TRADE AUDIT - Verifying against market data")
    print(f"   (Last 7 days only - for data availability)")
    print(f"{'='*80}\n")
    
    # Get closed trades
    conn = __import__('sqlite3').connect(db.db_path)
    conn.row_factory = __import__('sqlite3').Row
    cursor = conn.cursor()
    
    # Only audit recent trades (last 7 days) by default for data availability
    from datetime import datetime as dt, timedelta
    seven_days_ago = (dt.now() - timedelta(days=7)).isoformat()
    
    query = f'SELECT * FROM trades WHERE status = "CLOSED" AND exit_time >= "{seven_days_ago}"'
    if symbol:
        query += f' AND symbol = "{symbol}"'
    query += f' ORDER BY exit_time DESC LIMIT {limit}'
    
    cursor.execute(query)
    trades = cursor.fetchall()
    conn.close()
    
    if not trades:
        print("No closed trades to audit.")
        return
    
    print(f"Auditing last {len(trades)} closed trades...\n")
    
    client = BinanceClient()
    audit_results = []
    
    for trade in trades:
        trade_id = trade['trade_id']
        symbol = trade['symbol']
        action = trade['action']
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        entry_price = trade['entry_price']
        exit_price = trade['exit_price']
        exit_reason = trade['exit_reason']
        stop_loss = trade['stop_loss']
        take_profit = trade['take_profit']
        pnl = trade['pnl']
        strategy = trade['strategy']
        
        print(f"{'─'*80}")
        print(f"Trade: {trade_id}")
        print(f"Strategy: {strategy.upper()} | {action} @ ${entry_price}")
        print(f"Entry: {entry_time[:19]}")
        print(f"Exit: {exit_time[:19]} ({exit_reason})")
        print(f"Recorded Exit Price: ${exit_price}")
        print(f"SL: ${stop_loss} | TP: ${take_profit}")
        print(f"Recorded P&L: ${pnl:.2f}")
        
        try:
            # Use 15m candles (better history availability)
            from datetime import datetime as dt, timedelta
            entry_dt = dt.fromisoformat(entry_time)
            exit_dt = dt.fromisoformat(exit_time)
            
            # Get 15m candles from entry to now (should cover the trade duration)
            klines = client.get_klines(symbol, '15m', limit=500)
            
            # Find candles during trade duration
            relevant_candles = []
            for idx, row in klines.iterrows():
                candle_time = row['timestamp']
                # Candle is relevant if it's between entry and exit (+/- buffer)
                if (candle_time >= entry_dt - timedelta(minutes=30) and 
                    candle_time <= exit_dt + timedelta(minutes=30)):
                    relevant_candles.append(row)
            
            if len(relevant_candles) > 0:
                # Get highest high and lowest low during trade
                max_high = max(c['high'] for c in relevant_candles)
                min_low = min(c['low'] for c in relevant_candles)
                
                print(f"\nMarket data verification (15m candles):")
                print(f"  Candles during trade: {len(relevant_candles)}")
                print(f"  Highest: ${max_high:.2f} | Lowest: ${min_low:.2f}")
                print(f"  Trade duration: {entry_time[:16]} → {exit_time[:16]}")
                
                # Verify SL/TP hit (Priority: SL first, then TP)
                verified = False
                verification_msg = ""
                
                if action == 'LONG':
                    # Check SL first (priority)
                    sl_hit = min_low <= stop_loss
                    tp_hit = max_high >= take_profit
                    
                    if exit_reason == 'SL_HIT':
                        if sl_hit:
                            verified = True
                            verification_msg = f"✅ SL verified: Lowest ${min_low:.2f} <= SL ${stop_loss:.2f}"
                        else:
                            verified = False
                            verification_msg = f"❌ SL NOT reached: Lowest ${min_low:.2f} > SL ${stop_loss:.2f}"
                    
                    elif exit_reason == 'TP_HIT':
                        # Check if SL was hit first (should have closed there)
                        if sl_hit and not tp_hit:
                            verified = False
                            verification_msg = f"❌ ERROR: SL hit first (${min_low:.2f}), but trade shows TP_HIT"
                        elif tp_hit:
                            verified = True
                            verification_msg = f"✅ TP verified: Highest ${max_high:.2f} >= TP ${take_profit:.2f}"
                        else:
                            verified = False
                            verification_msg = f"❌ TP NOT reached: Highest ${max_high:.2f} < TP ${take_profit:.2f}"
                
                else:  # SHORT
                    # Check SL first (priority)
                    sl_hit = max_high >= stop_loss
                    tp_hit = min_low <= take_profit
                    
                    if exit_reason == 'SL_HIT':
                        if sl_hit:
                            verified = True
                            verification_msg = f"✅ SL verified: Highest ${max_high:.2f} >= SL ${stop_loss:.2f}"
                        else:
                            verified = False
                            verification_msg = f"❌ SL NOT reached: Highest ${max_high:.2f} < SL ${stop_loss:.2f}"
                    
                    elif exit_reason == 'TP_HIT':
                        # Check if SL was hit first
                        if sl_hit and not tp_hit:
                            verified = False
                            verification_msg = f"❌ ERROR: SL hit first (${max_high:.2f}), but trade shows TP_HIT"
                        elif tp_hit:
                            verified = True
                            verification_msg = f"✅ TP verified: Lowest ${min_low:.2f} <= TP ${take_profit:.2f}"
                        else:
                            verified = False
                            verification_msg = f"❌ TP NOT reached: Lowest ${min_low:.2f} > TP ${take_profit:.2f}"
                
                print(f"  {verification_msg}")
                
                # Mark as invalid if verification failed
                if not verified:
                    db.mark_trade_invalid(trade_id, f"Audit failed: {verification_msg}")
                    print(f"  🚫 Trade marked as INVALID in database")
                
                # Check P&L accuracy
                if action == 'LONG':
                    expected_pnl = exit_price - entry_price
                else:
                    expected_pnl = entry_price - exit_price
                
                pnl_correct = abs(pnl - expected_pnl) < 0.01
                if pnl_correct:
                    print(f"  ✅ P&L calculation correct: ${pnl:.2f}")
                else:
                    print(f"  ❌ P&L mismatch: Recorded ${pnl:.2f} vs Expected ${expected_pnl:.2f}")
                
                audit_results.append({
                    "trade_id": trade_id,
                    "strategy": strategy,
                    "verified": verified,
                    "pnl_correct": pnl_correct,
                    "exit_reason": exit_reason,
                    "market_data": {
                        "high": float(max_high),
                        "low": float(min_low),
                        "candles": len(relevant_candles)
                    },
                    "trade_data": {
                        "entry": entry_price,
                        "exit": exit_price,
                        "sl": stop_loss,
                        "tp": take_profit,
                        "pnl": pnl
                    }
                })
            else:
                print(f"  ⚠️  Could not find market data for exit time")
                audit_results.append({
                    "trade_id": trade_id,
                    "strategy": strategy,
                    "verified": None,
                    "pnl_correct": None,
                    "error": "No market data found"
                })
        
        except Exception as e:
            print(f"  ❌ Audit error: {e}")
            audit_results.append({
                "trade_id": trade_id,
                "strategy": strategy,
                "verified": None,
                "error": str(e)
            })
        
        print()
    
    # LLM-powered audit summary
    print(f"\n{'='*80}")
    print(f"🤖 AI-POWERED AUDIT SUMMARY")
    print(f"{'='*80}\n")
    
    try:
        # Prepare audit summary for LLM
        verified_count = sum(1 for r in audit_results if r.get('verified') == True)
        failed_count = sum(1 for r in audit_results if r.get('verified') == False)
        error_count = sum(1 for r in audit_results if r.get('verified') is None)
        
        # Call DeepSeek for audit analysis
        client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL
        )
        
        audit_summary = f"""Audit Results for {len(trades)} closed trades:

VERIFICATION SUMMARY:
- Verified correct: {verified_count}/{len(trades)}
- Failed verification: {failed_count}/{len(trades)}
- Could not verify: {error_count}/{len(trades)}

DETAILED RESULTS:
{chr(10).join([f"- {r['trade_id']}: {r.get('exit_reason', 'N/A')} - {'✅ Verified' if r.get('verified') else '❌ Failed' if r.get('verified') == False else '⚠️ No data'}" for r in audit_results[:10]])}

TASK:
Analyze this audit and provide:
1. Overall assessment (is the trading system working correctly?)
2. Any concerns or red flags
3. Recommendations for improvement
4. Confidence in the system's reliability

Be concise (3-4 sentences)."""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a trading system auditor. Analyze trade execution accuracy and system reliability."},
                {"role": "user", "content": audit_summary}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        ai_assessment = response.choices[0].message.content.strip()
        
        print("🤖 DeepSeek AI Assessment:")
        print(f"{ai_assessment}\n")
        
        print(f"{'='*80}\n")
        print(f"📊 Audit Summary:")
        print(f"  Total audited: {len(trades)}")
        print(f"  ✅ Verified: {verified_count}")
        print(f"  ❌ Failed: {failed_count}")
        print(f"  ⚠️  No data: {error_count}")
        
        accuracy = (verified_count / (verified_count + failed_count) * 100) if (verified_count + failed_count) > 0 else 0
        print(f"  Accuracy: {accuracy:.1f}%")
        
        if accuracy >= 95:
            print(f"  Status: 🌟 Excellent - System highly reliable")
        elif accuracy >= 80:
            print(f"  Status: ✅ Good - System working well")
        elif accuracy >= 60:
            print(f"  Status: ⚠️  Fair - Some issues detected")
        else:
            print(f"  Status: ❌ Poor - System needs attention")
        
    except Exception as e:
        print(f"⚠️  Could not generate AI assessment: {e}")
    
    print(f"\n{'='*80}\n")


def close_trade_manual(db: TradingDatabase, trade_id: str, exit_price: float, reason: str = "MANUAL"):
    """Manually close a trade"""
    try:
        db.close_trade(trade_id, exit_price, reason)
        
        # Get trade details with correct P&L (including fees)
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
            
            print(f"✅ Trade {trade_id} closed at ${exit_price}")
            print(f"   Reason: {reason}")
            print(f"   Fees: ${total_fees:.4f}")
            print(f"   P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%) [after fees]")
        else:
            print(f"✅ Trade {trade_id} closed at ${exit_price}")
            print(f"   Reason: {reason}")
    except Exception as e:
        print(f"❌ Error closing trade: {e}")


def check_open_trades(db: TradingDatabase, current_prices: dict):
    """Check open trades against current prices and close if SL/TP hit"""
    open_trades = db.get_open_trades()
    
    if not open_trades:
        print("No open trades to check.")
        return
    
    print(f"\n{'='*60}")
    print(f"🔍 CHECKING OPEN TRADES")
    print(f"{'='*60}\n")
    
    for trade in open_trades:
        symbol = trade['symbol']
        if symbol not in current_prices:
            print(f"⏩ {trade['trade_id']}: No price data for {symbol}")
            continue
        
        current_price = current_prices[symbol]
        action = trade['action']
        stop_loss = trade['stop_loss']
        take_profit = trade['take_profit']
        
        print(f"Trade: {trade['trade_id']}")
        print(f"  {action} @ ${trade['entry_price']}")
        print(f"  Current: ${current_price}")
        
        # Check if SL or TP hit
        if action == 'LONG':
            if current_price <= stop_loss:
                print(f"  🛑 STOP LOSS HIT!")
                db.close_trade(trade['trade_id'], stop_loss, 'SL_HIT')
            elif current_price >= take_profit:
                print(f"  🎯 TAKE PROFIT HIT!")
                db.close_trade(trade['trade_id'], take_profit, 'TP_HIT')
            else:
                unrealized = current_price - trade['entry_price']
                print(f"  ⏳ Open (Unrealized: ${unrealized:.2f})")
        else:  # SHORT
            if current_price >= stop_loss:
                print(f"  🛑 STOP LOSS HIT!")
                db.close_trade(trade['trade_id'], stop_loss, 'SL_HIT')
            elif current_price <= take_profit:
                print(f"  🎯 TAKE PROFIT HIT!")
                db.close_trade(trade['trade_id'], take_profit, 'TP_HIT')
            else:
                unrealized = trade['entry_price'] - current_price
                print(f"  ⏳ Open (Unrealized: ${unrealized:.2f})")
        
        print()


def main():
    """CLI main function"""
    parser = argparse.ArgumentParser(description='Paper Trading Manager')
    parser.add_argument('command', choices=['list', 'stats', 'close', 'check', 'compare', 'audit'],
                       help='Command to execute')
    parser.add_argument('--status', choices=['open', 'closed'], help='Filter by status')
    parser.add_argument('--strategy', choices=['structured', 'minimal', 'macro', 'intraday', 'intraday2'], help='Filter by strategy')
    parser.add_argument('--symbol', help='Filter by symbol')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of results')
    parser.add_argument('--trade-id', help='Trade ID for close command')
    parser.add_argument('--price', type=float, help='Exit price for close command')
    
    args = parser.parse_args()
    
    db = TradingDatabase()
    
    if args.command == 'list':
        list_trades(db, args.status, args.strategy, args.limit)
    
    elif args.command == 'stats':
        show_stats(db, args.symbol)
    
    elif args.command == 'close':
        if not args.trade_id or args.price is None:
            print("❌ Error: --trade-id and --price required for close command")
            sys.exit(1)
        close_trade_manual(db, args.trade_id, args.price)
    
    elif args.command == 'compare':
        # Compare strategies side-by-side
        print("\n" + "="*80)
        print("🆚 STRATEGY COMPARISON")
        print("="*80 + "\n")
        
        stats_s = db.get_trade_stats(args.symbol, 'structured')
        stats_m = db.get_trade_stats(args.symbol, 'minimal')
        
        print(f"{'Metric':<25} {'STRUCTURED':<20} {'MINIMAL':<20} {'Winner':<15}")
        print("-" * 80)
        
        # Total trades
        print(f"{'Total Trades':<25} {stats_s['total_trades']:<20} {stats_m['total_trades']:<20}")
        print(f"{'Closed Trades':<25} {stats_s['closed_trades']:<20} {stats_m['closed_trades']:<20}")
        
        if stats_s['closed_trades'] > 0 and stats_m['closed_trades'] > 0:
            # Win rate
            wr_winner = "MINIMAL 🤖" if stats_m['win_rate'] > stats_s['win_rate'] else "STRUCTURED 📐" if stats_s['win_rate'] > stats_m['win_rate'] else "TIE"
            print(f"{'Win Rate':<25} {stats_s['win_rate']:.1f}%{'':<16} {stats_m['win_rate']:.1f}%{'':<16} {wr_winner:<15}")
            
            # Total P&L
            pnl_winner = "MINIMAL 🤖" if stats_m['total_pnl'] > stats_s['total_pnl'] else "STRUCTURED 📐" if stats_s['total_pnl'] > stats_m['total_pnl'] else "TIE"
            print(f"{'Total P&L':<25} ${stats_s['total_pnl']:.2f}{'':<14} ${stats_m['total_pnl']:.2f}{'':<14} {pnl_winner:<15}")
            
            # ROI
            roi_winner = "MINIMAL 🤖" if stats_m['cumulative_roi'] > stats_s['cumulative_roi'] else "STRUCTURED 📐" if stats_s['cumulative_roi'] > stats_m['cumulative_roi'] else "TIE"
            print(f"{'Cumulative ROI':<25} {stats_s['cumulative_roi']:.2f}%{'':<16} {stats_m['cumulative_roi']:.2f}%{'':<16} {roi_winner:<15}")
            
            # Avg P&L
            avg_winner = "MINIMAL 🤖" if stats_m['avg_pnl_percentage'] > stats_s['avg_pnl_percentage'] else "STRUCTURED 📐"
            print(f"{'Avg P&L':<25} {stats_s['avg_pnl_percentage']:.2f}%{'':<16} {stats_m['avg_pnl_percentage']:.2f}%{'':<16} {avg_winner:<15}")
            
            # Streaks
            print(f"{'Max Win Streak':<25} {stats_s['max_consecutive_wins']:<20} {stats_m['max_consecutive_wins']:<20}")
            print(f"{'Max Loss Streak':<25} {stats_s['max_consecutive_losses']:<20} {stats_m['max_consecutive_losses']:<20}")
        
        print("\n" + "="*80 + "\n")
    
    elif args.command == 'audit':
        # Audit closed trades against market data
        audit_trades(db, args.symbol, args.limit or 10)
    
    elif args.command == 'check':
        # For check command, you'd need to fetch current prices
        print("Check command requires live price feed.")
        print("Use this in a script with binance client.")


if __name__ == "__main__":
    main()

