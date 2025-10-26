"""Paper Trading Agent - Executes simulated trades and stores in database (Multi-Strategy)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.database import TradingDatabase
from datetime import datetime
import config


def execute_paper_trade(state: TradingState) -> TradingState:
    """
    Execute paper trades for ALL strategies (dynamically finds all recommendation_* keys)
    
    Args:
        state: Current trading state with recommendations from all strategies
        
    Returns:
        Updated state with trade execution info
    """
    print(f"\n📝 Executing paper trades (Multi-Strategy)...")
    
    try:
        recommendations = []
        
        # Dynamically collect ALL recommendations from state
        # Find all keys starting with 'recommendation_'
        for key, value in state.items():
            if key.startswith('recommendation_') and value is not None:
                strategy_name = key.replace('recommendation_', '')
                recommendations.append((strategy_name, value))
        
        if not recommendations:
            print("❌ No recommendations from any strategy")
            return state
        
        print(f"   Found {len(recommendations)} recommendation(s): {', '.join(r[0] for r in recommendations)}")
        
        executed_trades = []
        
        # Try to get analysis and market_data (may be strategy-specific)
        # For backward compatibility, try generic keys first, then fall back to strategy-specific
        analysis = state.get('analysis')
        market_data = state.get('market_data')
        
        # Execute trade for each strategy
        for strategy_name, recommendation in recommendations:
            action = recommendation['action']
            
            # Get strategy-specific data if available, otherwise use generic
            strategy_market_data = state.get(f'market_data_{strategy_name}') or market_data
            strategy_analysis = state.get(f'analysis_{strategy_name}') or analysis
            
            # Ensure we have valid data (not None)
            if not strategy_analysis:
                print(f"⚠️  [{strategy_name.upper()}] Skipping - No analysis data available")
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
                print(f"ℹ️  [{strategy_name.upper()}] No trade - {action}")
                continue
            
            # Check if strategy already has open trade (RISK MANAGEMENT!)
            db_check = TradingDatabase()
            existing_open = db_check.get_open_trades(state['symbol'])
            
            # Filter for this strategy
            strategy_open = [t for t in existing_open if t.get('strategy') == strategy_name]
            
            if strategy_open:
                # Check if opposite direction - if so, close existing trades
                existing_direction = strategy_open[0].get('side', 'UNKNOWN')
                opposite_direction = (existing_direction == 'LONG' and action == 'SHORT') or \
                                   (existing_direction == 'SHORT' and action == 'LONG')
                
                if opposite_direction:
                    # Close all open trades for this strategy (on opposite signal)
                    current_price = strategy_market_data.get('current_price') if strategy_market_data else market_data.get('current_price')
                    from datetime import datetime as dt, timezone
                    
                    print(f"🔄 [{strategy_name.upper()}] OPPOSITE SIGNAL detected!")
                    print(f"   Closing {len(strategy_open)} {existing_direction} trade(s) on {action} signal")
                    print(f"   Exit price: ${current_price:.2f} (close of last candle)")
                    
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
                            
                            # Close trade
                            db_close = TradingDatabase()
                            db_close.close_trade(
                                trade_id=trade['trade_id'],
                                exit_price=current_price,
                                exit_reason=f"OPPOSITE_SIGNAL ({action})",
                                pnl=pnl
                            )
                            
                            print(f"   ✅ Closed {trade['trade_id']}: ${entry_price:.2f} → ${current_price:.2f}")
                            print(f"      P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
                            
                        except Exception as e:
                            print(f"   ❌ Error closing trade {trade['trade_id']}: {str(e)}")
                    
                    # Now continue to open new trade in opposite direction
                    print(f"   Opening new {action} trade...")
                    
                else:
                    # Same direction - skip (don't double up)
                    log_data['execution_reason'] = f"Already has {len(strategy_open)} open {existing_direction} trade(s)"
                    db_log.log_strategy_run(log_data)
                    print(f"⚠️  [{strategy_name.upper()}] Skipping - Already has {len(strategy_open)} open {existing_direction} trade(s)")
                    print(f"    Open trade: {strategy_open[0]['trade_id']}")
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
                from datetime import datetime as dt, timedelta, timezone
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
                    'structured': 45,   # Swing: longer cooldown
                    'minimal': 30,      # Medium
                    'macro': 30,        # Swing: medium cooldown
                    'intraday': 20,     # Intraday: shorter cooldown
                    'intraday2': 15     # Mean reversion: shortest (more trades)
                }
                
                cooldown_minutes = COOLDOWN_MAP.get(strategy_name, 30)  # Default 30min
                
                if time_since_exit < cooldown_minutes:
                    log_data['execution_reason'] = f"COOLDOWN - Wait {cooldown_minutes - time_since_exit:.1f}min"
                    db_log.log_strategy_run(log_data)
                    print(f"⏳ [{strategy_name.upper()}] COOLDOWN ({cooldown_minutes}min) - Last trade closed {time_since_exit:.1f}min ago")
                    print(f"    Waiting {cooldown_minutes - time_since_exit:.1f}min more before re-entry")
                    continue
            
            # Check if we have risk management
            if 'risk_management' not in recommendation:
                log_data['execution_reason'] = "No risk management data"
                db_log.log_strategy_run(log_data)
                print(f"❌ [{strategy_name.upper()}] No risk management data")
                continue
            
            risk_mgmt = recommendation['risk_management']
            
            # Initialize database
            db = TradingDatabase()
            
            # Create 2 PARTIAL TRADES (scale out strategy)
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            
            # Calculate partial TP (50% of distance to full TP)
            entry = risk_mgmt['entry']
            original_sl = risk_mgmt['stop_loss']
            
            # INTRADAY2 has custom TP1/TP2, others use standard partial
            if strategy_name == 'intraday2' and 'take_profit_1' in risk_mgmt:
                partial_tp = risk_mgmt['take_profit_1']
                full_tp = risk_mgmt['take_profit_2']
            else:
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
            
            # TRADE 1: Partial (50% TP) - Original SL
            trade_data_1 = {
                "symbol": state['symbol'],
                "strategy": strategy_name,
                "action": action,
                "confidence": recommendation.get('confidence', 'unknown'),
                "entry_price": entry,
                "stop_loss": round(sl_partial1, 2),
                "take_profit": round(partial_tp, 2),
                "risk_amount": risk_mgmt['risk_amount'] / 2,
                "reward_amount": risk_mgmt['reward_amount'] / 4,  # Half distance
                "risk_reward_ratio": 1.0,  # 50% TP = 1:1 R/R
                "atr": risk_mgmt['atr'],
                "entry_setup": strategy_analysis.get('entry_quality', 'unknown'),
                "entry_time": datetime.now(timezone.utc).isoformat(),
                "reasoning": f"{recommendation.get('reasoning', '')} [PARTIAL 1/2]",
                "analysis_data": {
                    "strategy": strategy_name,
                    "partial": "1/2",
                    "confluence": strategy_analysis.get('confluence'),
                    "entry_quality": strategy_analysis.get('entry_quality')
                }
            }
            
            # TRADE 2: Full (100% TP) - Tighter SL (break-even style)
            trade_data_2 = {
                "symbol": state['symbol'],
                "strategy": strategy_name,
                "action": action,
                "confidence": recommendation.get('confidence', 'unknown'),
                "entry_price": entry,
                "stop_loss": round(sl_partial2, 2),
                "take_profit": full_tp,
                "risk_amount": risk_mgmt['risk_amount'] / 2,
                "reward_amount": risk_mgmt['reward_amount'] / 2,
                "risk_reward_ratio": risk_mgmt['risk_reward_ratio'],
                "atr": risk_mgmt['atr'],
                "entry_setup": strategy_analysis.get('entry_quality', 'unknown'),
                "entry_time": datetime.now(timezone.utc).isoformat(),
                "reasoning": f"{recommendation.get('reasoning', '')} [FULL 2/2]",
                "analysis_data": {
                    "strategy": strategy_name,
                    "partial": "2/2",
                    "confluence": strategy_analysis.get('confluence'),
                    "entry_quality": strategy_analysis.get('entry_quality')
                }
            }
            
            # Store both trades
            trade_id_1 = f"{state['symbol']}_{timestamp}_{strategy_name}_partial1"
            trade_id_2 = f"{state['symbol']}_{timestamp}_{strategy_name}_partial2"
            
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
                # Calculate entry fee
                entry_fee = tdata['entry_price'] * fee_rate
                
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
                    tid,
                    tdata['symbol'],
                    tdata['strategy'],
                    tdata['action'],
                    tdata.get('confidence'),
                    tdata['entry_price'],
                    tdata['stop_loss'],
                    tdata['take_profit'],
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
            
            print(f"✅ [{strategy_name.upper()}] 2 Partial trades executed:")
            print(f"   1/2 (50% TP): {trade_id_1[:50]}... @ TP ${round(partial_tp, 2)}")
            print(f"   2/2 (Full TP): {trade_id_2[:50]}... @ TP ${full_tp}")
            print(f"   Entry: ${entry} | SL: ${original_sl}")
            
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
            
            print(f"\n📊 Multi-Strategy Performance:")
            print(f"   OVERALL: {stats_all['total_trades']} trades total")
            if stats_all.get('closed_trades', 0) > 0:
                print(f"      Win rate: {stats_all['win_rate']:.1f}% | P&L: ${stats_all['total_pnl']:.2f}")
            
            if stats_structured['total_trades'] > 0:
                print(f"   STRUCTURED: {stats_structured['total_trades']} trades", end='')
                if stats_structured.get('closed_trades', 0) > 0:
                    print(f" | Win: {stats_structured['win_rate']:.1f}% | P&L: ${stats_structured['total_pnl']:.2f}")
                else:
                    print()
            
            if stats_minimal['total_trades'] > 0:
                print(f"   🤖 MINIMAL: {stats_minimal['total_trades']} trades", end='')
                if stats_minimal.get('closed_trades', 0) > 0:
                    print(f" | Win: {stats_minimal['win_rate']:.1f}% | P&L: ${stats_minimal['total_pnl']:.2f}")
                else:
                    print()
            
            if stats_macro['total_trades'] > 0:
                print(f"   🌍 MACRO: {stats_macro['total_trades']} trades", end='')
                if stats_macro.get('closed_trades', 0) > 0:
                    print(f" | Win: {stats_macro['win_rate']:.1f}% | P&L: ${stats_macro['total_pnl']:.2f}")
                else:
                    print()
            
            if stats_intraday['total_trades'] > 0:
                print(f"   ⚡ INTRADAY: {stats_intraday['total_trades']} trades", end='')
                if stats_intraday.get('closed_trades', 0) > 0:
                    print(f" | Win: {stats_intraday['win_rate']:.1f}% | P&L: ${stats_intraday['total_pnl']:.2f}")
                else:
                    print()
            
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
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        state['trade_execution'] = {
            "executed": False,
            "error": error_msg
        }
    
    return state
