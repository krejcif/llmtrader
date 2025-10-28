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
from strategy_config import STRATEGIES

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


@app.route('/live')
def live():
    """Serve live trading page"""
    return send_from_directory('../web', 'live.html')


@app.route('/api/stats')
def get_stats():
    """Get overall and per-strategy statistics (combines paper + live trading)"""
    symbol = request.args.get('symbol')
    
    # Create strategy symbol mapping from config
    strategy_symbols = {strategy.name: strategy.symbol for strategy in STRATEGIES}
    
    # Get paper trading stats from database
    stats_all = db.get_trade_stats(symbol)
    stats_sol = db.get_trade_stats(symbol, 'sol')
    stats_sol_fast = db.get_trade_stats(symbol, 'sol_fast')
    stats_eth = db.get_trade_stats(symbol, 'eth')
    stats_eth_fast = db.get_trade_stats(symbol, 'eth_fast')
    
    # Get live trading stats from Binance
    live_stats = None
    try:
        from utils.binance_client import BinanceClient
        client = BinanceClient()
        live_stats = client.get_live_trading_stats(symbol=symbol)
    except Exception as e:
        print(f"Error fetching live stats: {e}")
        live_stats = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'today_pnl': 0,
            'today_roi': 0,
            'week_pnl': 0,
            'week_roi': 0,
            'month_pnl': 0,
            'month_roi': 0,
            'roi': 0
        }
    
    return jsonify({
        'overall': stats_all,
        'strategies': {
            'sol': stats_sol,
            'sol_fast': stats_sol_fast,
            'eth': stats_eth,
            'eth_fast': stats_eth_fast
        },
        'strategy_symbols': strategy_symbols,
        'live_stats': live_stats  # Add live trading stats from Binance
    })


@app.route('/api/trades')
def get_trades():
    """Get trades with filtering and live P&L for open positions"""
    status = request.args.get('status')  # open, closed
    strategy = request.args.get('strategy')  # sol, sol_fast, eth, eth_fast, doge, doge_fast, xrp, xrp_fast
    limit = int(request.args.get('limit', 15))
    
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
                        size = trade.get('size', 0)  # Position size (quantity of asset)
                        
                        # Calculate P&L based on direction (price difference * size)
                        if trade['action'] == 'LONG':
                            pnl_dollars = (current_price - entry_price) * size
                        else:  # SHORT
                            pnl_dollars = (entry_price - current_price) * size
                        
                        # Calculate P&L percentage based on position value
                        position_value = entry_price * size
                        pnl_pct = (pnl_dollars / position_value) * 100 if position_value > 0 else 0
                        
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
        
        # Close trade using database function (handles P&L calculation with fees and size)
        db.close_trade(
            trade_id=trade_id,
            exit_price=current_price,
            exit_reason='MANUAL_CLOSE'
        )
        
        # Get actual P&L after fees from database (calculated with proper size)
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
        
        # Get all closed trades for this strategy (or all strategies if "overall")
        if strategy == 'overall':
            cursor.execute("""
                SELECT *  FROM trades
                WHERE status = 'CLOSED' AND valid = 1
                ORDER BY exit_time ASC
            """)
        else:
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
        if strategy == 'overall':
            cursor.execute("""
                SELECT * FROM trades
                WHERE valid = 1
                ORDER BY entry_time DESC
                LIMIT 10
            """)
        else:
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


