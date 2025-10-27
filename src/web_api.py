"""Web API for Trading Dashboard"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from utils.database import TradingDatabase
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import requests
import config

app = Flask(__name__, static_folder='../web', static_url_path='')
CORS(app)

db = TradingDatabase()


@app.route('/')
def index():
    """Serve main dashboard"""
    return send_from_directory('../web', 'index.html')


@app.route('/logs')
def logs():
    """Serve strategy logs page"""
    return send_from_directory('../web', 'logs.html')


@app.route('/strategy')
def strategy():
    """Serve strategy detail page"""
    return send_from_directory('../web', 'strategy.html')


@app.route('/api/stats')
def get_stats():
    """Get overall and per-strategy statistics"""
    symbol = request.args.get('symbol')
    
    stats_all = db.get_trade_stats(symbol)
    stats_structured = db.get_trade_stats(symbol, 'structured')
    stats_minimal = db.get_trade_stats(symbol, 'minimal')
    stats_minimalbtc = db.get_trade_stats(symbol, 'minimalbtc')
    stats_macro = db.get_trade_stats(symbol, 'macro')
    stats_intraday = db.get_trade_stats(symbol, 'intraday')
    stats_intraday2 = db.get_trade_stats(symbol, 'intraday2')
    
    return jsonify({
        'overall': stats_all,
        'strategies': {
            'structured': stats_structured,
            'minimal': stats_minimal,
            'minimalbtc': stats_minimalbtc,
            'macro': stats_macro,
            'intraday': stats_intraday,
            'intraday2': stats_intraday2
        }
    })


@app.route('/api/trades')
def get_trades():
    """Get trades with filtering and live P&L for open positions"""
    status = request.args.get('status')  # open, closed
    strategy = request.args.get('strategy')  # structured, minimal, minimalbtc, macro, intraday, intraday2
    limit = int(request.args.get('limit', 50))
    
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM trades WHERE valid = 1'
    params = []
    
    if status:
        query += ' AND status = ?'
        params.append(status.upper())
    
    if strategy:
        query += ' AND strategy = ?'
        params.append(strategy.lower())
    
    query += ' ORDER BY entry_time DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    trades = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Calculate live P&L for open positions
    open_trades = [t for t in trades if t['status'] == 'OPEN']
    if open_trades:
        # Get unique symbols
        symbols = list(set(t['symbol'] for t in open_trades))
        
        # Fetch current prices from Binance
        try:
            from utils.binance_client import BinanceClient
            client = BinanceClient()
            current_prices = {}
            
            for symbol in symbols:
                try:
                    ticker = client.client.get_symbol_ticker(symbol=symbol)
                    current_prices[symbol] = float(ticker['price'])
                except:
                    current_prices[symbol] = None
            
            # Calculate live P&L for each open trade
            for trade in trades:
                if trade['status'] == 'OPEN' and trade['symbol'] in current_prices:
                    current_price = current_prices[trade['symbol']]
                    if current_price:
                        entry_price = trade['entry_price']
                        
                        # Calculate P&L based on direction
                        if trade['action'] == 'LONG':
                            pnl_pct = ((current_price - entry_price) / entry_price) * 100
                            pnl_dollars = current_price - entry_price
                        else:  # SHORT
                            pnl_pct = ((entry_price - current_price) / entry_price) * 100
                            pnl_dollars = entry_price - current_price
                        
                        # Add live P&L to trade data (both $ and %)
                        trade['live_pnl_percentage'] = round(pnl_pct, 2)
                        trade['live_pnl_dollars'] = round(pnl_dollars, 2)
                        trade['current_price'] = round(current_price, 2)
        except Exception as e:
            print(f"Error calculating live P&L: {e}")
    
    return jsonify({'trades': trades, 'count': len(trades)})


@app.route('/api/chart-data')
def get_chart_data():
    """Get price and portfolio data for chart (with optional strategy filter)"""
    from utils.binance_client import BinanceClient
    from datetime import datetime, timedelta
    
    strategy = request.args.get('strategy')  # Optional filter by strategy
    
    try:
        # Get SOLUSDT price history (last 48 hours, 2h intervals for cleaner chart)
        client = BinanceClient()
        klines = client.client.get_klines(
            symbol='SOLUSDT',
            interval='2h',
            limit=24
        )
        
        # Extract timestamps and prices
        price_data = []
        
        for kline in klines:
            timestamp_ms = kline[0]
            close_price = float(kline[4])
            price_data.append({
                'timestamp': timestamp_ms,
                'datetime': datetime.fromtimestamp(timestamp_ms / 1000),
                'price': close_price
            })
        
        # Add current time point to capture recent trades
        current_ticker = client.client.get_symbol_ticker(symbol='SOLUSDT')
        current_price = float(current_ticker['price'])
        current_time = datetime.now()
        
        price_data.append({
            'timestamp': int(current_time.timestamp() * 1000),
            'datetime': current_time,
            'price': current_price
        })
        
        # Get closed trades ordered by exit_time (with optional strategy filter)
        conn = sqlite3.connect(db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT exit_time, pnl 
            FROM trades 
            WHERE status = 'CLOSED' AND valid = 1
        """
        params = []
        
        if strategy:
            query += " AND strategy = ?"
            params.append(strategy.lower())
        
        query += " ORDER BY exit_time ASC"
        
        cursor.execute(query, params)
        
        closed_trades = cursor.fetchall()
        conn.close()
        
        # Build portfolio timeline aligned with price data
        starting_capital = 10000
        timestamps = []
        prices = []
        portfolio_values = []
        
        current_portfolio = starting_capital
        counted_trade_times = set()
        
        for price_point in price_data:
            chart_time = price_point['datetime']
            
            # Add P&L from all trades that closed before this timestamp
            for trade in closed_trades:
                if trade['exit_time']:
                    trade_time_str = trade['exit_time']
                    # Handle 'Z' suffix (Python < 3.11 doesn't support it in fromisoformat)
                    trade_time_str_clean = trade_time_str.replace('Z', '+00:00')
                    trade_time = datetime.fromisoformat(trade_time_str_clean)
                    
                    # Make chart_time timezone-aware for comparison (assume UTC)
                    if chart_time.tzinfo is None:
                        from datetime import timezone
                        chart_time_aware = chart_time.replace(tzinfo=timezone.utc)
                    else:
                        chart_time_aware = chart_time
                    
                    # If trade closed before this chart point and not yet counted
                    if trade_time <= chart_time_aware and trade_time_str not in counted_trade_times:
                        current_portfolio += trade['pnl']
                        counted_trade_times.add(trade_time_str)
            
            # Format timestamp for display
            timestamps.append(chart_time.strftime('%m/%d %H:%M'))
            prices.append(price_point['price'])
            portfolio_values.append(round(current_portfolio, 2))
        
        return jsonify({
            'timestamps': timestamps,
            'prices': prices,
            'portfolio': portfolio_values,
            'starting_capital': starting_capital
        })
        
    except Exception as e:
        print(f"Error generating chart data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'timestamps': [],
            'prices': [],
            'portfolio': [],
            'error': str(e)
        })


