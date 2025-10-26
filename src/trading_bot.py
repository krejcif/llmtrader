#!/usr/bin/env python
"""Autonomous Trading Bot - Runs continuously, analyzes, trades, and monitors"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.graph import StateGraph, END
from models.state import TradingState
from agents.data_collector import collect_market_data
from agents.data_collector_intraday import collect_market_data_intraday
from agents.news_collector import collect_stock_news
from agents.btc_collector import collect_btc_data
from agents.ixic_collector import collect_ixic_data
from agents.analysis import analyze_market
from agents.analysis_intraday import analyze_market_intraday
from agents.decision_maker import make_decision
from agents.decision_minimal import make_decision_minimal
from agents.decision_minimalbtc import make_decision_minimalbtc
from agents.decision_macro import make_decision_macro
from agents.decision_intraday import make_decision_intraday
from agents.paper_trading import execute_paper_trade
from utils.database import TradingDatabase
from utils.binance_client import BinanceClient
import config
from datetime import datetime, timedelta
import time
import signal
import json
import logging
from logging.handlers import RotatingFileHandler


class TradingBot:
    """Autonomous trading bot that runs continuously"""
    
    def __init__(self, analysis_interval: int = 300, monitor_interval: int = 60):
        """
        Initialize trading bot
        
        Args:
            analysis_interval: Seconds between analyses (default 300 = 5 min for intraday)
            monitor_interval: Seconds between trade checks (default 60 = 1 min)
        """
        self.analysis_interval = analysis_interval  # 5 min for intraday
        self.monitor_interval = monitor_interval
        self.running = True
        self.db = TradingDatabase()
        self.binance_client = BinanceClient()
        
        # Create two workflows: full (all strategies) and intraday-only
        self.workflow_full = self.create_workflow_full()
        self.workflow_intraday = self.create_workflow_intraday()
        
        self.last_analysis_time = 0
        self.last_intraday_time = 0
        self.last_monitor_time = 0
        self.analysis_count = 0
        self.intraday_count = 0
        self.trades_created = 0
        self.trades_closed = 0
        
        # Setup logging
        self.setup_logging()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """Setup comprehensive logging system"""
        # Create logs directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(project_root, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('TradingBot')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # File handler with rotation (10MB per file, keep 10 files)
        log_file = os.path.join(logs_dir, 'trading_bot.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        
        # Detailed log file (all details)
        detailed_log = os.path.join(logs_dir, 'bot_detailed.log')
        detailed_handler = RotatingFileHandler(
            detailed_log,
            maxBytes=50*1024*1024,  # 50MB
            backupCount=5
        )
        detailed_handler.setLevel(logging.DEBUG)
        
        # Error log file (errors only)
        error_log = os.path.join(logs_dir, 'bot_errors.log')
        error_handler = RotatingFileHandler(
            error_log,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # Console handler (less verbose)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(funcName)20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_handler.setFormatter(detailed_formatter)
        detailed_handler.setFormatter(detailed_formatter)
        error_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(detailed_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("="*70)
        self.logger.info("Logging system initialized")
        self.logger.info(f"Main log: {log_file}")
        self.logger.info(f"Detailed log: {detailed_log}")
        self.logger.info(f"Error log: {error_log}")
        self.logger.info("="*70)
    
    def calculate_next_candle_time(self, timeframe: str, delay_seconds: int = 3) -> int:
        """
        Calculate seconds until next timeframe candle CLOSES + safety delay
        
        Args:
            timeframe: e.g., '15m', '1h', '4h'
            delay_seconds: Wait after candle close for API to settle (default 3s)
            
        Returns:
            Seconds to wait
        """
        now = datetime.now()
        
        # Parse timeframe
        if timeframe.endswith('m'):
            minutes = int(timeframe[:-1])
            # Round to next candle
            current_minute = now.minute
            next_minute = ((current_minute // minutes) + 1) * minutes
            
            if next_minute >= 60:
                next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            else:
                next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        
        elif timeframe.endswith('h'):
            hours = int(timeframe[:-1])
            current_hour = now.hour
            next_hour = ((current_hour // hours) + 1) * hours
            
            if next_hour >= 24:
                next_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                next_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
        
        elif timeframe.endswith('d'):
            # Next day at midnight
            next_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        else:
            # Unknown format, default to analysis_interval
            return self.analysis_interval
        
        # Add safety delay after candle close
        # This ensures Binance API has time to finalize the candle
        next_time = next_time + timedelta(seconds=delay_seconds)
        
        # Calculate wait time
        wait_seconds = (next_time - now).total_seconds()
        
        self.logger.info(f"Candle close sync: Next {timeframe} candle closes at {(next_time - timedelta(seconds=delay_seconds)).strftime('%H:%M:%S')}")
        self.logger.info(f"Analysis scheduled at {next_time.strftime('%H:%M:%S')} (+{delay_seconds}s safety delay)")
        
        return int(wait_seconds)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.warning("Shutdown signal received. Stopping bot gracefully...")
        print(f"\n\n⏹️  Shutdown signal received. Stopping bot gracefully...")
        self.running = False
    
    def create_workflow_full(self) -> StateGraph:
        """Create FULL workflow - all strategies (runs every 15 minutes)"""
        from langgraph.graph import START
        
        workflow = StateGraph(TradingState)
        
        # Data collection nodes (for 1h/15m strategies)
        workflow.add_node("collect_data", collect_market_data)
        workflow.add_node("collect_news", collect_stock_news)
        workflow.add_node("collect_btc", collect_btc_data)
        workflow.add_node("collect_ixic", collect_ixic_data)
        
        # Intraday data collection (5m/15m)
        workflow.add_node("collect_data_intraday", collect_market_data_intraday)
        
        # Analysis nodes
        workflow.add_node("analyze", analyze_market)
        workflow.add_node("analyze_intraday", analyze_market_intraday)
        
        # Decision nodes (5 strategies)
        workflow.add_node("decide_structured", make_decision)
        workflow.add_node("decide_minimal", make_decision_minimal)
        workflow.add_node("decide_minimalbtc", make_decision_minimalbtc)
        workflow.add_node("decide_macro", make_decision_macro)
        workflow.add_node("decide_intraday", make_decision_intraday)
        
        # Execution node
        workflow.add_node("execute_trade", execute_paper_trade)
        
        # Set entry point
        workflow.set_entry_point("collect_data")
        
        # Parallel data collection (standard + intraday)
        workflow.add_edge("collect_data", "collect_news")
        workflow.add_edge("collect_data", "collect_btc")
        workflow.add_edge("collect_data", "collect_ixic")
        workflow.add_edge("collect_data", "collect_data_intraday")
        
        # Standard analysis after standard collectors
        workflow.add_edge("collect_news", "analyze")
        workflow.add_edge("collect_btc", "analyze")
        workflow.add_edge("collect_ixic", "analyze")
        
        # Intraday analysis after intraday data
        workflow.add_edge("collect_data_intraday", "analyze_intraday")
        
        # PARALLEL EXECUTION: All 5 decision strategies run after their respective analyses
        workflow.add_edge("analyze", "decide_structured")
        workflow.add_edge("analyze", "decide_minimal")
        workflow.add_edge("analyze", "decide_minimalbtc")
        workflow.add_edge("analyze", "decide_macro")
        workflow.add_edge("analyze_intraday", "decide_intraday")
        
        # All 5 must complete before execution
        workflow.add_edge("decide_structured", "execute_trade")
        workflow.add_edge("decide_minimal", "execute_trade")
        workflow.add_edge("decide_minimalbtc", "execute_trade")
        workflow.add_edge("decide_macro", "execute_trade")
        workflow.add_edge("decide_intraday", "execute_trade")
        
        workflow.add_edge("execute_trade", END)
        
        return workflow.compile()
    
    def create_workflow_intraday(self) -> StateGraph:
        """Create INTRADAY-ONLY workflow (runs every 5 minutes)"""
        from langgraph.graph import START
        
        workflow = StateGraph(TradingState)
        
        # Only intraday data collection
        workflow.add_node("collect_data_intraday", collect_market_data_intraday)
        
        # Only intraday analysis
        workflow.add_node("analyze_intraday", analyze_market_intraday)
        
        # Only intraday decision
        workflow.add_node("decide_intraday", make_decision_intraday)
        
        # Execution node
        workflow.add_node("execute_trade", execute_paper_trade)
        
        # Set entry point
        workflow.set_entry_point("collect_data_intraday")
        
        # Simple linear workflow
        workflow.add_edge("collect_data_intraday", "analyze_intraday")
        workflow.add_edge("analyze_intraday", "decide_intraday")
        workflow.add_edge("decide_intraday", "execute_trade")
        workflow.add_edge("execute_trade", END)
        
        return workflow.compile()
    
    def run_analysis(self):
        """Run complete analysis and trading decision"""
        self.analysis_count += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.logger.info("="*70)
        self.logger.info(f"ANALYSIS #{self.analysis_count} STARTED - {timestamp}")
        self.logger.info("="*70)
        
        print(f"\n{'='*70}")
        print(f"📊 RUNNING ANALYSIS #{self.analysis_count} - {timestamp}")
        print(f"{'='*70}\n")
        
        try:
            self.logger.info(f"Symbol: {config.SYMBOL}, TF: {config.TIMEFRAME_HIGHER}/{config.TIMEFRAME_LOWER}")
            initial_state: TradingState = {
                "symbol": config.SYMBOL,
                "market_data": None,
                "news_data": None,
                "btc_data": None,
                "ixic_data": None,
                "analysis": None,
                "recommendation_structured": None,
                "recommendation_minimal": None,
                "recommendation_minimalbtc": None,
                "recommendation_macro": None,
                "recommendation_intraday": None,
                "trade_execution": None,
                "error": None
            }
            
            result = self.workflow.invoke(initial_state)
            
            # Log and display summary (all 5 strategies)
            rec_struct = result.get('recommendation_structured')
            rec_minimal = result.get('recommendation_minimal')
            rec_minimalbtc = result.get('recommendation_minimalbtc')
            rec_macro = result.get('recommendation_macro')
            rec_intraday = result.get('recommendation_intraday')
            
            if rec_struct or rec_minimal or rec_minimalbtc or rec_macro or rec_intraday:
                print(f"\n{'='*70}")
                print(f"📈 MULTI-STRATEGY ANALYSIS COMPLETE")
                print(f"{'='*70}\n")
                
                # Structured strategy
                if rec_struct:
                    action_s = rec_struct['action']
                    conf_s = rec_struct.get('confidence', 'N/A')
                    
                    print(f"📐 STRUCTURED: {action_s} ({conf_s})")
                    self.logger.info(f"[STRUCTURED] {action_s} (confidence: {conf_s})")
                    
                    if action_s in ['LONG', 'SHORT']:
                        rm_s = rec_struct.get('risk_management', {})
                        print(f"   Entry: ${rm_s.get('entry', 'N/A')} | SL: ${rm_s.get('stop_loss', 'N/A')} | TP: ${rm_s.get('take_profit', 'N/A')}")
                        self.logger.info(f"   Entry ${rm_s.get('entry', 'N/A')}, SL ${rm_s.get('stop_loss', 'N/A')}, TP ${rm_s.get('take_profit', 'N/A')}, R/R 1:{rm_s.get('risk_reward_ratio', 'N/A')}")
                    
                    reasoning_s = rec_struct.get('reasoning', '')
                    if reasoning_s:
                        print(f"   Reasoning: {reasoning_s[:80]}...")
                        self.logger.info(f"   Reasoning: {reasoning_s}")
                    print()
                
                # Minimal strategy
                if rec_minimal:
                    action_m = rec_minimal['action']
                    conf_m = rec_minimal.get('confidence', 'N/A')
                    
                    print(f"🤖 MINIMAL: {action_m} ({conf_m})")
                    self.logger.info(f"[MINIMAL] {action_m} (confidence: {conf_m})")
                    
                    if action_m in ['LONG', 'SHORT']:
                        rm_m = rec_minimal.get('risk_management', {})
                        print(f"   Entry: ${rm_m.get('entry', 'N/A')} | SL: ${rm_m.get('stop_loss', 'N/A')} | TP: ${rm_m.get('take_profit', 'N/A')}")
                        self.logger.info(f"   Entry ${rm_m.get('entry', 'N/A')}, SL ${rm_m.get('stop_loss', 'N/A')}, TP ${rm_m.get('take_profit', 'N/A')}, R/R 1:{rm_m.get('risk_reward_ratio', 'N/A')}")
                    
                    reasoning_m = rec_minimal.get('reasoning', '')
                    if reasoning_m:
                        print(f"   Reasoning: {reasoning_m[:80]}...")
                        self.logger.info(f"   Reasoning: {reasoning_m}")
                    print()
                
                # MinimalBTC strategy
                if rec_minimalbtc:
                    action_mbtc = rec_minimalbtc['action']
                    conf_mbtc = rec_minimalbtc.get('confidence', 'N/A')
                    btc_ctx = rec_minimalbtc.get('btc_context', 'N/A')
                    
                    print(f"₿  MINIMALBTC: {action_mbtc} ({conf_mbtc}) [BTC: {btc_ctx}]")
                    self.logger.info(f"[MINIMALBTC] {action_mbtc} (confidence: {conf_mbtc}, BTC context: {btc_ctx})")
                    
                    if action_mbtc in ['LONG', 'SHORT']:
                        rm_mbtc = rec_minimalbtc.get('risk_management', {})
                        print(f"   Entry: ${rm_mbtc.get('entry', 'N/A')} | SL: ${rm_mbtc.get('stop_loss', 'N/A')} | TP: ${rm_mbtc.get('take_profit', 'N/A')}")
                        self.logger.info(f"   Entry ${rm_mbtc.get('entry', 'N/A')}, SL ${rm_mbtc.get('stop_loss', 'N/A')}, TP ${rm_mbtc.get('take_profit', 'N/A')}, R/R 1:{rm_mbtc.get('risk_reward_ratio', 'N/A')}")
                    
                    reasoning_mbtc = rec_minimalbtc.get('reasoning', '')
                    if reasoning_mbtc:
                        print(f"   Reasoning: {reasoning_mbtc[:80]}...")
                        self.logger.info(f"   Reasoning: {reasoning_mbtc}")
                    print()
                
                # Macro strategy
                if rec_macro:
                    action_ma = rec_macro['action']
                    conf_ma = rec_macro.get('confidence', 'N/A')
                    
                    print(f"🌍 MACRO: {action_ma} ({conf_ma})")
                    self.logger.info(f"[MACRO] {action_ma} (confidence: {conf_ma})")
                    
                    if action_ma in ['LONG', 'SHORT']:
                        rm_ma = rec_macro.get('risk_management', {})
                        print(f"   Entry: ${rm_ma.get('entry', 'N/A')} | SL: ${rm_ma.get('stop_loss', 'N/A')} | TP: ${rm_ma.get('take_profit', 'N/A')}")
                        self.logger.info(f"   Entry ${rm_ma.get('entry', 'N/A')}, SL ${rm_ma.get('stop_loss', 'N/A')}, TP ${rm_ma.get('take_profit', 'N/A')}")
                    
                    reasoning_ma = rec_macro.get('reasoning', '')
                    if reasoning_ma:
                        print(f"   Reasoning: {reasoning_ma[:80]}...")
                        self.logger.info(f"   Reasoning: {reasoning_ma}")
                    print()
                
                # Intraday strategy
                if rec_intraday:
                    action_id = rec_intraday['action']
                    conf_id = rec_intraday.get('confidence', 'N/A')
                    session = rec_intraday.get('session', 'N/A')
                    
                    print(f"⚡ INTRADAY: {action_id} ({conf_id}) [{session}]")
                    self.logger.info(f"[INTRADAY] {action_id} (confidence: {conf_id}, session: {session})")
                    
                    if action_id in ['LONG', 'SHORT']:
                        rm_id = rec_intraday.get('risk_management', {})
                        print(f"   Entry: ${rm_id.get('entry', 'N/A')} | SL: ${rm_id.get('stop_loss', 'N/A')} | TP: ${rm_id.get('take_profit', 'N/A')}")
                        print(f"   Scalping stops: -{rm_id.get('stop_distance_percentage', 0):.2f}% / +{rm_id.get('tp_distance_percentage', 0):.2f}%")
                        self.logger.info(f"   Entry ${rm_id.get('entry', 'N/A')}, Tight stops: -{rm_id.get('stop_distance_percentage', 0):.2f}%/+{rm_id.get('tp_distance_percentage', 0):.2f}%")
                    
                    reasoning_id = rec_intraday.get('reasoning', '')
                    if reasoning_id:
                        print(f"   Reasoning: {reasoning_id[:80]}...")
                        self.logger.info(f"   Reasoning: {reasoning_id}")
                    print()
                
                # Agreement check
                if rec_struct and rec_minimal:
                    if rec_struct['action'] == rec_minimal['action']:
                        if rec_struct['action'] in ['LONG', 'SHORT']:
                            print(f"🤝 AGREEMENT: Both strategies → {rec_struct['action']}")
                            self.logger.info(f"AGREEMENT: Both strategies signal {rec_struct['action']}")
                        else:
                            print(f"🤝 AGREEMENT: Both → NEUTRAL")
                    else:
                        print(f"⚠️  DISAGREEMENT: STRUCTURED={rec_struct['action']}, MINIMAL={rec_minimal['action']}")
                        self.logger.warning(f"DISAGREEMENT: STRUCTURED={rec_struct['action']}, MINIMAL={rec_minimal['action']}")
                    print()
                
                # Trade execution summary
                if result.get('trade_execution', {}).get('executed'):
                    trades = result['trade_execution'].get('trades', [])
                    print(f"✅ {len(trades)} trade(s) executed:")
                    for trade_info in trades:
                        print(f"   [{trade_info['strategy'].upper()}] {trade_info['trade_id']}")
                        self.logger.info(f"Trade created [{trade_info['strategy'].upper()}]: {trade_info['trade_id']} - {trade_info['action']}")
                    self.trades_created += len(trades)
                else:
                    print(f"ℹ️  No trades executed (both NEUTRAL)")
                    self.logger.info("No trades executed - both strategies NEUTRAL")
                
                print(f"\n{'='*70}\n")
            else:
                self.logger.warning("Analysis completed but no recommendations generated")
            
            self.last_analysis_time = time.time()
            self.logger.info(f"Analysis #{self.analysis_count} finished. Next in {self.analysis_interval}s")
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {e}", exc_info=True)
            print(f"❌ Error during analysis: {e}")
            import traceback
            traceback.print_exc()
    
    def monitor_trades(self):
        """Check and close open trades if SL/TP hit"""
        open_trades = self.db.get_open_trades()
        
        if not open_trades:
            return
        
        self.logger.debug(f"Monitoring {len(open_trades)} open trade(s)")
        trades_checked = 0
        trades_closed = 0
        
        for trade in open_trades:
            try:
                symbol = trade['symbol']
                current_price = self.binance_client.get_current_price(symbol)
                
                action = trade['action']
                stop_loss = trade['stop_loss']
                take_profit = trade['take_profit']
                
                should_close = False
                exit_price = None
                exit_reason = None
                
                if action == 'LONG':
                    if current_price <= stop_loss:
                        should_close = True
                        exit_price = stop_loss
                        exit_reason = 'SL_HIT'
                    elif current_price >= take_profit:
                        should_close = True
                        exit_price = take_profit
                        exit_reason = 'TP_HIT'
                
                else:  # SHORT
                    if current_price >= stop_loss:
                        should_close = True
                        exit_price = stop_loss
                        exit_reason = 'SL_HIT'
                    elif current_price <= take_profit:
                        should_close = True
                        exit_price = take_profit
                        exit_reason = 'TP_HIT'
                
                if should_close:
                    self.db.close_trade(trade['trade_id'], exit_price, exit_reason)
                    
                    # Get updated trade from DB with correct P&L (including fees)
                    conn = __import__('sqlite3').connect(self.db.db_path)
                    conn.row_factory = __import__('sqlite3').Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM trades WHERE trade_id = ?', (trade['trade_id'],))
                    closed_trade = dict(cursor.fetchone())
                    conn.close()
                    
                    # Use P&L from database (already includes fees deduction)
                    pnl = closed_trade['pnl']
                    pnl_pct = closed_trade['pnl_percentage']
                    total_fees = closed_trade['total_fees']
                    
                    # Log trade closure
                    pnl_sign = '+' if pnl >= 0 else ''
                    self.logger.info("="*70)
                    self.logger.info(f"TRADE CLOSED: {trade['trade_id']}")
                    self.logger.info(f"  Action: {action} @ ${trade['entry_price']}")
                    self.logger.info(f"  Exit: ${exit_price} ({exit_reason})")
                    self.logger.info(f"  Fees: ${total_fees:.4f} (entry + exit)")
                    self.logger.info(f"  P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%) [after fees]")
                    self.logger.info(f"  Setup: {trade.get('entry_setup', 'N/A')}")
                    
                    print(f"\n{'='*70}")
                    print(f"🔔 TRADE CLOSED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"{'='*70}")
                    print(f"Trade ID: {trade['trade_id']}")
                    print(f"Action: {action} @ ${trade['entry_price']}")
                    print(f"Exit: ${exit_price} ({exit_reason})")
                    print(f"Fees: ${total_fees:.4f}")
                    print(f"P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%) [after fees]")
                    
                    # Show updated stats
                    stats = self.db.get_trade_stats(symbol)
                    if stats['closed_trades'] > 0:
                        print(f"\nUpdated Stats:")
                        print(f"  Win rate: {stats['win_rate']:.1f}%")
                        print(f"  Total P&L: ${stats['total_pnl']:.2f}")
                        
                        self.logger.info(f"  Updated stats: Win rate {stats['win_rate']:.1f}%, Total P&L ${stats['total_pnl']:.2f}")
                    
                    print(f"{'='*70}\n")
                    self.logger.info("="*70)
                    
                    self.trades_closed += 1
                    trades_closed += 1
                
                trades_checked += 1
                
            except Exception as e:
                self.logger.error(f"Error checking trade {trade.get('trade_id', 'unknown')}: {e}")
                print(f"⚠️  Error checking trade {trade.get('trade_id', 'unknown')}: {e}")
        
        if trades_closed > 0:
            self.logger.info(f"Monitor cycle complete: {trades_checked} checked, {trades_closed} closed")
        
        self.last_monitor_time = time.time()
    
    def run(self):
        """Main bot loop"""
        self.logger.info("="*70)
        self.logger.info("BOT STARTING")
        self.logger.info(f"Symbol: {config.SYMBOL}")
        self.logger.info(f"Timeframes: {config.TIMEFRAME_HIGHER} / {config.TIMEFRAME_LOWER}")
        self.logger.info(f"Analysis interval: {self.analysis_interval}s ({self.analysis_interval//60}min)")
        self.logger.info(f"Monitor interval: {self.monitor_interval}s")
        self.logger.info("="*70)
        
        print(f"\n{'='*70}")
        print(f"🤖 AUTONOMOUS TRADING BOT STARTED")
        print(f"{'='*70}")
        print(f"Symbol: {config.SYMBOL}")
        print(f"Timeframes: {config.TIMEFRAME_HIGHER} (trend) + {config.TIMEFRAME_LOWER} (entry)")
        print(f"Analysis interval: {self.analysis_interval}s ({self.analysis_interval//60} min)")
        print(f"Monitor interval: {self.monitor_interval}s")
        print(f"\n🔄 Bot will:")
        print(f"  1. Run analysis every {self.analysis_interval//60} minutes")
        print(f"  2. Monitor open trades every {self.monitor_interval} seconds")
        print(f"  3. Auto-execute paper trades on LONG/SHORT signals")
        print(f"  4. Auto-close trades when SL/TP hit")
        print(f"\n⏹️  Press Ctrl+C to stop gracefully")
        print(f"📁 Logs: logs/trading_bot.log")
        print(f"{'='*70}\n")
        
        # Run first analysis immediately
        print(f"🚀 Running initial analysis...\n")
        self.logger.info("Running initial analysis...")
        self.run_analysis()
        
        # Calculate time to next candle for synchronized analyses
        wait_to_next_candle = self.calculate_next_candle_time(config.TIMEFRAME_LOWER)
        next_analysis_time = datetime.now() + timedelta(seconds=wait_to_next_candle)
        
        print(f"⏰ Next analysis synchronized to {config.TIMEFRAME_LOWER} candle close (+3s safety):")
        print(f"   Candle closes: {(next_analysis_time - timedelta(seconds=3)).strftime('%H:%M:%S')}")
        print(f"   Analysis at: {next_analysis_time.strftime('%H:%M:%S')} (after candle fully closed)")
        print(f"   Wait time: {wait_to_next_candle}s ({wait_to_next_candle//60}min {wait_to_next_candle%60}s)")
        print(f"   Then every {config.TIMEFRAME_LOWER} candle (+3s delay for complete data)")
        print(f"   ⏰ Bot will sync to 15-minute marks: XX:00, XX:15, XX:30, XX:45\n")
        
        self.logger.info(f"Next analysis at {next_analysis_time.strftime('%Y-%m-%d %H:%M:%S')} (synced to {config.TIMEFRAME_LOWER} candle)")
        self.logger.info("Bot configured to run at 15-minute marks (00, 15, 30, 45)")
        
        # Main loop
        cycle = 0
        while self.running:
            try:
                cycle += 1
                current_time = time.time()
                now = datetime.now()
                
                # Calculate time to next 15-minute mark (00, 15, 30, 45)
                current_minute = now.minute
                current_second = now.second
                
                # Find next 15-minute boundary
                next_quarter = ((current_minute // 15) + 1) * 15
                if next_quarter >= 60:
                    next_quarter = 0
                    minutes_to_next = 60 - current_minute
                else:
                    minutes_to_next = next_quarter - current_minute
                
                # Calculate seconds to next 15-minute mark
                seconds_to_next_quarter = (minutes_to_next * 60) - current_second
                
                # For first run or if we're past the 15-minute mark, analyze now
                time_since_analysis = current_time - self.last_analysis_time
                
                if self.analysis_count == 0:
                    # First run - do immediately
                    should_analyze = True
                    time_to_next = seconds_to_next_quarter
                elif self.analysis_count == 1:
                    # Second run - wait for next 15-minute mark
                    should_analyze = time_since_analysis >= wait_to_next_candle
                    time_to_next = seconds_to_next_quarter
                else:
                    # Regular runs - trigger at 15-minute marks (with small buffer to avoid missing)
                    # Trigger if we're within 10 seconds after a 15-minute mark AND haven't run recently
                    at_quarter_mark = (current_minute % 15 == 0 and current_second <= 10)
                    should_analyze = at_quarter_mark and time_since_analysis >= 60  # At least 1 min since last
                    time_to_next = seconds_to_next_quarter
                
                if should_analyze:
                    self.run_analysis()
                    
                    # Recalculate for next quarter
                    now = datetime.now()
                    current_minute = now.minute
                    current_second = now.second
                    next_quarter = ((current_minute // 15) + 1) * 15
                    if next_quarter >= 60:
                        next_quarter = 0
                        minutes_to_next = 60 - current_minute
                    else:
                        minutes_to_next = next_quarter - current_minute
                    time_to_next = (minutes_to_next * 60) - current_second
                
                # Check if time to monitor trades
                time_since_monitor = current_time - self.last_monitor_time
                if time_since_monitor >= self.monitor_interval:
                    self.monitor_trades()
                
                # Status update every 10 cycles
                if cycle % 10 == 0:
                    next_analysis = int(time_to_next) if 'time_to_next' in locals() else seconds_to_next_quarter
                    next_monitor = int(self.monitor_interval - time_since_monitor)
                    
                    # Calculate next analysis timestamp (next 15-minute mark)
                    now_for_calc = datetime.now()
                    current_min = now_for_calc.minute
                    next_qtr = ((current_min // 15) + 1) * 15
                    if next_qtr >= 60:
                        next_analysis_dt = now_for_calc.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                    else:
                        next_analysis_dt = now_for_calc.replace(minute=next_qtr, second=0, microsecond=0)
                    
                    status_msg = (f"Bot running... Cycle {cycle} | "
                                f"Next analysis: {next_analysis_dt.strftime('%H:%M:%S')} (in {next_analysis}s), "
                                f"Next monitor: {next_monitor}s")
                    print(f"⏰ [{datetime.now().strftime('%H:%M:%S')}] {status_msg}")
                    
                    # Log every hour
                    if cycle % 720 == 0:  # Every hour (720 * 5s = 3600s)
                        self.logger.info(f"Heartbeat: Cycle {cycle}, Analyses: {self.analysis_count}, "
                                       f"Trades created: {self.trades_created}, Trades closed: {self.trades_closed}")
                
                # Sleep short interval
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in bot loop: {e}", exc_info=True)
                print(f"⚠️  Error in bot loop: {e}")
                time.sleep(10)  # Wait before retry
        
        # Shutdown
        self.logger.info("="*70)
        self.logger.info("BOT SHUTDOWN INITIATED")
        self.logger.info(f"Total runtime cycles: {cycle}")
        self.logger.info(f"Total analyses run: {self.analysis_count}")
        self.logger.info(f"Total trades created: {self.trades_created}")
        self.logger.info(f"Total trades closed: {self.trades_closed}")
        
        print(f"\n{'='*70}")
        print(f"🛑 BOT STOPPED")
        print(f"{'='*70}")
        
        # Final stats
        stats = self.db.get_trade_stats(config.SYMBOL)
        print(f"\n📊 Final Statistics:")
        print(f"   Analyses run: {self.analysis_count}")
        print(f"   Trades created: {self.trades_created}")
        print(f"   Trades closed: {self.trades_closed}")
        print(f"   Total trades: {stats['total_trades']}")
        print(f"   Open: {stats['open_trades']} | Closed: {stats['closed_trades']}")
        if stats['closed_trades'] > 0:
            print(f"   Win rate: {stats['win_rate']:.1f}%")
            print(f"   Total P&L: ${stats['total_pnl']:.2f}")
        
        self.logger.info(f"Final stats: Win rate {stats.get('win_rate', 0):.1f}%, P&L ${stats.get('total_pnl', 0):.2f}")
        self.logger.info("BOT STOPPED")
        self.logger.info("="*70)
        
        print(f"\n👋 Goodbye!\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomous Trading Bot')
    parser.add_argument('--analysis-interval', type=int, default=900,
                       help='Analysis interval in seconds (default 900 = 15 min)')
    parser.add_argument('--monitor-interval', type=int, default=60,
                       help='Monitor interval in seconds (default 60 = 1 min)')
    parser.add_argument('--run-once', action='store_true',
                       help='Run analysis once and exit (testing mode)')
    
    args = parser.parse_args()
    
    if args.run_once:
        # Testing mode - single analysis
        print("🧪 Running in TEST mode (single analysis)\n")
        bot = TradingBot(args.analysis_interval, args.monitor_interval)
        bot.run_analysis()
        bot.monitor_trades()
    else:
        # Continuous mode
        bot = TradingBot(args.analysis_interval, args.monitor_interval)
        bot.run()


if __name__ == "__main__":
    main()

