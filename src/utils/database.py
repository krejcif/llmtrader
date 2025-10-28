"""Database utilities for paper trading"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os
import sys

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class TradingDatabase:
    """SQLite database for paper trading records"""
    
    def __init__(self, db_path: str = None):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            # Default to project root/data directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(project_root, 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'paper_trades.db')
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist and run migrations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if table exists and needs migration
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Check if columns exist and migrate
            cursor.execute("PRAGMA table_info(trades)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'strategy' not in columns:
                print("🔧 Migrating database: Adding 'strategy' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN strategy TEXT DEFAULT 'structured'")
                cursor.execute("UPDATE trades SET strategy = 'structured' WHERE strategy IS NULL")
                conn.commit()
                print("✅ Database migration complete")
            
            if 'valid' not in columns:
                print("🔧 Migrating database: Adding 'valid' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN valid INTEGER DEFAULT 1")
                cursor.execute("UPDATE trades SET valid = 1 WHERE valid IS NULL")
                conn.commit()
                print("✅ Database migration complete (valid column added)")
            
            if 'audit_notes' not in columns:
                print("🔧 Migrating database: Adding 'audit_notes' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN audit_notes TEXT")
                conn.commit()
                print("✅ Database migration complete (audit_notes column added)")
            
            if 'entry_fee' not in columns:
                print("🔧 Migrating database: Adding 'entry_fee' and 'exit_fee' columns...")
                cursor.execute("ALTER TABLE trades ADD COLUMN entry_fee REAL DEFAULT 0")
                cursor.execute("ALTER TABLE trades ADD COLUMN exit_fee REAL DEFAULT 0")
                cursor.execute("ALTER TABLE trades ADD COLUMN total_fees REAL DEFAULT 0")
                conn.commit()
                print("✅ Database migration complete (fee columns added)")
            
            if 'size' not in columns:
                print("🔧 Migrating database: Adding 'size' column...")
                cursor.execute("ALTER TABLE trades ADD COLUMN size REAL DEFAULT 0")
                conn.commit()
                print("✅ Database migration complete (size column added)")
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence TEXT,
                entry_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                size REAL DEFAULT 0,
                risk_amount REAL,
                reward_amount REAL,
                risk_reward_ratio REAL,
                atr REAL,
                entry_setup TEXT,
                status TEXT DEFAULT 'OPEN',
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                exit_price REAL,
                exit_reason TEXT,
                exit_market_high REAL,
                exit_market_low REAL,
                exit_market_close REAL,
                pnl REAL,
                pnl_percentage REAL,
                entry_fee REAL DEFAULT 0,
                exit_fee REAL DEFAULT 0,
                total_fees REAL DEFAULT 0,
                analysis_data TEXT,
                reasoning TEXT,
                valid INTEGER DEFAULT 1,
                audit_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                live_trade INTEGER DEFAULT 0
            )
        ''')
        
        # Index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON trades(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON trades(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy ON trades(strategy)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entry_time ON trades(entry_time)')
        
        # Strategy runs table (execution logs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence TEXT,
                reasoning TEXT,
                key_factors TEXT,
                market_data TEXT,
                analysis_summary TEXT,
                risk_management TEXT,
                executed BOOLEAN DEFAULT 0,
                execution_reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Index for strategy runs
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_runs_symbol ON strategy_runs(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_runs_strategy ON strategy_runs(strategy)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON strategy_runs(timestamp)')
        
        conn.commit()
        conn.close()
    
    def create_trade(self, trade_data: Dict) -> str:
        """
        Create a new paper trade
        
        Args:
            trade_data: Dictionary with trade information
            
        Returns:
            trade_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Include strategy in trade_id for uniqueness
        strategy = trade_data.get('strategy', 'unknown')
        trade_id = f"{trade_data['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{strategy}"
        
        # Calculate entry fee (Binance Futures taker fee from config)
        entry_price = trade_data['entry_price']
        fee_rate = trade_data.get('fee_rate', config.TRADING_FEE_RATE)
        entry_fee = entry_price * fee_rate
        
        cursor.execute('''
            INSERT INTO trades (
                trade_id, symbol, strategy, action, confidence,
                entry_price, stop_loss, take_profit,
                risk_amount, reward_amount, risk_reward_ratio,
                atr, entry_setup, status, entry_time,
                entry_fee, exit_fee, total_fees,
                analysis_data, reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_id,
            trade_data['symbol'],
            trade_data.get('strategy', 'unknown'),
            trade_data['action'],
            trade_data.get('confidence'),
            entry_price,
            trade_data['stop_loss'],
            trade_data['take_profit'],
            trade_data.get('risk_amount'),
            trade_data.get('reward_amount'),
            trade_data.get('risk_reward_ratio'),
            trade_data.get('atr'),
            trade_data.get('entry_setup'),
            'OPEN',
            trade_data.get('entry_time', datetime.utcnow().isoformat() + 'Z'),
            entry_fee,
            0,  # exit_fee will be calculated on close
            entry_fee,  # total_fees starts with entry_fee
            json.dumps(trade_data.get('analysis_data', {})),
            trade_data.get('reasoning')
        ))
        
        conn.commit()
        conn.close()
        
        return trade_id
    
    def mark_trade_invalid(self, trade_id: str, reason: str):
        """Mark a trade as invalid (failed audit)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE trades 
            SET valid = 0, audit_notes = ?
            WHERE trade_id = ?
        ''', (reason, trade_id))
        
        conn.commit()
        conn.close()
    
    def get_open_trades(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get all open paper trades (trades table is ONLY for paper trading)
        
        Args:
            symbol: Filter by symbol (optional)
        
        Returns:
            List of open paper trades
        
        Note:
            Live trades are NOT stored in this table.
            Check Binance API directly for live positions.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute('SELECT * FROM trades WHERE status = "OPEN" AND symbol = ?', (symbol,))
        else:
            cursor.execute('SELECT * FROM trades WHERE status = "OPEN"')
        
        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return trades
    
    def close_trade(self, trade_id: str, exit_price: float, exit_reason: str, fee_rate: float = None):
        """
        Close a trade and calculate P&L (with fees deducted)
        
        Args:
            trade_id: Trade identifier
            exit_price: Exit price
            exit_reason: Reason for exit (TP_HIT, SL_HIT, MANUAL)
            fee_rate: Trading fee rate (default from config.TRADING_FEE_RATE)
        """
        if fee_rate is None:
            fee_rate = config.TRADING_FEE_RATE
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Get trade details
        cursor.execute('SELECT * FROM trades WHERE trade_id = ?', (trade_id,))
        trade = cursor.fetchone()
        
        if not trade:
            conn.close()
            raise ValueError(f"Trade {trade_id} not found")
        
        action = trade['action']
        entry_price = trade['entry_price']
        size = trade['size'] if trade['size'] is not None else 0
        entry_fee = trade['entry_fee'] if trade['entry_fee'] is not None else 0
        
        # Calculate exit fee (0.05% of position value at exit)
        position_value_at_exit = exit_price * size
        exit_fee = position_value_at_exit * fee_rate
        
        # Calculate total fees
        total_fees = entry_fee + exit_fee
        
        # Calculate P&L before fees (price difference * position size)
        if action == 'LONG':
            pnl_before_fees = (exit_price - entry_price) * size
        else:  # SHORT
            pnl_before_fees = (entry_price - exit_price) * size
        
        # Calculate final P&L after fees
        pnl = pnl_before_fees - total_fees
        
        # P&L percentage based on entry position value
        entry_position_value = entry_price * size
        pnl_percentage = (pnl / entry_position_value) * 100 if entry_position_value > 0 else 0
        
        # Update trade
        cursor.execute('''
            UPDATE trades 
            SET status = 'CLOSED',
                exit_time = ?,
                exit_price = ?,
                exit_reason = ?,
                exit_fee = ?,
                total_fees = ?,
                pnl = ?,
                pnl_percentage = ?
            WHERE trade_id = ?
        ''', (
            datetime.utcnow().isoformat() + 'Z',
            exit_price,
            exit_reason,
            exit_fee,
            total_fees,
            pnl,
            pnl_percentage,
            trade_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_trade_stats(self, symbol: Optional[str] = None, strategy: Optional[str] = None) -> Dict:
        """Get trading statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_parts = []
        if symbol:
            where_parts.append(f"symbol = '{symbol}'")
        if strategy:
            where_parts.append(f"strategy = '{strategy}'")
        
        where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""
        
        # Build proper where clause for all queries
        where_clause_with_and = " AND " + " AND ".join(where_parts) if where_parts else ""
        
        # Add valid filter to all queries
        valid_filter = " AND valid = 1"
        
        # Total trades (only valid)
        cursor.execute(f'SELECT COUNT(*) FROM trades WHERE valid = 1 {where_clause.replace("WHERE", "AND") if where_clause else ""}')
        total_trades = cursor.fetchone()[0]
        
        # Invalid trades count
        cursor.execute(f'SELECT COUNT(*) FROM trades WHERE valid = 0 {where_clause.replace("WHERE", "AND") if where_clause else ""}')
        invalid_trades = cursor.fetchone()[0]
        
        # Open trades (only valid)
        cursor.execute(f'SELECT COUNT(*) FROM trades WHERE status = "OPEN"{valid_filter}{where_clause_with_and}')
        open_trades = cursor.fetchone()[0]
        
        # Closed trades (only valid)
        cursor.execute(f'SELECT COUNT(*) FROM trades WHERE status = "CLOSED"{valid_filter}{where_clause_with_and}')
        closed_trades = cursor.fetchone()[0]
        
        # Win/Loss stats (only valid)
        cursor.execute(f'SELECT COUNT(*) FROM trades WHERE status = "CLOSED" AND pnl > 0{valid_filter}{where_clause_with_and}')
        wins = cursor.fetchone()[0]
        
        cursor.execute(f'SELECT COUNT(*) FROM trades WHERE status = "CLOSED" AND pnl <= 0{valid_filter}{where_clause_with_and}')
        losses = cursor.fetchone()[0]
        
        # Total P&L (only valid)
        cursor.execute(f'SELECT SUM(pnl), AVG(pnl_percentage) FROM trades WHERE status = "CLOSED"{valid_filter}{where_clause_with_and}')
        result = cursor.fetchone()
        total_pnl = result[0] or 0
        avg_pnl_pct = result[1] or 0
        
        # Calculate cumulative ROI (based on $10,000 starting capital)
        starting_capital = 10000
        cumulative_roi = (total_pnl / starting_capital * 100) if total_pnl != 0 else 0
        
        # Profit factor (total wins / total losses)
        cursor.execute(f'SELECT SUM(pnl) FROM trades WHERE status = "CLOSED" AND pnl > 0{valid_filter}{where_clause_with_and}')
        total_wins_amount = cursor.fetchone()[0] or 0
        
        cursor.execute(f'SELECT SUM(ABS(pnl)) FROM trades WHERE status = "CLOSED" AND pnl < 0{valid_filter}{where_clause_with_and}')
        total_losses_amount = cursor.fetchone()[0] or 0
        
        profit_factor = (total_wins_amount / total_losses_amount) if total_losses_amount > 0 else (total_wins_amount if total_wins_amount > 0 else 0)
        
        # Max consecutive wins/losses (only valid trades)
        cursor.execute(f'''
            SELECT pnl FROM trades 
            WHERE status = "CLOSED"{valid_filter}{where_clause_with_and}
            ORDER BY entry_time ASC
        ''')
        pnls = [row[0] for row in cursor.fetchall()]
        
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for pnl in pnls:
            if pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
        
        conn.close()
        
        win_rate = (wins / closed_trades * 100) if closed_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "invalid_trades": invalid_trades,
            "open_trades": open_trades,
            "closed_trades": closed_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_pnl_percentage": round(avg_pnl_pct, 2),
            "cumulative_roi": round(cumulative_roi, 2),
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            "profit_factor": round(profit_factor, 2)
        }
    
    def log_strategy_run(self, run_data: Dict) -> str:
        """
        Log a strategy run (decision making process)
        
        Args:
            run_data: Dictionary with strategy run information
            
        Returns:
            run_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate run_id (with microseconds for uniqueness)
        run_id = f"{run_data['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{run_data['strategy']}"
        
        cursor.execute('''
            INSERT INTO strategy_runs (
                run_id, symbol, strategy, timestamp, action, confidence,
                reasoning, key_factors, market_data, analysis_summary,
                risk_management, executed, execution_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            run_id,
            run_data['symbol'],
            run_data['strategy'],
            run_data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
            run_data['action'],
            run_data.get('confidence'),
            run_data.get('reasoning'),
            json.dumps(run_data.get('key_factors', [])),
            json.dumps(run_data.get('market_data', {})),
            run_data.get('analysis_summary'),
            json.dumps(run_data.get('risk_management', {})),
            run_data.get('executed', False),
            run_data.get('execution_reason')
        ))
        
        conn.commit()
        conn.close()
        
        return run_id
    
    def get_strategy_runs(self, symbol: Optional[str] = None, strategy: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get strategy runs with optional filtering"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM strategy_runs WHERE 1=1'
        params = []
        
        if symbol:
            query += ' AND symbol = ?'
            params.append(symbol)
        
        if strategy:
            query += ' AND strategy = ?'
            params.append(strategy)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        runs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return runs