@app.route('/api/bot-status')
def get_bot_status():
    """Check if bot is running (supports both dynamic and legacy bot)"""
    import subprocess
    try:
        # Try dynamic bot first (recommended)
        result = subprocess.run(['pgrep', '-f', 'trading_bot_dynamic.py'], 
                              capture_output=True, text=True)
        
        # If not found, try legacy bot
        if not result.stdout.strip():
            result = subprocess.run(['pgrep', '-f', 'trading_bot.py'], 
                                  capture_output=True, text=True)
        
        is_running = bool(result.stdout.strip())
        pid = result.stdout.strip() if is_running else None
        
        return jsonify({
            'running': is_running,
            'pid': pid
        })
    except:
        return jsonify({'running': False, 'pid': None})


@app.route('/api/strategy-runs')
def get_strategy_runs():
    """Get strategy execution logs"""
    strategy = request.args.get('strategy')
    limit = int(request.args.get('limit', 100))
    
    runs = db.get_strategy_runs(strategy=strategy, limit=limit)
    
    # Parse JSON fields
    for run in runs:
        run['key_factors'] = json.loads(run['key_factors']) if run['key_factors'] else []
        run['market_data'] = json.loads(run['market_data']) if run['market_data'] else {}
        run['risk_management'] = json.loads(run['risk_management']) if run['risk_management'] else {}
    
    return jsonify({'runs': runs, 'count': len(runs)})