@app.route('/api/binance-account')
def get_binance_account():
    """Get comprehensive Binance Futures account overview"""
    try:
        from utils.binance_client import BinanceClient
        
        client = BinanceClient()
        is_demo = client.demo
        
        # Get account balance
        account = client.client.futures_account()
        
        # Get all positions
        positions = client.client.futures_position_information()
        
        # Get open orders
        open_orders = client.client.futures_get_open_orders()
        
        # Calculate total wallet balance
        total_wallet_balance = float(account['totalWalletBalance'])
        total_unrealized_profit = float(account['totalUnrealizedProfit'])
        total_margin_balance = float(account['totalMarginBalance'])
        available_balance = float(account['availableBalance'])
        
        # Process assets (only non-zero balances)
        assets = []
        for asset in account['assets']:
            balance = float(asset['walletBalance'])
            if balance > 0:
                assets.append({
                    'asset': asset['asset'],
                    'wallet_balance': balance,
                    'unrealized_profit': float(asset['unrealizedProfit']),
                    'margin_balance': float(asset['marginBalance']),
                    'available_balance': float(asset['availableBalance'])
                })
        
        # Get funding fees for open positions
        from datetime import datetime, timedelta
        funding_fees_by_symbol = {}
        try:
            # Get funding fee history for last 30 days
            month_ago = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
            income_history = client.client.futures_income_history(
                incomeType='FUNDING_FEE',
                startTime=month_ago,
                limit=1000
            )
            
            # Group by symbol
            for item in income_history:
                symbol = item.get('symbol', '')
                if symbol:
                    if symbol not in funding_fees_by_symbol:
                        funding_fees_by_symbol[symbol] = 0
                    funding_fees_by_symbol[symbol] += float(item['income'])
        except:
            pass
        
        # Process positions (only open positions)
        fee_rate = 0.0004  # 0.04% Binance Futures taker fee
        active_positions = []
        for pos in positions:
            position_amt = float(pos['positionAmt'])
            if position_amt != 0:
                unrealized_pnl = float(pos['unRealizedProfit'])
                entry_price = float(pos['entryPrice'])
                mark_price = float(pos['markPrice'])
                symbol = pos['symbol']
                
                # Calculate P&L percentage
                if position_amt > 0:  # LONG
                    pnl_pct = ((mark_price - entry_price) / entry_price) * 100
                else:  # SHORT
                    pnl_pct = ((entry_price - mark_price) / entry_price) * 100
                
                # Calculate fees
                position_value_entry = abs(position_amt) * entry_price
                position_value_exit = abs(position_amt) * mark_price
                
                entry_fee = position_value_entry * fee_rate
                exit_fee = position_value_exit * fee_rate
                
                # Get funding fees for this symbol (since position was opened)
                funding_fees = funding_fees_by_symbol.get(symbol, 0)
                
                # Calculate NET P&L = Unrealized PnL - Entry Fee - Exit Fee - Funding Fees
                total_fees = entry_fee + exit_fee + abs(funding_fees)
                net_pnl = unrealized_pnl - total_fees
                net_pnl_pct = (net_pnl / position_value_entry) * 100
                
                active_positions.append({
                    'symbol': symbol,
                    'position_side': pos.get('positionSide', 'BOTH'),
                    'position_amt': position_amt,
                    'position_value': position_value_exit,  # Current position value in USD
                    'entry_price': entry_price,
                    'mark_price': mark_price,
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_pct': pnl_pct,
                    'entry_fee': entry_fee,
                    'exit_fee': exit_fee,
                    'funding_fees': funding_fees,
                    'total_fees': total_fees,
                    'net_pnl': net_pnl,
                    'net_pnl_pct': net_pnl_pct,
                    'leverage': int(pos.get('leverage', 1)),
                    'margin_type': pos.get('marginType', 'cross'),
                    'liquidation_price': float(pos.get('liquidationPrice', 0)) if pos.get('liquidationPrice') else 0
                })
        
        # Process open orders
        formatted_orders = []
        for order in open_orders:
            formatted_orders.append({
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'price': float(order['price']),
                'orig_qty': float(order['origQty']),
                'executed_qty': float(order['executedQty']),
                'status': order['status'],
                'time': order['time']
            })
        
        # Get account statistics
        total_positions = len(active_positions)
        total_orders = len(formatted_orders)
        
        return jsonify({
            'success': True,
            'demo_mode': is_demo,
            'account': {
                'total_wallet_balance': total_wallet_balance,
                'total_unrealized_profit': total_unrealized_profit,
                'total_margin_balance': total_margin_balance,
                'available_balance': available_balance,
                'can_trade': account['canTrade'],
                'can_withdraw': account['canWithdraw']
            },
            'assets': assets,
            'positions': active_positions,
            'orders': formatted_orders,
            'statistics': {
                'total_positions': total_positions,
                'total_orders': total_orders
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/binance-debug')
def binance_debug():
    """Debug endpoint to check Binance data"""
    try:
        from utils.binance_client import BinanceClient
        from datetime import datetime, timedelta
        
        client = BinanceClient()
        now = datetime.now()
        month_ago = int((now - timedelta(days=30)).timestamp() * 1000)
        
        # Get income history
        income_items = client.client.futures_income_history(
            startTime=month_ago,
            limit=1000
        )
        
        # Analyze
        income_types = {}
        for item in income_items:
            itype = item['incomeType']
            income_types[itype] = income_types.get(itype, 0) + 1
        
        realized_pnl_items = [item for item in income_items if item['incomeType'] == 'REALIZED_PNL']
        items_with_symbol = [item for item in realized_pnl_items if item.get('symbol')]
        items_without_symbol = [item for item in realized_pnl_items if not item.get('symbol')]
        
        # Sample items
        sample_with_symbol = []
        for item in items_with_symbol[:5]:
            sample_with_symbol.append({
                'symbol': item.get('symbol'),
                'income': float(item['income']),
                'time': datetime.fromtimestamp(item['time']/1000).isoformat(),
                'asset': item.get('asset'),
                'info': item.get('info')
            })
        
        sample_without_symbol = []
        for item in items_without_symbol[:5]:
            sample_without_symbol.append(item)
        
        return jsonify({
            'demo_mode': client.demo,
            'has_credentials': client.has_credentials,
            'total_income_items': len(income_items),
            'income_types': income_types,
            'realized_pnl_count': len(realized_pnl_items),
            'with_symbol': len(items_with_symbol),
            'without_symbol': len(items_without_symbol),
            'sample_with_symbol': sample_with_symbol,
            'sample_without_symbol': sample_without_symbol
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/binance-analytics')
def get_binance_analytics():
    """Get comprehensive analytics for Binance account (ONLY Binance data, no local DB)"""
    try:
        from utils.binance_client import BinanceClient
        from datetime import datetime, timedelta
        
        client = BinanceClient()
        
        # Get account info
        account = client.client.futures_account()
        positions = client.client.futures_position_information()
        
        # Calculate current balance
        current_balance = float(account['totalWalletBalance'])
        unrealized_pnl = float(account['totalUnrealizedProfit'])
        
        # Get account balance history (income history for last 30 days)
        now = datetime.now()
        start_time = int((now - timedelta(days=30)).timestamp() * 1000)
        
        try:
            income_history = client.client.futures_income_history(
                startTime=start_time,
                limit=1000
            )
        except:
            income_history = []
        
        # Build equity curve data
        equity_data = {}
        realized_pnl_total = 0
        
        for item in income_history:
            timestamp = item['time']
            date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
            income = float(item['income'])
            
            if item['incomeType'] in ['REALIZED_PNL', 'COMMISSION', 'FUNDING_FEE']:
                if date_str not in equity_data:
                    equity_data[date_str] = {'realized_pnl': 0, 'funding': 0, 'commission': 0}
                
                if item['incomeType'] == 'REALIZED_PNL':
                    equity_data[date_str]['realized_pnl'] += income
                    realized_pnl_total += income
                elif item['incomeType'] == 'FUNDING_FEE':
                    equity_data[date_str]['funding'] += income
                elif item['incomeType'] == 'COMMISSION':
                    equity_data[date_str]['commission'] += income
        
        # Calculate daily equity values
        equity_curve = []
        cumulative_pnl = 0
        starting_balance = current_balance - unrealized_pnl - realized_pnl_total
        
        sorted_dates = sorted(equity_data.keys())
        for date in sorted_dates:
            daily_data = equity_data[date]
            cumulative_pnl += daily_data['realized_pnl'] + daily_data['funding'] + daily_data['commission']
            equity_curve.append({
                'date': date,
                'balance': starting_balance + cumulative_pnl,
                'realized_pnl': daily_data['realized_pnl'],
                'funding': daily_data['funding'],
                'commission': daily_data['commission']
            })
        
        # Add today's point
        equity_curve.append({
            'date': now.strftime('%Y-%m-%d'),
            'balance': current_balance,
            'realized_pnl': 0,
            'funding': 0,
            'commission': 0
        })
        
        # Get live trading statistics using our new function
        live_stats = client.get_live_trading_stats(days=365)
        
        # Get closed positions from Binance account trades (more reliable than income history)
        closed_positions = {}
        try:
            # Get all symbols that had activity in the last 30 days
            month_ago = int((now - timedelta(days=30)).timestamp() * 1000)
            
            # First, get income history to find which symbols had trades
            print(f"🔍 Finding symbols with recent activity...")
            income_items = client.client.futures_income_history(
                startTime=month_ago,
                limit=1000
            )
            
            # Extract symbols from income history (use 'symbol' or 'asset' field)
            active_symbols = set()
            for item in income_items:
                if item.get('symbol'):
                    active_symbols.add(item['symbol'])
                elif item.get('asset') and item.get('asset') != 'USDT':
                    # Convert asset to symbol format (e.g., BTC -> BTCUSDT)
                    active_symbols.add(item['asset'] + 'USDT')
            
            # Fallback: If no symbols found in income history, use symbols from strategies + open positions
            if not active_symbols:
                print("   ⚠️  No symbols in income history, using symbols from active strategies + open positions")
                # Add symbols from open positions
                for pos in positions:
                    if float(pos['positionAmt']) != 0:
                        active_symbols.add(pos['symbol'])
                
                # Add symbols from all active strategies
                for strategy in STRATEGIES:
                    if strategy.enabled:
                        symbol = strategy.symbol.upper() if strategy.symbol else ''
                        if symbol:
                            active_symbols.add(symbol)
                
                print(f"   Symbols from strategies: {sorted(active_symbols)}")
            
            print(f"   Found {len(active_symbols)} symbols to check: {sorted(list(active_symbols))[:10]}")
            
            # Now fetch actual trades for each symbol to get accurate P&L
            all_trades = []
            for symbol in active_symbols:
                try:
                    # Note: Binance Testnet may have issues with startTime, so we fetch last 1000 trades
                    trades = client.client.futures_account_trades(
                        symbol=symbol,
                        limit=1000
                    )
                    all_trades.extend(trades)
                    print(f"   - {symbol}: {len(trades)} trades")
                except Exception as e:
                    print(f"   ⚠️  Could not fetch trades for {symbol}: {e}")
            
            print(f"✅ Total trades fetched: {len(all_trades)}")
            
            # Parse individual positions (not aggregated by symbol)
            # Group trades by symbol and sort by time
            trades_by_symbol = {}
            for trade in all_trades:
                symbol = trade['symbol']
                if symbol not in trades_by_symbol:
                    trades_by_symbol[symbol] = []
                trades_by_symbol[symbol].append(trade)
            
            # Sort trades by time for each symbol
            for symbol in trades_by_symbol:
                trades_by_symbol[symbol].sort(key=lambda x: x['time'])
            
            # Track individual positions
            individual_positions = []
            
            for symbol, symbol_trades in trades_by_symbol.items():
                current_position = None
                running_qty = 0
                
                for trade in symbol_trades:
                    qty = float(trade['qty'])
                    side = trade['side']
                    realized_pnl = float(trade.get('realizedPnl', 0))
                    commission = float(trade.get('commission', 0))
                    price = float(trade['price'])
                    timestamp = trade['time']
                    
                    # Determine trade direction
                    if side == 'BUY':
                        trade_qty = qty
                    else:  # SELL
                        trade_qty = -qty
                    
                    # Check if this opens a new position
                    if current_position is None and trade_qty != 0:
                        # Start new position
                        current_position = {
                            'symbol': symbol,
                            'side': 'LONG' if trade_qty > 0 else 'SHORT',
                            'entry_time': timestamp,
                            'entry_price': price,
                            'entry_qty': abs(trade_qty),
                            'exit_time': None,
                            'exit_price': None,
                            'realized_pnl': 0,
                            'total_commission': abs(commission),
                            'trades': 1
                        }
                        running_qty = trade_qty
                    
                    elif current_position is not None:
                        # Add to current position
                        current_position['total_commission'] += abs(commission)
                        current_position['trades'] += 1
                        
                        # Check if this trade closes or reduces the position
                        new_running_qty = running_qty + trade_qty
                        
                        # Position is being closed (partially or fully)
                        if realized_pnl != 0:
                            current_position['realized_pnl'] += realized_pnl
                        
                        # Check if position is fully closed
                        if abs(new_running_qty) < 0.0001:  # Position closed
                            current_position['exit_time'] = timestamp
                            current_position['exit_price'] = price
                            current_position['duration_hours'] = (timestamp - current_position['entry_time']) / (1000 * 3600)
                            current_position['net_pnl'] = current_position['realized_pnl'] - current_position['total_commission']
                            
                            # Only save positions with realized P&L
                            if current_position['realized_pnl'] != 0:
                                individual_positions.append(current_position)
                            
                            # Reset for next position
                            current_position = None
                            running_qty = 0
                        
                        # Position reversed direction
                        elif (running_qty > 0 and new_running_qty < 0) or (running_qty < 0 and new_running_qty > 0):
                            # Close current position
                            current_position['exit_time'] = timestamp
                            current_position['exit_price'] = price
                            current_position['duration_hours'] = (timestamp - current_position['entry_time']) / (1000 * 3600)
                            current_position['net_pnl'] = current_position['realized_pnl'] - current_position['total_commission']
                            
                            if current_position['realized_pnl'] != 0:
                                individual_positions.append(current_position)
                            
                            # Start new position in opposite direction
                            current_position = {
                                'symbol': symbol,
                                'side': 'LONG' if new_running_qty > 0 else 'SHORT',
                                'entry_time': timestamp,
                                'entry_price': price,
                                'entry_qty': abs(new_running_qty),
                                'exit_time': None,
                                'exit_price': None,
                                'realized_pnl': 0,
                                'total_commission': 0,
                                'trades': 0
                            }
                            running_qty = new_running_qty
                        
                        else:
                            # Position continues
                            running_qty = new_running_qty
            
            closed_positions = individual_positions
            print(f"📊 Identified {len(closed_positions)} individual closed positions")
            
        except Exception as e:
            print(f"❌ Error aggregating closed positions: {e}")
            import traceback
            traceback.print_exc()
        
        # Calculate portfolio distribution by symbol
        portfolio_distribution = {}
        total_position_value = 0
        
        for pos in positions:
            position_amt = float(pos['positionAmt'])
            if position_amt != 0:
                mark_price = float(pos['markPrice'])
                position_value = abs(position_amt * mark_price)
                symbol = pos['symbol']
                
                portfolio_distribution[symbol] = {
                    'value': position_value,
                    'unrealized_pnl': float(pos['unRealizedProfit']),
                    'percentage': 0  # Will calculate after
                }
                total_position_value += position_value
        
        # Calculate percentages
        for symbol in portfolio_distribution:
            if total_position_value > 0:
                portfolio_distribution[symbol]['percentage'] = (
                    portfolio_distribution[symbol]['value'] / total_position_value * 100
                )
        
        # Risk metrics
        margin_balance = float(account['totalMarginBalance'])
        available_balance = float(account['availableBalance'])
        total_maintenance_margin = float(account['totalMaintMargin'])
        
        # Calculate used margin (initial margin) = margin_balance - available_balance
        used_margin = margin_balance - available_balance
        
        # Margin Usage should show % of used margin, not maintenance margin
        margin_usage = (used_margin / margin_balance * 100) if margin_balance > 0 else 0
        exposure_ratio = (total_position_value / margin_balance * 100) if margin_balance > 0 else 0
        
        # Calculate risk score (1-5)
        risk_score = 1
        if margin_usage > 80:
            risk_score = 5
        elif margin_usage > 60:
            risk_score = 4
        elif margin_usage > 40:
            risk_score = 3
        elif margin_usage > 20:
            risk_score = 2
        
        # Funding rate data
        funding_rates = []
        for pos in positions:
            position_amt = float(pos['positionAmt'])
            if position_amt != 0:
                symbol = pos['symbol']
                try:
                    funding_info = client.client.futures_funding_rate(symbol=symbol, limit=1)
                    if funding_info:
                        funding_rate = float(funding_info[0]['fundingRate'])
                        mark_price = float(pos['markPrice'])
                        position_value = abs(position_amt * mark_price)
                        
                        # Calculate 8h funding cost
                        funding_cost = position_value * funding_rate
                        if position_amt > 0:  # LONG pays funding if rate is positive
                            funding_cost = -funding_cost if funding_rate > 0 else abs(funding_cost)
                        else:  # SHORT pays funding if rate is negative
                            funding_cost = funding_cost if funding_rate > 0 else -abs(funding_cost)
                        
                        funding_rates.append({
                            'symbol': symbol,
                            'funding_rate': funding_rate * 100,  # Convert to percentage
                            'cost_8h': funding_cost,
                            'next_funding': 'in ' + str(8 - (datetime.now().hour % 8)) + 'h'
                        })
                except:
                    pass
        
        # Format individual positions for frontend (sorted by exit time, newest first)
        formatted_positions = []
        for pos in sorted(closed_positions, key=lambda x: x['exit_time'], reverse=True):
            formatted_positions.append({
                'symbol': pos['symbol'],
                'side': pos['side'],
                'entry_time': datetime.fromtimestamp(pos['entry_time'] / 1000).isoformat(),
                'exit_time': datetime.fromtimestamp(pos['exit_time'] / 1000).isoformat(),
                'entry_price': round(pos['entry_price'], 6),
                'exit_price': round(pos['exit_price'], 6),
                'quantity': pos['entry_qty'],
                'realized_pnl': round(pos['realized_pnl'], 2),
                'commission': round(pos['total_commission'], 2),
                'net_pnl': round(pos['net_pnl'], 2),
                'duration_hours': round(pos['duration_hours'], 2),
                'trades': pos['trades']
            })
        
        # Calculate total stats
        total_commission = sum(p['commission'] for p in formatted_positions)
        total_net_pnl = sum(p['net_pnl'] for p in formatted_positions)
        
        return jsonify({
            'success': True,
            'equity_curve': equity_curve[-30:],  # Last 30 days
            'performance': {
                'today': {
                    'pnl': live_stats['today_pnl'],
                    'roi': live_stats['today_roi']
                },
                'week': {
                    'pnl': live_stats['week_pnl'],
                    'roi': live_stats['week_roi']
                },
                'month': {
                    'pnl': live_stats['month_pnl'],
                    'roi': live_stats['month_roi']
                },
                'all_time': {
                    'pnl': live_stats['total_pnl'],
                    'roi': live_stats['roi']
                }
            },
            'portfolio_distribution': portfolio_distribution,
            'risk_metrics': {
                'margin_usage': margin_usage,
                'exposure_ratio': exposure_ratio,
                'risk_score': risk_score,
                'available_balance': available_balance,
                'margin_balance': margin_balance,
                'maintenance_margin': total_maintenance_margin
            },
            'funding_rates': funding_rates,
            'total_position_value': total_position_value,
            'closed_positions': formatted_positions,
            'statistics': {
                'total_positions': len(formatted_positions),
                'total_commission': total_commission,
                'total_net_pnl': total_net_pnl,
                'starting_balance': starting_balance
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/strategy-ai-analysis/<strategy_name>')
def get_strategy_ai_analysis(strategy_name):
    """Get AI analysis of strategy performance metrics using DeepSeek"""
    try:
        # Get trades for this strategy (or all strategies if "overall")
        conn = sqlite3.connect(db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if strategy_name == 'overall':
            # Get last 100 trades from ALL strategies
            cursor.execute("""
                SELECT * FROM trades
                WHERE status = 'CLOSED' AND valid = 1
                ORDER BY exit_time DESC
                LIMIT 100
            """)
        else:
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
        
        # Load decision code for specific strategies (not for overall)
        decision_code = ""
        if strategy_name != 'overall':
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
        
        # Prepare prompt based on strategy type
        if strategy_name == 'overall':
            # Overall portfolio analysis - focus on aggregated metrics from all strategies
            prompt = f"""Analyze the OVERALL PORTFOLIO PERFORMANCE across all trading strategies based on the last 100 trades.

AGGREGATED PERFORMANCE METRICS:
{metrics_text}

Note: This represents combined performance from multiple strategies (SOL, ETH, and their variants).

Provide a comprehensive portfolio analysis:

1. **Overall Portfolio Assessment** (2-3 sentences)
   - Comment on the aggregated risk-adjusted returns and overall performance

2. **Key Strengths** (3-4 bullet points)
   - Focus on portfolio-level metrics (diversification, consistency, risk management)
   - Highlight what's working well across strategies

3. **Key Weaknesses or Risks** (3-4 bullet points)
   - Identify portfolio-level concerns (correlation, drawdowns, concentration risk)
   - Point out areas needing improvement

4. **Strategic Recommendations** (3-4 bullet points)
   - Suggest portfolio-level adjustments (position sizing, strategy allocation, risk limits)
   - Focus on optimizing the overall portfolio performance

Keep analysis concise but technical. Focus on portfolio management perspective."""
        else:
            # Individual strategy analysis - include code review
            code_section = f"""

STRATEGY CODE:
```python
{decision_code}
```
"""
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


@app.route('/api/strategies')
def get_strategies():
    """Get all strategies with their configuration"""
    try:
        strategies_list = []
        
        for strategy in STRATEGIES:
            strategies_list.append({
                'name': strategy.name,
                'symbol': strategy.symbol,
                'timeframe_higher': strategy.timeframe_higher,
                'timeframe_lower': strategy.timeframe_lower,
                'interval_minutes': strategy.interval_minutes,
                'enabled': strategy.enabled,
                'live_trading': strategy.live_trading
            })
        
        return jsonify({
            'success': True,
            'strategies': strategies_list,
            'binance_demo': config.BINANCE_DEMO
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/strategies/<strategy_name>/live-trading', methods=['POST'])
def toggle_live_trading(strategy_name):
    """Toggle live trading for a strategy"""
    try:
        data = request.get_json()
        live_trading = data.get('live_trading', False)
        
        # Find strategy and update
        strategy = next((s for s in STRATEGIES if s.name == strategy_name), None)
        
        if not strategy:
            return jsonify({
                'success': False,
                'error': f'Strategy {strategy_name} not found'
            }), 404
        
        # Update strategy configuration
        strategy.live_trading = live_trading
        
        # Save to persistent storage
        live_trading_file = os.path.join(os.path.dirname(__file__), '../data/live_trading_config.json')
        os.makedirs(os.path.dirname(live_trading_file), exist_ok=True)
        
        # Load existing config
        live_config = {}
        if os.path.exists(live_trading_file):
            with open(live_trading_file, 'r') as f:
                live_config = json.load(f)
        
        # Update config
        live_config[strategy_name] = live_trading
        
        # Save config
        with open(live_trading_file, 'w') as f:
            json.dump(live_config, f, indent=2)
        
        return jsonify({
            'success': True,
            'strategy': strategy_name,
            'live_trading': live_trading,
            'message': f'Live trading {"enabled" if live_trading else "disabled"} for {strategy_name}'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("🌐 Starting Trading Dashboard Web Server...")
    print("📊 Dashboard: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=5000, debug=False)

