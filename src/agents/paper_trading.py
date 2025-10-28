"""Paper Trading Agent - Executes simulated trades and stores in database (Multi-Strategy)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.database import TradingDatabase
from datetime import datetime, timezone, timedelta
import config
import logging

# Get parent logger (will use DynamicTradingBot's logger)
logger = logging.getLogger('DynamicTradingBot.PaperTrading')


def execute_paper_trade(state: TradingState) -> TradingState:
    """
    Execute paper trades for ALL strategies (dynamically finds all recommendation_* keys)
    
    Args:
        state: Current trading state with recommendations from all strategies
        
    Returns:
        Updated state with trade execution info
    """
    logger.info("")
    logger.info("📝 === PAPER TRADING EXECUTION START ===")
    logger.info("📝 Processing paper trades for all strategies...")
    
    try:
        recommendations = []
        
        # Dynamically collect ALL recommendations from state
        # Find all keys starting with 'recommendation_'
        for key, value in state.items():
            if key.startswith('recommendation_') and value is not None:
                strategy_name = key.replace('recommendation_', '')
                recommendations.append((strategy_name, value))
        
        if not recommendations:
            logger.info("📝 ❌ No recommendations found in state")
            logger.info("📝 === PAPER TRADING EXECUTION END (No recommendations) ===\n")
            return state
        
        logger.info(f"📝 ✅ Found {len(recommendations)} recommendation(s): {', '.join(r[0] for r in recommendations)}")
        
        executed_trades = []
        
        # Try to get analysis and market_data (may be strategy-specific)
        # For backward compatibility, try generic keys first, then fall back to strategy-specific
        analysis = state.get('analysis')
        market_data = state.get('market_data')
        
        # Execute trade for each strategy
        for strategy_name, recommendation in recommendations:
            logger.info(f"\n📝 [{strategy_name.upper()}] Processing recommendation...")
            action = recommendation['action']
            confidence = recommendation.get('confidence', 'unknown')
            logger.info(f"📝 [{strategy_name.upper()}] Decision: {action} (confidence: {confidence})")
            
            # Get strategy-specific data if available, otherwise use generic
            strategy_market_data = state.get(f'market_data_{strategy_name}') or market_data
            strategy_analysis = state.get(f'analysis_{strategy_name}') or analysis
            
            # Ensure we have valid data (not None)
            if not strategy_analysis:
                logger.info(f"📝 ❌ [{strategy_name.upper()}] SKIPPED - No analysis data available")
                logger.info(f"📝 [{strategy_name.upper()}] Reason: analysis is None or empty")
                continue
            
            # LOG STRATEGY RUN (always log, even if not executed)
            db_log = TradingDatabase()
            log_data = {
                'symbol': state['symbol'],
                'strategy': strategy_name,
                'action': action,
                'confidence': recommendation.get('confidence'),
                'reasoning': recommendation.get('reasoning'),
                'key_factors': recommendation.get('key_factors', []),
                'market_data': {
                    'current_price': strategy_market_data.get('current_price') if strategy_market_data else None,
                    'volume_24h': strategy_market_data.get('volume_24h') if strategy_market_data else None
                },
                'analysis_summary': strategy_analysis.get('summary') if strategy_analysis else None,
                'risk_management': recommendation.get('risk_management', {}),
                'executed': False,
                'execution_reason': None
            }
            
            # Only execute for LONG or SHORT
            if action not in ['LONG', 'SHORT']:
                log_data['execution_reason'] = f"No trade - {action}"
                db_log.log_strategy_run(log_data)
                logger.info(f"📝 ℹ️  [{strategy_name.upper()}] NO TRADE EXECUTED - Action is {action} (not LONG or SHORT)")
                logger.info(f"📝 [{strategy_name.upper()}] Trade skipped - waiting for LONG or SHORT signal")
                continue
            
            # Check if strategy already has open trade (RISK MANAGEMENT!)
            db_check = TradingDatabase()
            symbol = recommendation.get('symbol', state['symbol'])
            existing_open = db_check.get_open_trades(symbol)  # trades table = only paper trades
            
            # Filter for this strategy
            strategy_open = [t for t in existing_open if t.get('strategy') == strategy_name]
            
            logger.info(f"📝 [{strategy_name.upper()}] Open trades check: {len(strategy_open)} existing open trade(s)")
            
            if strategy_open:
                # Check if opposite direction - if so, close existing trades
                existing_direction = strategy_open[0].get('action', 'UNKNOWN')  # Fixed: use 'action', not 'side'
                opposite_direction = (existing_direction == 'LONG' and action == 'SHORT') or \
                                   (existing_direction == 'SHORT' and action == 'LONG')
                
                if opposite_direction:
                    logger.info(f"📝 [{strategy_name.upper()}] 🔄 OPPOSITE SIGNAL DETECTED!")
                    logger.info(f"📝 [{strategy_name.upper()}] Existing: {existing_direction}, New signal: {action}")
                    
                    # Close all open trades for this strategy (on opposite signal)
                    # Use last CLOSED candle price (not ticker) to avoid look-ahead bias
                    tf_lower = strategy_analysis.get('indicators', {}).get('lower_tf', {}).get('timeframe')
                    if tf_lower and strategy_market_data and 'timeframes' in strategy_market_data:
                        candles = strategy_market_data['timeframes'][tf_lower]
                        current_price = float(candles['close'].iloc[-1])
                    else:
                        # Fallback to ticker only if closed candle data not available
                        current_price = strategy_market_data.get('current_price') if strategy_market_data else market_data.get('current_price')
                        logger.info(f"📝 ⚠️  WARNING: Using ticker price as fallback (no closed candle data)")
                    from datetime import datetime as dt
                    
                    logger.info(f"📝 [{strategy_name.upper()}] Closing {len(strategy_open)} {existing_direction} trade(s)")
                    logger.info(f"📝 [{strategy_name.upper()}] Exit price: ${current_price:.2f} (last closed candle)")
                    
                    for trade in strategy_open:
                        try:
                            # Calculate P&L
                            entry_price = trade['entry_price']
                            size = trade['size']
                            
                            if existing_direction == 'LONG':
                                pnl = (current_price - entry_price) * size
                                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                            else:  # SHORT
                                pnl = (entry_price - current_price) * size
                                pnl_pct = ((entry_price - current_price) / entry_price) * 100
                            
                            # Close trade (database calculates P&L automatically)
                            db_close = TradingDatabase()
                            db_close.close_trade(
                                trade_id=trade['trade_id'],
                                exit_price=current_price,
                                exit_reason=f"OPPOSITE_SIGNAL ({action})"
                            )
                            
                            logger.info(f"   ✅ Closed {trade['trade_id']}: ${entry_price:.2f} → ${current_price:.2f}")
                            logger.info(f"      P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
                            
                        except Exception as e:
                            logger.info(f"   ❌ Error closing trade {trade['trade_id']}: {str(e)}")
                    
                    # DO NOT open new trade in opposite direction - just close and wait for cooldown
                    logger.info(f"📝 [{strategy_name.upper()}] ✅ All trades closed successfully")
                    logger.info(f"📝 [{strategy_name.upper()}] ⏸️  COOLDOWN ACTIVATED - No new {action} trade will be opened")
                    logger.info(f"📝 [{strategy_name.upper()}] Reason: Risk management - waiting for next clear signal")
                    
                    # Log this event
                    log_data['executed'] = False
                    log_data['execution_reason'] = f"Closed {existing_direction} on opposite {action} signal - cooldown active"
                    db_log.log_strategy_run(log_data)
                    
                    # Skip opening new trade (cooldown will apply next time)
                    continue
                    
                else:
                    # Same direction - skip (don't double up)
                    log_data['execution_reason'] = f"Already has {len(strategy_open)} open {existing_direction} trade(s)"
                    db_log.log_strategy_run(log_data)
                    logger.info(f"📝 ⚠️  [{strategy_name.upper()}] NO TRADE EXECUTED - Already have open {existing_direction} position")
                    logger.info(f"📝 [{strategy_name.upper()}] Existing trade: {strategy_open[0]['trade_id']}")
                    logger.info(f"📝 [{strategy_name.upper()}] Reason: Risk management - one position per strategy at a time")
                    continue
            
            # COOLDOWN CHECK: Prevent re-entry too soon after closing previous trade
            # (Cooldown applies ALWAYS, even for opposite direction trades)
            conn = db_check.conn = __import__('sqlite3').connect(db_check.db_path)
            cursor = conn.cursor()
            
            # Get last closed trade for this strategy
            cursor.execute("""
                SELECT exit_time, exit_price, exit_reason 
                FROM trades 
                WHERE strategy = ? AND symbol = ? AND status = 'CLOSED'
                ORDER BY exit_time DESC 
                LIMIT 1
            """, (strategy_name, state['symbol']))
            
            last_closed = cursor.fetchone()
            conn.close()
            
            if last_closed and last_closed[0]:
                from datetime import datetime as dt
                # Handle both 'Z' and standard ISO format
                timestamp_str = last_closed[0].replace('Z', '+00:00') if 'Z' in last_closed[0] else last_closed[0]
                last_exit_time = dt.fromisoformat(timestamp_str)
                
                # Make both datetimes timezone-aware for comparison
                if last_exit_time.tzinfo is None:
                    last_exit_time = last_exit_time.replace(tzinfo=timezone.utc)
                current_time = dt.now(timezone.utc)
                
                time_since_exit = (current_time - last_exit_time).total_seconds() / 60
                
                # COOLDOWN: Strategy-specific periods
                COOLDOWN_MAP = {
                    'sol': 30,
                    'sol_fast': 20,
                    'eth': 30,
                    'eth_fast': 20,
                    'doge': 30,
                    'doge_fast': 20,
                    'xrp': 30,
                    'xrp_fast': 20
                }
                
                cooldown_minutes = COOLDOWN_MAP.get(strategy_name, 30)  # Default 30min
                
                if time_since_exit < cooldown_minutes:
                    remaining = cooldown_minutes - time_since_exit
                    log_data['execution_reason'] = f"COOLDOWN - Wait {remaining:.1f}min"
                    db_log.log_strategy_run(log_data)
                    logger.info(f"📝 ⏳ [{strategy_name.upper()}] NO TRADE EXECUTED - COOLDOWN ACTIVE")
                    logger.info(f"📝 [{strategy_name.upper()}] Cooldown period: {cooldown_minutes} minutes")
                    logger.info(f"📝 [{strategy_name.upper()}] Time since last exit: {time_since_exit:.1f} minutes")
                    logger.info(f"📝 [{strategy_name.upper()}] Remaining cooldown: {remaining:.1f} minutes")
                    logger.info(f"📝 [{strategy_name.upper()}] Reason: Risk management - preventing over-trading")
                    continue
                else:
                    logger.info(f"📝 [{strategy_name.upper()}] ✅ Cooldown check passed ({time_since_exit:.1f}min since last exit)")
            
            # Check if we have risk management
            if 'risk_management' not in recommendation:
                log_data['execution_reason'] = "No risk management data"
                db_log.log_strategy_run(log_data)
                logger.info(f"📝 ❌ [{strategy_name.upper()}] NO TRADE EXECUTED - Missing risk management data")
                logger.info(f"📝 [{strategy_name.upper()}] Reason: Cannot execute trade without SL/TP levels")
                continue
            
            logger.info(f"📝 [{strategy_name.upper()}] ✅ All pre-checks passed - Proceeding with trade execution")
            risk_mgmt = recommendation['risk_management']
            
            # Initialize database
            db = TradingDatabase()
            
            # Create 2 PARTIAL TRADES (scale out strategy)
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            
            # Calculate partial TP (50% of distance to full TP)
            entry = risk_mgmt['entry']
            original_sl = risk_mgmt['stop_loss']
            
            # Calculate TP levels
            full_tp = risk_mgmt['take_profit']
            if action == 'LONG':
                tp_distance = full_tp - entry
                partial_tp = entry + (tp_distance * 0.5)  # 50% TP
            else:  # SHORT
                tp_distance = entry - full_tp
                partial_tp = entry - (tp_distance * 0.5)
            
            # DIFFERENT SL for each partial trade
            # Partial 1: Same SL (needs to close first)
            # Partial 2: Move to break-even after partial 1 TP
            # For now: Partial 1 keeps original SL, Partial 2 gets tighter SL
            if action == 'LONG':
                sl_partial1 = original_sl  # Original SL for quick exit
                sl_partial2 = entry - (entry - original_sl) * 0.5  # 50% tighter (break-even style)
            else:  # SHORT
                sl_partial1 = original_sl  # Original SL for quick exit
                sl_partial2 = entry + (original_sl - entry) * 0.5  # 50% tighter
            
            # FIXED POSITION SIZE: $10,000 split into 2 partial trades (50% each)
            TOTAL_POSITION_USD = 10000.0
            partial_position_usd = TOTAL_POSITION_USD / 2  # $5,000 per partial
            
            # Calculate size (quantity of asset to buy) for each partial
            size_partial1 = partial_position_usd / entry  # Quantity for $5,000
            size_partial2 = partial_position_usd / entry  # Quantity for $5,000
            
            # TRADE 1: Partial (50% TP) - Original SL
            trade_data_1 = {
                "symbol": recommendation.get('symbol', state['symbol']),  # Prefer symbol from recommendation
                "strategy": strategy_name,
                "action": action,
                "confidence": recommendation.get('confidence', 'unknown'),
                "entry_price": entry,
                "stop_loss": round(sl_partial1, 2),
                "take_profit": round(partial_tp, 2),
                "size": round(size_partial1, 4),  # Quantity of asset
                "risk_amount": risk_mgmt['risk_amount'] / 2,
                "reward_amount": risk_mgmt['reward_amount'] / 4,  # Half distance
                "risk_reward_ratio": 1.0,  # 50% TP = 1:1 R/R
                "atr": risk_mgmt['atr'],
                "entry_setup": strategy_analysis.get('entry_quality', 'unknown'),
                "entry_time": datetime.now(timezone.utc).isoformat(),
                "reasoning": f"{recommendation.get('reasoning', '')} [PARTIAL 1/2 - ${partial_position_usd:.0f}]",
                "analysis_data": {
                    "strategy": strategy_name,
                    "partial": "1/2",
                    "position_usd": partial_position_usd,
                    "confluence": strategy_analysis.get('confluence'),
                    "entry_quality": strategy_analysis.get('entry_quality')
                }
            }
            
            # TRADE 2: Full (100% TP) - Tighter SL (break-even style)
            trade_data_2 = {
                "symbol": recommendation.get('symbol', state['symbol']),  # Prefer symbol from recommendation
                "strategy": strategy_name,
                "action": action,
                "confidence": recommendation.get('confidence', 'unknown'),
                "entry_price": entry,
                "stop_loss": round(sl_partial2, 2),
                "take_profit": full_tp,
                "size": round(size_partial2, 4),  # Quantity of asset
                "risk_amount": risk_mgmt['risk_amount'] / 2,
                "reward_amount": risk_mgmt['reward_amount'] / 2,
                "risk_reward_ratio": risk_mgmt['risk_reward_ratio'],
                "atr": risk_mgmt['atr'],
                "entry_setup": strategy_analysis.get('entry_quality', 'unknown'),
                "entry_time": datetime.now(timezone.utc).isoformat(),
                "reasoning": f"{recommendation.get('reasoning', '')} [FULL 2/2 - ${partial_position_usd:.0f}]",
                "analysis_data": {
                    "strategy": strategy_name,
                    "partial": "2/2",
                    "position_usd": partial_position_usd,
                    "confluence": strategy_analysis.get('confluence'),
                    "entry_quality": strategy_analysis.get('entry_quality')
                }
            }
            
            # Store both trades
            trade_id_1 = f"{symbol}_{timestamp}_{strategy_name}_partial1"
            trade_id_2 = f"{symbol}_{timestamp}_{strategy_name}_partial2"
            
            # Override trade_id in data
            import copy
            data_1 = copy.deepcopy(trade_data_1)
            data_2 = copy.deepcopy(trade_data_2)
            
            # Manual insert to control trade_id (with fees calculation)
            conn = db.conn = __import__('sqlite3').connect(db.db_path)
            cursor = conn.cursor()
            
            # Get fee rate from config
            fee_rate = config.TRADING_FEE_RATE
            
            for tid, tdata in [(trade_id_1, data_1), (trade_id_2, data_2)]:
                # Calculate entry fee (0.05% of position value at entry)
                position_value_at_entry = tdata['entry_price'] * tdata.get('size', 0)
                entry_fee = position_value_at_entry * fee_rate
                
                cursor.execute('''
                    INSERT INTO trades (
                        trade_id, symbol, strategy, action, confidence,
                        entry_price, stop_loss, take_profit, size,
                        risk_amount, reward_amount, risk_reward_ratio,
                        atr, entry_setup, status, entry_time,
                        entry_fee, exit_fee, total_fees,
                        analysis_data, reasoning
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tid,
                    tdata['symbol'],
                    tdata['strategy'],
                    tdata['action'],
                    tdata.get('confidence'),
                    tdata['entry_price'],
                    tdata['stop_loss'],
                    tdata['take_profit'],
                    tdata.get('size', 0),  # Position size (quantity of asset)
                    tdata.get('risk_amount'),
                    tdata.get('reward_amount'),
                    tdata.get('risk_reward_ratio'),
                    tdata.get('atr'),
                    tdata.get('entry_setup'),
                    'OPEN',
                    tdata.get('entry_time'),
                    entry_fee,  # Calculate entry fee
                    0,  # exit_fee (will be calculated on close)
                    entry_fee,  # total_fees starts with entry_fee
                    __import__('json').dumps(tdata.get('analysis_data', {})),
                    tdata.get('reasoning')
                ))
            
            conn.commit()
            conn.close()
            
            # LOG SUCCESSFUL EXECUTION
            log_data['executed'] = True
            log_data['execution_reason'] = f"Executed 2 partial trades: {trade_id_1[:30]}, {trade_id_2[:30]}"
            db_log.log_strategy_run(log_data)
            
            logger.info(f"✅ [{strategy_name.upper()}] 2 Partial trades executed:")
            logger.info(f"   Position Size: ${TOTAL_POSITION_USD:.0f} (${partial_position_usd:.0f} each)")
            logger.info(f"   Quantity: {size_partial1:.4f} {state['symbol'][:3]} per partial")
            logger.info(f"   1/2 (50% TP): {trade_id_1[:50]}... @ TP ${round(partial_tp, 2)}")
            logger.info(f"   2/2 (Full TP): {trade_id_2[:50]}... @ TP ${full_tp}")
            logger.info(f"   Entry: ${entry} | SL: ${original_sl}")
            
            executed_trades.append({
                "strategy": strategy_name,
                "trade_id": f"{trade_id_1}, {trade_id_2}",
                "action": action,
                "partial": True
            })
        
        # Get statistics
        if executed_trades:
            db = TradingDatabase()
            stats_all = db.get_trade_stats(state['symbol'])
            stats_structured = db.get_trade_stats(state['symbol'], 'structured')
            stats_minimal = db.get_trade_stats(state['symbol'], 'minimal')
            stats_macro = db.get_trade_stats(state['symbol'], 'macro')
            stats_intraday = db.get_trade_stats(state['symbol'], 'intraday')
            
            logger.info(f"\n📊 Multi-Strategy Performance:")
            logger.info(f"   OVERALL: {stats_all['total_trades']} trades total")
            if stats_all.get('closed_trades', 0) > 0:
                logger.info(f"      Win rate: {stats_all['win_rate']:.1f}% | P&L: ${stats_all['total_pnl']:.2f}")
            
            if stats_structured['total_trades'] > 0:
                logger.info(f"   STRUCTURED: {stats_structured['total_trades']} trades", end='')
                if stats_structured.get('closed_trades', 0) > 0:
                    logger.info(f" | Win: {stats_structured['win_rate']:.1f}% | P&L: ${stats_structured['total_pnl']:.2f}")
                else:
                    logger.info("")
            
            if stats_minimal['total_trades'] > 0:
                logger.info(f"   🤖 MINIMAL: {stats_minimal['total_trades']} trades", end='')
                if stats_minimal.get('closed_trades', 0) > 0:
                    logger.info(f" | Win: {stats_minimal['win_rate']:.1f}% | P&L: ${stats_minimal['total_pnl']:.2f}")
                else:
                    logger.info("")
            
            if stats_macro['total_trades'] > 0:
                logger.info(f"   🌍 MACRO: {stats_macro['total_trades']} trades", end='')
                if stats_macro.get('closed_trades', 0) > 0:
                    logger.info(f" | Win: {stats_macro['win_rate']:.1f}% | P&L: ${stats_macro['total_pnl']:.2f}")
                else:
                    logger.info("")
            
            if stats_intraday['total_trades'] > 0:
                logger.info(f"   ⚡ INTRADAY: {stats_intraday['total_trades']} trades", end='')
                if stats_intraday.get('closed_trades', 0) > 0:
                    logger.info(f" | Win: {stats_intraday['win_rate']:.1f}% | P&L: ${stats_intraday['total_pnl']:.2f}")
                else:
                    logger.info("")
            
            state['trade_execution'] = {
                "executed": True,
                "trades": executed_trades,
                "stats": {
                    "overall": stats_all,
                    "structured": stats_structured,
                    "minimal": stats_minimal,
                    "macro": stats_macro,
                    "intraday": stats_intraday
                }
            }
        else:
            state['trade_execution'] = {
                "executed": False,
                "reason": "All strategies returned NEUTRAL"
            }
        
    except Exception as e:
        error_msg = f"Error executing paper trades: {str(e)}"
        logger.info(f"📝 ❌ PAPER TRADING ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        state['trade_execution'] = {
            "executed": False,
            "error": error_msg
        }
    
    # Final summary
    executed_count = len([t for t in executed_trades]) if 'executed_trades' in locals() else 0
    if executed_count > 0:
        logger.info(f"\n📝 === PAPER TRADING EXECUTION END ===")
        logger.info(f"📝 ✅ Successfully executed {executed_count} paper trade(s)")
    else:
        logger.info(f"\n📝 === PAPER TRADING EXECUTION END ===")
        logger.info(f"📝 ℹ️  No trades executed this cycle")
    logger.info("")
    
    return state