@app.route('/api/close-trade/<trade_id>', methods=['POST'])
def close_trade_api(trade_id):
    """Close an open trade at current market price"""
    try:
        from utils.binance_client import BinanceClient
        import sqlite3
        
        # Check if trade exists and is open
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT status, symbol, action, entry_price FROM trades WHERE trade_id = ?', (trade_id,))
        trade = cursor.fetchone()
        conn.close()
        
        if not trade:
            return jsonify({'error': 'Trade not found'}), 404
        
        status, symbol, action, entry_price = trade
        
        if status == 'CLOSED':
            return jsonify({'error': 'Trade is already closed'}), 400
        
        # Get current market price
        client = BinanceClient()
        current_price = client.get_current_price(symbol)
        
        # Close trade using database function (handles P&L calculation with fees)
        db.close_trade(
            trade_id=trade_id,
            exit_price=current_price,
            exit_reason='MANUAL_CLOSE'
        )
        
        # Calculate P&L percentage for response (before fees for display)
        if action == 'LONG':
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Get actual P&L after fees from database
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT pnl, pnl_percentage FROM trades WHERE trade_id = ?', (trade_id,))
        result = cursor.fetchone()
        conn.close()
        
        actual_pnl, actual_pnl_pct = result if result else (0, 0)
        
        return jsonify({
            'success': True,
            'message': f'Trade {trade_id} closed successfully',
            'exit_price': current_price,
            'pnl': actual_pnl,
            'pnl_percentage': actual_pnl_pct
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/trades/<trade_id>', methods=['DELETE'])
def delete_trade(trade_id):
    """Delete a trade from database"""
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Check if trade exists
        cursor.execute('SELECT * FROM trades WHERE trade_id = ?', (trade_id,))
        trade = cursor.fetchone()
        
        if not trade:
            conn.close()
            return jsonify({'error': 'Trade not found'}), 404
        
        # Delete the trade
        cursor.execute('DELETE FROM trades WHERE trade_id = ?', (trade_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Trade {trade_id} deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/strategy-detail')
def get_strategy_detail():
    """Get comprehensive strategy analysis"""
    strategy = request.args.get('strategy', 'minimal')
    
    try:
        conn = sqlite3.connect(db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all closed trades for this strategy (for analysis)
        cursor.execute("""
            SELECT *  FROM trades
            WHERE strategy = ? AND status = 'CLOSED' AND valid = 1
            ORDER BY exit_time ASC
        """, (strategy,))
        
        trades = cursor.fetchall()
        
        if len(trades) == 0:
            conn.close()
            return jsonify({'error': 'No trades found for this strategy'})
        
        # Calculate KPIs
        wins = sum(1 for t in trades if t['pnl'] > 0)
        losses = sum(1 for t in trades if t['pnl'] < 0)
        total_trades = len(trades)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in trades)
        starting_capital = 10000
        pnl_percent = (total_pnl / starting_capital * 100)
        
        total_wins_amount = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        total_losses_amount = sum(abs(t['pnl']) for t in trades if t['pnl'] < 0)
        profit_factor = (total_wins_amount / total_losses_amount) if total_losses_amount > 0 else 'N/A'
        if isinstance(profit_factor, float):
            profit_factor = f"{profit_factor:.2f}"
        
        avg_win = (total_wins_amount / wins) if wins > 0 else 0
        avg_loss = -(total_losses_amount / losses) if losses > 0 else 0
        
        # Calculate average win/loss percentages
        win_trades = [t for t in trades if t['pnl'] > 0]
        loss_trades = [t for t in trades if t['pnl'] < 0]
        avg_win_percent = (sum(t['pnl_percentage'] for t in win_trades) / len(win_trades)) if win_trades else 0
        avg_loss_percent = (sum(t['pnl_percentage'] for t in loss_trades) / len(loss_trades)) if loss_trades else 0
        
        # Calculate average duration
        durations = []
        for t in trades:
            if t['entry_time'] and t['exit_time']:
                try:
                    entry_clean = t['entry_time'].replace('Z', '+00:00')
                    exit_clean = t['exit_time'].replace('Z', '+00:00')
                    entry = datetime.fromisoformat(entry_clean)
                    exit = datetime.fromisoformat(exit_clean)
                    duration = (exit - entry).total_seconds() / 3600  # hours
                    durations.append(duration)
                except:
                    pass
        avg_duration = f"{sum(durations) / len(durations):.1f}h" if durations else "N/A"
        
        # Calculate additional trading ratios
        import math
        
        # Sharpe Ratio (simplified - assuming 0% risk-free rate)
        if total_trades > 1:
            pnl_list = [t['pnl'] for t in trades]
            mean_pnl = sum(pnl_list) / len(pnl_list)
            variance = sum((x - mean_pnl) ** 2 for x in pnl_list) / (len(pnl_list) - 1)
            std_dev = math.sqrt(variance)
            sharpe = (mean_pnl / std_dev * math.sqrt(252)) if std_dev > 0 else 0  # Annualized
            sharpe_ratio = f"{sharpe:.2f}"
        else:
            sharpe_ratio = "N/A"
        
        # Sortino Ratio (only downside deviation)
        if total_trades > 1:
            pnl_list = [t['pnl'] for t in trades]
            mean_pnl = sum(pnl_list) / len(pnl_list)
            downside_returns = [x for x in pnl_list if x < 0]
            if downside_returns:
                downside_var = sum(x ** 2 for x in downside_returns) / len(downside_returns)
                downside_std = math.sqrt(downside_var)
                sortino = (mean_pnl / downside_std * math.sqrt(252)) if downside_std > 0 else 0
                sortino_ratio = f"{sortino:.2f}"
            else:
                sortino_ratio = "∞"  # No losses
        else:
            sortino_ratio = "N/A"
        
        # Calmar Ratio (Return / Max Drawdown)
        # Calculate max drawdown first
        peak = starting_capital
        max_dd = 0
        current = starting_capital
        for t in trades:
            current += t['pnl']
            if current > peak:
                peak = current
            dd = ((peak - current) / peak * 100) if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        if max_dd > 0:
            calmar = (pnl_percent / max_dd)
            calmar_ratio = f"{calmar:.2f}"
        else:
            calmar_ratio = "N/A"
        
        # Expectancy (Expected value per trade)
        expectancy = (win_rate / 100 * avg_win) + ((100 - win_rate) / 100 * avg_loss)
        
        # Kelly Criterion %
        if losses > 0 and avg_loss != 0:
            win_prob = win_rate / 100
            loss_prob = 1 - win_prob
            kelly = (win_prob / abs(avg_loss)) - (loss_prob / avg_win) if avg_win > 0 else 0
            kelly_percent = max(0, min(kelly * 100, 100))  # Cap at 0-100%
            kelly_percent = f"{kelly_percent:.1f}"
        else:
            kelly_percent = "N/A"
        
        # Payoff Ratio (Avg Win / Avg Loss)
        if avg_loss != 0:
            payoff = avg_win / abs(avg_loss)
            payoff_ratio = f"{payoff:.2f}"
        else:
            payoff_ratio = "N/A"
        
        # Calculate risk metrics here for KPIs
        best_trade = max(t['pnl'] for t in trades) if trades else 0
        worst_trade = min(t['pnl'] for t in trades) if trades else 0
        total_fees = sum(t['total_fees'] or 0 for t in trades)
        
        # Calculate win/loss streaks
        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for t in trades:
            if t['pnl'] > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            elif t['pnl'] < 0:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
        
        kpis = {
            'win_rate': round(win_rate, 1),
            'wins': wins,
            'losses': losses,
            'total_pnl': round(total_pnl, 2),
            'pnl_percent': round(pnl_percent, 2),
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'avg_duration': avg_duration,
            'avg_win': round(avg_win, 2),
            'avg_win_percent': f"{avg_win_percent:.2f}",
            'avg_loss': round(avg_loss, 2),
            'avg_loss_percent': f"{avg_loss_percent:.2f}",
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'expectancy': f"{expectancy:.2f}",
            'kelly_percent': kelly_percent,
            'payoff_ratio': payoff_ratio,
            # Risk metrics
            'max_drawdown': f"{max_dd:.2f}%",
            'best_trade': f"${best_trade:.2f}",
            'worst_trade': f"${worst_trade:.2f}",
            'avg_hold_time': avg_duration,
            'total_fees': f"${total_fees:.2f}",
            'win_streak': max_win_streak,
            'loss_streak': max_loss_streak
        }
        
        # Build equity curve
        equity_labels = []
        equity_values = []
        current_equity = starting_capital
        
        for t in trades:
            try:
                exit_clean = t['exit_time'].replace('Z', '+00:00')
                exit_time = datetime.fromisoformat(exit_clean)
                equity_labels.append(exit_time.strftime('%m/%d %H:%M'))
                current_equity += t['pnl']
                equity_values.append(round(current_equity, 2))
            except:
                pass
        
        equity = {
            'labels': equity_labels,
            'values': equity_values
        }
        
        # P&L Distribution (histogram)
        pnl_buckets = defaultdict(int)
        for t in trades:
            pnl = t['pnl']
            # Create buckets of $0.50
            bucket = round(pnl / 0.5) * 0.5
            pnl_buckets[bucket] += 1
        
        sorted_buckets = sorted(pnl_buckets.items())
        pnl_dist = {
            'labels': [f"${k:.2f}" for k, v in sorted_buckets],
            'values': [v for k, v in sorted_buckets],
            'colors': ['#ef4444' if k < 0 else '#10b981' for k, v in sorted_buckets]
        }
        
        # Hourly Performance
        hourly_pnl = defaultdict(float)
        for t in trades:
            try:
                entry_clean = t['entry_time'].replace('Z', '+00:00')
                entry_time = datetime.fromisoformat(entry_clean)
                hour = entry_time.hour
                hourly_pnl[hour] += t['pnl']
            except:
                pass
        
        hourly = {
            'labels': [f"{h:02d}:00" for h in range(24)],
            'values': [round(hourly_pnl.get(h, 0), 2) for h in range(24)],
            'colors': ['#ef4444' if hourly_pnl.get(h, 0) < 0 else '#10b981' for h in range(24)]
        }
        
        # Risk Metrics
        best_trade = max(t['pnl'] for t in trades)
        worst_trade = min(t['pnl'] for t in trades)
        
        # Max drawdown
        peak = starting_capital
        max_dd = 0
        current = starting_capital
        for t in trades:
            current += t['pnl']
            if current > peak:
                peak = current
            dd = ((peak - current) / peak * 100) if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        # Win/Loss streaks
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        for t in trades:
            if t['pnl'] > 0:
                if current_streak >= 0:
                    current_streak += 1
                else:
                    current_streak = 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                if current_streak <= 0:
                    current_streak -= 1
                else:
                    current_streak = -1
                max_loss_streak = max(max_loss_streak, abs(current_streak))
        
        total_fees = sum(t['total_fees'] if t['total_fees'] else 0 for t in trades)
        
        recovery_factor = (total_pnl / max_dd) if max_dd > 0 else 'N/A'
        if isinstance(recovery_factor, float):
            recovery_factor = f"{recovery_factor:.2f}"
        
        risk_metrics = {
            'max_drawdown': f"{max_dd:.2f}%",
            'best_trade': f"${best_trade:.2f}",
            'worst_trade': f"${worst_trade:.2f}",
            'avg_hold_time': avg_duration,
            'total_fees': f"${total_fees:.2f}",
            'win_streak': max_win_streak,
            'loss_streak': max_loss_streak,
            'recovery_factor': recovery_factor
        }
        
        # Recent trades (last 10) - get ALL trades (OPEN + CLOSED) to match index filter
        cursor.execute("""
            SELECT * FROM trades
            WHERE strategy = ? AND valid = 1
            ORDER BY entry_time DESC
            LIMIT 10
        """, (strategy,))
        recent_trades_raw = cursor.fetchall()
        
        recent = []
        for t in recent_trades_raw:
            try:
                entry_clean = t['entry_time'].replace('Z', '+00:00')
                entry_time = datetime.fromisoformat(entry_clean)
                
                # For CLOSED trades, show exit time and P&L
                if t['status'] == 'CLOSED' and t['exit_time']:
                    exit_clean = t['exit_time'].replace('Z', '+00:00')
                    exit_time = datetime.fromisoformat(exit_clean)
                    recent.append({
                        'entry_time': entry_time.strftime('%m/%d %H:%M'),
                        'exit_time': exit_time.strftime('%m/%d %H:%M'),
                        'action': t['action'],
                        'pnl': round(t['pnl'], 2)
                    })
                else:
                    # For OPEN trades, show "OPEN" as exit
                    recent.append({
                        'entry_time': entry_time.strftime('%m/%d %H:%M'),
                        'exit_time': 'OPEN',
                        'action': t['action'],
                        'pnl': 0  # Open trade, no P&L yet
                    })
            except Exception as e:
                print(f"Error parsing trade: {e}")
                pass
        
        conn.close()
        
        return jsonify({
            'kpis': kpis,
            'equity': equity,
            'pnl_distribution': pnl_dist,
            'hourly_performance': hourly,
            'risk_metrics': risk_metrics,
            'recent_trades': recent
        })
        
    except Exception as e:
        print(f"Error generating strategy detail: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategy-ai-analysis/<strategy_name>')
def get_strategy_ai_analysis(strategy_name):
    """Get AI analysis of strategy performance metrics using DeepSeek"""
    try:
        # Get trades for this strategy
        conn = sqlite3.connect(db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trades
            WHERE strategy = ? AND status = 'CLOSED' AND valid = 1
            ORDER BY exit_time ASC
        """, (strategy_name,))
        
        trades = cursor.fetchall()
        conn.close()
        
        if len(trades) == 0:
            return jsonify({
                'success': False,
                'analysis': 'Insufficient data for analysis. No trades found for this strategy.'
            })
        
        # Load decision code for this strategy
        decision_code = ""
        decision_file = f"agents/decision_{strategy_name}.py"
        decision_path = os.path.join(os.path.dirname(__file__), decision_file)
        
        if os.path.exists(decision_path):
            try:
                with open(decision_path, 'r') as f:
                    decision_code = f.read()
            except Exception as e:
                print(f"Warning: Could not read decision file: {e}")
                decision_code = "Decision code not available"
        else:
            decision_code = f"Decision file not found: {decision_file}"
        
        # Calculate metrics
        import math
        
        wins = sum(1 for t in trades if t['pnl'] > 0)
        losses = sum(1 for t in trades if t['pnl'] < 0)
        total_trades = len(trades)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in trades)
        starting_capital = 10000
        pnl_percent = (total_pnl / starting_capital * 100)
        
        total_wins_amount = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        total_losses_amount = sum(abs(t['pnl']) for t in trades if t['pnl'] < 0)
        profit_factor = (total_wins_amount / total_losses_amount) if total_losses_amount > 0 else 0
        
        avg_win = (total_wins_amount / wins) if wins > 0 else 0
        avg_loss = -(total_losses_amount / losses) if losses > 0 else 0
        
        # Sharpe Ratio
        if total_trades > 1:
            pnl_list = [t['pnl'] for t in trades]
            mean_pnl = sum(pnl_list) / len(pnl_list)
            variance = sum((x - mean_pnl) ** 2 for x in pnl_list) / (len(pnl_list) - 1)
            std_dev = math.sqrt(variance)
            sharpe = (mean_pnl / std_dev * math.sqrt(252)) if std_dev > 0 else 0
        else:
            sharpe = 0
        
        # Sortino Ratio
        if total_trades > 1:
            pnl_list = [t['pnl'] for t in trades]
            mean_pnl = sum(pnl_list) / len(pnl_list)
            downside_returns = [x for x in pnl_list if x < 0]
            if downside_returns:
                downside_var = sum(x ** 2 for x in downside_returns) / len(downside_returns)
                downside_std = math.sqrt(downside_var)
                sortino = (mean_pnl / downside_std * math.sqrt(252)) if downside_std > 0 else 0
            else:
                sortino = float('inf')
        else:
            sortino = 0
        
        # Max Drawdown
        peak = starting_capital
        max_dd = 0
        current = starting_capital
        for t in trades:
            current += t['pnl']
            if current > peak:
                peak = current
            dd = ((peak - current) / peak * 100) if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        # Calmar Ratio
        calmar = (pnl_percent / max_dd) if max_dd > 0 else 0
        
        # Expectancy
        expectancy = (win_rate / 100 * avg_win) + ((100 - win_rate) / 100 * avg_loss)
        
        # Kelly %
        if losses > 0 and avg_loss != 0:
            win_prob = win_rate / 100
            loss_prob = 1 - win_prob
            kelly = (win_prob / abs(avg_loss)) - (loss_prob / avg_win) if avg_win > 0 else 0
            kelly_percent = max(0, min(kelly * 100, 100))
        else:
            kelly_percent = 0
        
        best_trade = max(t['pnl'] for t in trades) if trades else 0
        worst_trade = min(t['pnl'] for t in trades) if trades else 0
        
        # Win/Loss streaks
        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for t in trades:
            if t['pnl'] > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            elif t['pnl'] < 0:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
        
        # Prepare metrics for AI
        sortino_str = f"{sortino:.2f}" if sortino != float('inf') else "∞"
        
        metrics_text = f"""
Strategy: {strategy_name}
Total Trades: {total_trades}
Win Rate: {win_rate:.1f}% ({wins} wins, {losses} losses)
Total P&L: ${total_pnl:.2f} ({pnl_percent:.2f}%)
Profit Factor: {profit_factor:.2f}
Average Win: ${avg_win:.2f}
Average Loss: ${abs(avg_loss):.2f}
Sharpe Ratio: {sharpe:.2f}
Sortino Ratio: {sortino_str}
Calmar Ratio: {calmar:.2f}
Max Drawdown: {max_dd:.2f}%
Expectancy: ${expectancy:.2f}
Kelly %: {kelly_percent:.1f}%
Best Trade: ${best_trade:.2f}
Worst Trade: ${worst_trade:.2f}
Win/Loss Streaks: {max_win_streak} / {max_loss_streak}
"""
        
        # Prepare code section
        code_section = f"""

STRATEGY CODE:
```python
{decision_code}
```
"""

        # Call DeepSeek API
        prompt = f"""Analyze this trading strategy by examining both its performance metrics AND its decision-making code.

PERFORMANCE METRICS:
{metrics_text}
{code_section}

Provide a comprehensive analysis:

1. **Overall Performance Assessment** (2-3 sentences)
   - Comment on both metrics AND code quality/logic

2. **Key Strengths** (3-4 bullet points)
   - Include both metric strengths and code strengths (e.g., risk management, logic clarity)

3. **Key Weaknesses or Risks** (3-4 bullet points)
   - Include both metric weaknesses and code issues (e.g., overfitting, hardcoded values, missing edge cases)

4. **Practical Recommendations** (3-4 bullet points)
   - Suggest specific code improvements and parameter adjustments
   - Focus on actionable changes to the strategy code

Keep analysis concise but technical. Use plain language but don't shy away from specific code critiques."""

        response = requests.post(
            f"{config.DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional trading strategy analyst and Python developer. Analyze both performance metrics and code quality of trading strategies. Provide clear, technical, and actionable insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            },
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result['choices'][0]['message']['content']
            
            return jsonify({
                'success': True,
                'analysis': analysis
            })
        else:
            return jsonify({
                'success': False,
                'analysis': f'AI analysis unavailable (API error: {response.status_code})'
            })
            
    except Exception as e:
        print(f"Error generating AI analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'analysis': f'Error generating analysis: {str(e)}'
        })


if __name__ == '__main__':
    print("🌐 Starting Trading Dashboard Web Server...")
    print("📊 Dashboard: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=5000, debug=False)

