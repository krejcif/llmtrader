#!/usr/bin/env python
"""Autonomous Trading Bot - Dynamic multi-strategy system"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.state import TradingState
from agents.data_collector_generic import collect_market_data_generic
from agents.decision_generic import make_decision_generic
from agents.news_collector import collect_stock_news
from agents.btc_collector import collect_btc_data
from agents.ixic_collector import collect_ixic_data
from agents.paper_trading import execute_paper_trade
from agents.live_trading import execute_live_trade
from agents.monitoring import MonitoringAgent
from utils.database import TradingDatabase
from utils.binance_client import BinanceClient
from strategy_config import get_active_strategies, get_all_intervals, get_min_interval, get_strategies_by_interval
import config
from datetime import datetime, timedelta
import time
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import json
import logging
from logging.handlers import RotatingFileHandler


class DynamicTradingBot:
    """Dynamic autonomous trading bot with configurable multi-strategy support"""
    
    def __init__(self, monitor_interval: int = 60):
        """
        Initialize dynamic trading bot
        
        Args:
            monitor_interval: Seconds between trade checks (default 60 = 1 min)
        """
        self.monitor_interval = monitor_interval
        self.running = True
        self.db = TradingDatabase()
        self.binance_client = BinanceClient()
        
        # Load active strategies from config
        self.strategies = get_active_strategies()
        self.all_intervals = get_all_intervals()
        self.min_interval = get_min_interval()
        
        # Track last run time for each interval
        self.last_run_time = {interval: 0 for interval in self.all_intervals}
        self.last_run_minute = {interval: -1 for interval in self.all_intervals}  # Track UTC minute
        self.last_monitor_time = 0
        self.last_monitoring_agent_time = 0  # Track monitoring agent runs (every 60s)
        
        # Setup logging first
        self.setup_logging()
        
        # Monitoring agent (runs independently every minute) - pass bot's logger
        self.monitoring_agent = MonitoringAgent(logger_instance=self.logger)
        self.monitoring_agent_interval = 60  # Run every 60 seconds
        
        # Counters
        self.analysis_counts = {s.name: 0 for s in self.strategies}
        self.trades_created = 0
        self.trades_closed = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info(f"Loaded {len(self.strategies)} active strategies:")
        for s in self.strategies:
            self.logger.info(f"  - {s}")
    
    def setup_logging(self):
        """Setup comprehensive logging system"""
        # Create logs directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(project_root, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('DynamicTradingBot')
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
            '%(asctime)s | %(levelname)8s | %(funcName)37s | %(message)s',
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
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.warning("Shutdown signal received. Stopping bot gracefully...")
        print(f"\n\n⏹️  Shutdown signal received. Stopping bot gracefully...")
        self.running = False
    
    def collect_shared_data(self, state: TradingState) -> TradingState:
        """Collect shared data (news, BTC, IXIC) - run once per cycle"""
        try:
            # Ensure symbol is preserved
            symbol = state.get('symbol', config.SYMBOL)
            
            # Merge shared data into state (collectors return partial dicts)
            state.update(collect_stock_news(state))
            state.update(collect_btc_data(state))
            state.update(collect_ixic_data(state))
            
            # DEBUG: Check if btc_data is in state
            print(f"   [DEBUG] After shared data collection:")
            print(f"   - btc_data in state: {'btc_data' in state}")
            print(f"   - btc_data value: {state.get('btc_data', 'MISSING')}")
            
            # Restore symbol if it was lost
            if 'symbol' not in state:
                state['symbol'] = symbol
        except Exception as e:
            self.logger.error(f"Error collecting shared data: {e}")
        return state
    
    def run_strategy(self, strategy, state: TradingState) -> TradingState:
        """Run a single strategy: data -> analysis -> decision"""
        try:
            self.analysis_counts[strategy.name] += 1
            
            print(f"\n📊 Running {strategy.name.upper()} strategy ({strategy.timeframe_higher}/{strategy.timeframe_lower})...")
            self.logger.info(f"Running {strategy.name} strategy (TF: {strategy.timeframe_higher}/{strategy.timeframe_lower})")
            
            # Ensure symbol is in state
            if 'symbol' not in state:
                state['symbol'] = config.SYMBOL
                self.logger.warning(f"Symbol was missing in state for {strategy.name}, added {config.SYMBOL}")
            
            # 1. Collect market data for this strategy's timeframes
            state = collect_market_data_generic(
                state, 
                strategy.name,
                strategy.timeframe_higher,
                strategy.timeframe_lower
            )
            
            # 2. Analyze market data (using strategy-specific analysis function)
            state = strategy.analysis_func(
                state,
                strategy.name,
                strategy.timeframe_higher,
                strategy.timeframe_lower
            )
            
            # 3. Make trading decision
            state = make_decision_generic(
                state,
                strategy.name,
                strategy.decision_func
            )
            
            # Log result
            rec_key = f"recommendation_{strategy.name}"
            recommendation = state.get(rec_key)
            
            if recommendation:
                action = recommendation['action']
                confidence = recommendation.get('confidence', 'N/A')
                
                print(f"✅ [{strategy.name.upper()}] Decision: {action} ({confidence})")
                self.logger.info(f"[{strategy.name}] Decision: {action} (confidence: {confidence})")
                
                if action in ['LONG', 'SHORT']:
                    rm = recommendation.get('risk_management', {})
                    print(f"   Entry: ${rm.get('entry', 'N/A')} | SL: ${rm.get('stop_loss', 'N/A')} | TP: ${rm.get('take_profit', 'N/A')}")
                    self.logger.info(f"   Entry ${rm.get('entry')}, SL ${rm.get('stop_loss')}, TP ${rm.get('take_profit')}, R/R 1:{rm.get('risk_reward_ratio')}")
            else:
                print(f"⚠️  [{strategy.name.upper()}] No recommendation generated")
                self.logger.warning(f"[{strategy.name}] No recommendation generated")
            
        except Exception as e:
            self.logger.error(f"Error running strategy {strategy.name}: {e}", exc_info=True)
            print(f"❌ Error running {strategy.name}: {e}")
        
        return state
    
    def run_strategy_wrapper(self, strategy, base_state):
        """
        Wrapper for run_strategy that returns strategy-specific data only
        Used for parallel execution with ThreadPoolExecutor
        """
        # Each thread gets its own copy of base state
        thread_state = deepcopy(base_state)
        
        # Set strategy-specific symbol (Fáze 2: multi-symbol support)
        thread_state['symbol'] = strategy.symbol
        
        # Run strategy (modifies thread_state)
        result_state = self.run_strategy(strategy, thread_state)
        
        # Return only strategy-specific keys (not shared data like news, btc)
        strategy_keys = [
            f'market_data_{strategy.name}',
            f'analysis_{strategy.name}',
            f'recommendation_{strategy.name}'
        ]
        
        strategy_result = {
            'strategy_name': strategy.name,
            'symbol': strategy.symbol,  # Include symbol for multi-symbol support
            'data': {key: result_state.get(key) for key in strategy_keys if key in result_state}
        }
        
        # IMPORTANT: Add symbol to recommendation so paper_trading knows which symbol to trade
        rec_key = f'recommendation_{strategy.name}'
        if rec_key in strategy_result['data'] and strategy_result['data'][rec_key]:
            strategy_result['data'][rec_key]['symbol'] = strategy.symbol
        
        return strategy_result
    
    def run_analysis_interval(self, interval_minutes: int):
        """Run all strategies scheduled for this interval (PARALLEL execution)"""
        strategies = get_strategies_by_interval(interval_minutes)
        
        if not strategies:
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = time.time()
        
        self.logger.info("="*70)
        self.logger.info(f"ANALYSIS CYCLE - {interval_minutes} min interval - {timestamp}")
        self.logger.info(f"Running {len(strategies)} strateg{'y' if len(strategies) == 1 else 'ies'} PARALLEL: {', '.join(s.name for s in strategies)}")
        self.logger.info("="*70)
        
        print(f"\n{'='*70}")
        print(f"📊 ANALYSIS CYCLE - {interval_minutes} min interval - {timestamp}")
        print(f"⚡ Running {len(strategies)} strateg{'y' if len(strategies) == 1 else 'ies'} in PARALLEL: {', '.join(s.name for s in strategies)}")
        print(f"{'='*70}")
        
        try:
            # Initialize state
            initial_state: TradingState = {
                "symbol": config.SYMBOL,
                "error": None
            }
            
            # Collect shared data once (news, BTC, IXIC)
            print(f"\n📰 Collecting shared data (news, BTC, IXIC)...")
            base_state = self.collect_shared_data(initial_state)
            
            # Run strategies in PARALLEL using ThreadPoolExecutor
            print(f"\n⚡ Running strategies in parallel threads...")
            strategy_results = []
            
            with ThreadPoolExecutor(max_workers=len(strategies)) as executor:
                # Submit all strategy runs to thread pool
                future_to_strategy = {
                    executor.submit(self.run_strategy_wrapper, strategy, base_state): strategy 
                    for strategy in strategies
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_strategy):
                    strategy = future_to_strategy[future]
                    try:
                        result = future.result()
                        strategy_results.append(result)
                        print(f"   ✓ {result['strategy_name'].upper()} completed")
                    except Exception as exc:
                        self.logger.error(f"Strategy {strategy.name} generated exception: {exc}", exc_info=True)
                        print(f"   ✗ {strategy.name.upper()} failed: {exc}")
            
            # Merge all strategy results into final state
            state = deepcopy(base_state)
            for result in strategy_results:
                state.update(result['data'])
            
            elapsed = time.time() - start_time
            print(f"\n⚡ All strategies completed in {elapsed:.2f}s (parallel execution)")
            self.logger.info(f"Parallel execution completed in {elapsed:.2f}s")
            
            # DEBUG: Show what recommendations are in state
            print(f"\n🔍 DEBUG: Recommendations in state:")
            for key, value in state.items():
                if key.startswith('recommendation_'):
                    strategy_name = key.replace('recommendation_', '')
                    action = value.get('action', 'UNKNOWN') if value else 'None'
                    print(f"   {strategy_name}: {action}")
            
            # Execute trades for all strategies
            print(f"\n💼 Executing trades...")
            
            # Create strategy_configs dict for live trading
            strategy_configs = {s.name: s for s in strategies}
            
            # Check if any strategy has live_trading enabled
            live_strategies = [s for s in strategies if s.live_trading]
            paper_strategies = [s for s in strategies if not s.live_trading]
            
            # Log trading mode for each strategy
            self.logger.info("")
            self.logger.info(f"🎯 Trading Mode Summary ({len(strategies)} active strategies):")
            for s in strategies:
                mode = "🔴 LIVE" if s.live_trading else "📝 PAPER"
                self.logger.info(f"   [{s.name.upper()}] {mode}")
            
            # PAPER TRADING (for strategies with live_trading=False)
            if paper_strategies:
                self.logger.info(f"\n📝 Executing Paper Trading for {len(paper_strategies)} strategies: {', '.join(s.name for s in paper_strategies)}")
                state = execute_paper_trade(state)
            else:
                self.logger.info(f"\n📝 No Paper Trading strategies (all are Live or disabled)")
            
            # LIVE TRADING (for strategies with live_trading=True)
            if live_strategies:
                demo_str = "DEMO/TESTNET" if config.BINANCE_DEMO else "REAL ACCOUNT"
                self.logger.info(f"\n🔴 Executing Live Trading for {len(live_strategies)} strategies ({demo_str}): {', '.join(s.name for s in live_strategies)}")
                state = execute_live_trade(state, strategy_configs)
            else:
                self.logger.info(f"\n🔴 No Live Trading strategies (all are Paper or disabled)")
            
            if not live_strategies and not paper_strategies:
                self.logger.info(f"\n⚠️  No trading strategies enabled")
            
            # Trade execution summary
            if state.get('trade_execution', {}).get('executed'):
                trades = state['trade_execution'].get('trades', [])
                is_live = state['trade_execution'].get('live', False)
                trade_type = "LIVE" if is_live else "PAPER"
                
                self.logger.info(f"\n✅ {len(trades)} {trade_type} trade(s) executed:")
                for trade_info in trades:
                    binance_ids = trade_info.get('binance_order_ids', [])
                    binance_info = f" | Binance: {binance_ids}" if binance_ids else ""
                    
                    # For live trades use binance_order_id, for paper trades use trade_id
                    if is_live:
                        trade_id = f"Binance Order {binance_ids[0] if binance_ids else 'N/A'}"
                    else:
                        trade_id = trade_info.get('trade_id', 'N/A')
                    
                    self.logger.info(f"   [{trade_info['strategy'].upper()}] {trade_id} - {trade_info.get('action', 'N/A')}{binance_info}")
                self.trades_created += len(trades)
            else:
                self.logger.info("\nℹ️  No trades executed (all NEUTRAL)")
            
            self.logger.info(f"\n{'='*70}\n")
            
            self.last_run_time[interval_minutes] = time.time()
            self.logger.info(f"Analysis cycle complete for {interval_minutes}min interval")
            
        except Exception as e:
            self.logger.error(f"Error during analysis cycle: {e}", exc_info=True)
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
                    self.logger.info(f"  Strategy: {trade['strategy']}")
                    self.logger.info(f"  Action: {action} @ ${trade['entry_price']}")
                    self.logger.info(f"  Exit: ${exit_price} ({exit_reason})")
                    self.logger.info(f"  Fees: ${total_fees:.4f} (entry + exit)")
                    self.logger.info(f"  P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%) [after fees]")
                    
                    print(f"\n{'='*70}")
                    print(f"🔔 TRADE CLOSED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"{'='*70}")
                    print(f"Trade ID: {trade['trade_id']}")
                    print(f"Strategy: {trade['strategy']}")
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
    
    def run_monitoring_agent_async(self):
        """
        Run monitoring agent in a separate thread (non-blocking).
        This allows the agent to run every minute without blocking the main trading cycle.
        """
        def _run_agent():
            try:
                self.monitoring_agent.run()
            except Exception as e:
                self.logger.error(f"Error in monitoring agent: {e}")
                import traceback
                traceback.print_exc()
        
        # Submit to thread pool for async execution
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(_run_agent)
    
    def run(self):
        """Main bot loop with dynamic strategy scheduling"""
        self.logger.info("="*70)
        self.logger.info("DYNAMIC BOT STARTING")
        self.logger.info(f"Symbol: {config.SYMBOL}")
        self.logger.info(f"Active strategies: {len(self.strategies)}")
        for s in self.strategies:
            self.logger.info(f"  - {s.name}: {s.timeframe_higher}/{s.timeframe_lower} every {s.interval_minutes}min")
        self.logger.info(f"Unique intervals: {self.all_intervals} minutes")
        self.logger.info(f"Monitor interval: {self.monitor_interval}s")
        self.logger.info("="*70)
        
        print(f"\n{'='*70}")
        print(f"🤖 DYNAMIC AUTONOMOUS TRADING BOT STARTED")
        print(f"{'='*70}")
        print(f"Symbol: {config.SYMBOL}")
        print(f"\n📋 Active Strategies ({len(self.strategies)}):")
        for s in self.strategies:
            print(f"  • {s.name.upper()}: {s.timeframe_higher}/{s.timeframe_lower} → Every {s.interval_minutes} min")
        print(f"\n⏱️  Scheduling (CRON-style - UTC time, synced with Binance candles):")
        for interval in self.all_intervals:
            strats = get_strategies_by_interval(interval)
            if interval == 5:
                times = "XX:00, XX:05, XX:10, XX:15, XX:20, XX:25, XX:30, XX:35, XX:40, XX:45, XX:50, XX:55 UTC"
            elif interval == 15:
                times = "XX:00, XX:15, XX:30, XX:45 UTC"
            elif interval == 60:
                times = "XX:00 UTC"
            else:
                times = f"Every {interval} min (UTC)"
            print(f"  • {', '.join(s.name for s in strats)}: {times}")
        
        # Show current time info
        now_local = datetime.now()
        now_utc = datetime.utcnow()
        print(f"\n🕐 Time info:")
        print(f"  • Local time: {now_local.strftime('%H:%M:%S')}")
        print(f"  • UTC time: {now_utc.strftime('%H:%M:%S')} (Binance uses UTC)")
        
        print(f"\n🔄 Bot will:")
        print(f"  1. Run strategies at exact UTC time marks (synchronized with Binance candle closes)")
        print(f"  2. Monitor open trades every {self.monitor_interval} seconds")
        print(f"  3. Run monitoring agent every {self.monitoring_agent_interval} seconds (orphaned orders cleanup)")
        print(f"  4. Auto-execute PAPER trades on LONG/SHORT signals (always)")
        if config.ENABLE_LIVE_TRADING:
            print(f"  5. Auto-execute LIVE trades (REAL MONEY - ${config.LIVE_POSITION_SIZE} per trade) ⚠️")
            print(f"  6. Auto-close trades when SL/TP hit (via Binance orders)")
        else:
            print(f"  5. LIVE trading: DISABLED (paper trading only)")
            print(f"  6. Auto-close paper trades when SL/TP hit")
        print(f"\n⏹️  Press Ctrl+C to stop gracefully")
        print(f"📁 Logs: logs/trading_bot.log")
        print(f"{'='*70}\n")
        
        # Run initial analysis for all strategies (good for testing)
        print(f"🚀 Running initial analysis for all strategies...\n")
        self.logger.info("Running initial analysis for all strategies...")
        for interval in self.all_intervals:
            self.run_analysis_interval(interval)
        
        print(f"\n✅ Initial analysis complete!")
        print(f"📊 Now waiting for CRON schedule...\n")
        
        # Show when next runs will happen
        now_utc = datetime.utcnow()
        for interval in self.all_intervals:
            current_minute_utc = now_utc.minute
            minutes_to_next = interval - (current_minute_utc % interval)
            if minutes_to_next == 0:
                minutes_to_next = interval
            next_minute = (current_minute_utc + minutes_to_next) % 60
            next_hour = now_utc.hour if (current_minute_utc + minutes_to_next) < 60 else (now_utc.hour + 1) % 24
            strats = get_strategies_by_interval(interval)
            print(f"  • {', '.join(s.name for s in strats)}: Next CRON run at {next_hour:02d}:{next_minute:02d} UTC")
        print()
        
        # Main loop
        cycle = 0
        while self.running:
            try:
                cycle += 1
                current_time = time.time()
                now = datetime.now()
                
                # Check each interval to see if it's time to run (CRON-STYLE with UTC)
                for interval_minutes in self.all_intervals:
                    # Use UTC time (Binance candles are in UTC)
                    now_utc = datetime.utcnow()
                    current_minute_utc = now_utc.minute
                    
                    # CRON-STYLE: Check if we're at the right UTC time mark
                    # For 5min: run at XX:00, XX:05, XX:10, XX:15, XX:20, XX:25, etc.
                    # For 15min: run at XX:00, XX:15, XX:30, XX:45
                    is_time_mark = (current_minute_utc % interval_minutes == 0)
                    
                    # Check if we haven't already run this UTC minute
                    is_new_minute = (current_minute_utc != self.last_run_minute[interval_minutes])
                    
                    # Run if we're at time mark AND it's a new minute (haven't run yet)
                    should_run = is_time_mark and is_new_minute
                    
                    if should_run:
                        self.run_analysis_interval(interval_minutes)
                        self.last_run_minute[interval_minutes] = current_minute_utc
                
                # Check if time to monitor trades
                time_since_monitor = current_time - self.last_monitor_time
                if time_since_monitor >= self.monitor_interval:
                    self.monitor_trades()
                
                # Check if time to run monitoring agent (every 60 seconds, async)
                time_since_monitoring_agent = current_time - self.last_monitoring_agent_time
                if time_since_monitoring_agent >= self.monitoring_agent_interval:
                    self.run_monitoring_agent_async()
                    self.last_monitoring_agent_time = current_time
                
                # Status update every 10 cycles
                if cycle % 10 == 0:
                    now_utc = datetime.utcnow()
                    next_runs = []
                    for interval_minutes in self.all_intervals:
                        current_minute_utc = now_utc.minute
                        current_second_utc = now_utc.second
                        
                        # Calculate next UTC cron time
                        minutes_to_next = interval_minutes - (current_minute_utc % interval_minutes)
                        if minutes_to_next == 0 and current_second_utc > 0:
                            minutes_to_next = interval_minutes
                        seconds_to_next = (minutes_to_next * 60) - current_second_utc
                        
                        next_minute = (current_minute_utc + minutes_to_next) % 60
                        
                        strats = get_strategies_by_interval(interval_minutes)
                        strat_names = ', '.join(s.name for s in strats)
                        next_runs.append(f"{strat_names} at {now_utc.hour:02d}:{next_minute:02d} UTC ({seconds_to_next}s)")
                    
                    next_monitor = int(self.monitor_interval - time_since_monitor)
                    
                    status_msg = f"Bot cycle {cycle} | Next: {' | '.join(next_runs)} | Monitor: {next_monitor}s"
                    print(f"⏰ [{datetime.now().strftime('%H:%M:%S')} local / {datetime.utcnow().strftime('%H:%M:%S')} UTC] {status_msg}")
                    
                    # Log every hour
                    if cycle % 720 == 0:  # Every hour (720 * 5s = 3600s)
                        total_analyses = sum(self.analysis_counts.values())
                        self.logger.info(f"Heartbeat: Cycle {cycle}, Total analyses: {total_analyses}, "
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
        self.logger.info(f"Strategy analysis counts: {self.analysis_counts}")
        self.logger.info(f"Total trades created: {self.trades_created}")
        self.logger.info(f"Total trades closed: {self.trades_closed}")
        
        print(f"\n{'='*70}")
        print(f"🛑 BOT STOPPED")
        print(f"{'='*70}")
        
        # Final stats
        stats = self.db.get_trade_stats(config.SYMBOL)
        print(f"\n📊 Final Statistics:")
        print(f"   Strategy analyses: {self.analysis_counts}")
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
    
    parser = argparse.ArgumentParser(description='Dynamic Autonomous Trading Bot')
    parser.add_argument('--monitor-interval', type=int, default=60,
                       help='Monitor interval in seconds (default 60 = 1 min)')
    parser.add_argument('--run-once', action='store_true',
                       help='Run analysis once and exit (testing mode)')
    
    args = parser.parse_args()
    
    if args.run_once:
        # Testing mode - single analysis for all strategies
        print("🧪 Running in TEST mode (single analysis for all strategies)\n")
        bot = DynamicTradingBot(args.monitor_interval)
        for interval in bot.all_intervals:
            bot.run_analysis_interval(interval)
        bot.monitor_trades()
    else:
        # Continuous mode
        bot = DynamicTradingBot(args.monitor_interval)
        bot.run()


if __name__ == "__main__":
    main()

