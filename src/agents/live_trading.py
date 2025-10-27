"""Live Trading Agent - Executes real trades via Binance API (Multi-Strategy)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.database import TradingDatabase
from utils.binance_client import BinanceClient
from datetime import datetime, timezone, timedelta
import config
import json


def execute_live_trade(state: TradingState) -> TradingState:
    """
    Execute LIVE trades for ALL strategies (real money via Binance API)
    
    SAFETY FEATURES:
    - Checks available balance before trading
    - Verifies no conflicting open positions
    - Applies cooldown periods between trades
    - Sets stop-loss and take-profit orders automatically
    - Logs all trades to database for tracking
    
    Args:
        state: Current trading state with recommendations from all strategies
        
    Returns:
        Updated state with trade execution info
    """
    print(f"\n💰 Executing LIVE trades (Multi-Strategy)...")
    
    try:
        # Initialize Binance client
        try:
            binance = BinanceClient()
            if not binance.has_credentials:
                print("❌ No API credentials - LIVE TRADING DISABLED")
                print("   Set BINANCE_API_KEY and BINANCE_API_SECRET in .env file")
                state['trade_execution'] = {
                    "executed": False,
                    "error": "No API credentials"
                }
                return state
        except Exception as e:
            print(f"❌ Failed to initialize Binance client: {e}")
            state['trade_execution'] = {
                "executed": False,
                "error": f"Binance client error: {str(e)}"
            }
            return state
        
        # Get account balance
        try:
            balance = binance.get_account_balance()
            available_balance = balance['available_balance']
            print(f"💵 Account Balance: ${balance['total_balance']:.2f} USDT")
            print(f"   Available: ${available_balance:.2f} | Unrealized P&L: ${balance['unrealized_pnl']:.2f}")
        except Exception as e:
            print(f"❌ Failed to fetch balance: {e}")
            state['trade_execution'] = {
                "executed": False,
                "error": f"Balance check failed: {str(e)}"
            }
            return state
        
        recommendations = []
        
        # Dynamically collect ALL recommendations from state
        for key, value in state.items():
            if key.startswith('recommendation_') and value is not None:
                strategy_name = key.replace('recommendation_', '')
                recommendations.append((strategy_name, value))
        
        if not recommendations:
            print("❌ No recommendations from any strategy")
            return state
        
        print(f"   Found {len(recommendations)} recommendation(s): {', '.join(r[0] for r in recommendations)}")
        
        executed_trades = []
        
        # Try to get analysis and market_data
        analysis = state.get('analysis')
        market_data = state.get('market_data')
        
        # Execute trade for each strategy
        for strategy_name, recommendation in recommendations:
            action = recommendation['action']
            
            # Get strategy-specific data if available, otherwise use generic
            strategy_market_data = state.get(f'market_data_{strategy_name}') or market_data
            strategy_analysis = state.get(f'analysis_{strategy_name}') or analysis
            
            # Ensure we have valid data
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
                'execution_reason': None,
                'live_trade': True  # Mark as live trade attempt
            }
            
            # Only execute for LONG or SHORT
            if action not in ['LONG', 'SHORT']:
                log_data['execution_reason'] = f"No trade - {action}"
                db_log.log_strategy_run(log_data)
                print(f"ℹ️  [{strategy_name.upper()}] No trade - {action}")
                continue
            
            # Check if strategy already has open trade (from paper trading DB)
            db_check = TradingDatabase()
            symbol = recommendation.get('symbol', state['symbol'])
            existing_open = db_check.get_open_trades(symbol)
            
            # Filter for this strategy
            strategy_open = [t for t in existing_open if t.get('strategy') == strategy_name]
            
            # Also check LIVE positions on Binance
            try:
                live_positions = binance.get_open_positions(symbol)
            except Exception as e:
                print(f"⚠️  Failed to check live positions: {e}")
                live_positions = []
            
            if strategy_open or live_positions:
                # Check if opposite direction - if so, close existing trades/positions
                if strategy_open:
                    existing_direction = strategy_open[0].get('action', 'UNKNOWN')  # Fixed: use 'action', not 'side'
                elif live_positions:
                    existing_direction = live_positions[0]['side']  # Live positions use 'side'
                else:
                    existing_direction = 'UNKNOWN'
                
                opposite_direction = (existing_direction == 'LONG' and action == 'SHORT') or \
                                   (existing_direction == 'SHORT' and action == 'LONG')
                
                if opposite_direction:
                    # CLOSE EXISTING POSITION on Binance
                    if live_positions:
                        print(f"🔄 [{strategy_name.upper()}] OPPOSITE SIGNAL detected!")
                        print(f"   Closing existing {existing_direction} position on Binance")
                        
                        for pos in live_positions:
                            try:
                                # Determine side for closing (opposite of position)
                                close_side = 'SELL' if pos['side'] == 'LONG' else 'BUY'
                                quantity = abs(pos['position_amt'])
                                
                                # Market close position
                                close_order = binance.place_market_order(
                                    symbol=symbol,
                                    side=close_side,
                                    quantity=quantity,
                                    reduce_only=True
                                )
                                
                                print(f"   ✅ Closed position: {quantity} {symbol} @ ${close_order['avg_price']:.2f}")
                                print(f"      Unrealized P&L: ${pos['unrealized_pnl']:+.2f}")
                                
                            except Exception as e:
                                print(f"   ❌ Error closing position: {e}")
                    
                    # Cancel any open orders (SL/TP from previous trade)
                    try:
                        binance.cancel_all_orders(symbol)
                        print(f"   🗑️  Cancelled all open orders for {symbol}")
                    except Exception as e:
                        print(f"   ⚠️  Error cancelling orders: {e}")
                    
                    # DO NOT open new trade in opposite direction - just close and wait for cooldown
                    print(f"   ✅ Position closed. Cooldown activated - no new {action} trade opened.")
                    
                    # Log this event
                    log_data['executed'] = False
                    log_data['execution_reason'] = f"Closed {existing_direction} on opposite {action} signal - cooldown active"
                    db_log.log_strategy_run(log_data)
                    
                    # Skip opening new trade (cooldown will apply next time)
                    continue
                    
                else:
                    # Same direction - skip (don't double up)
                    log_data['execution_reason'] = f"Already has open {existing_direction} position"
                    db_log.log_strategy_run(log_data)
                    print(f"⚠️  [{strategy_name.upper()}] Skipping - Already has open {existing_direction} position")
                    continue
            
            # COOLDOWN CHECK: Prevent re-entry too soon after closing previous trade
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
                
                # COOLDOWN: Universal 30 minutes for all strategies
                cooldown_minutes = 30
                
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
            
            # POSITION SIZING: Use smaller size for live trading
            # Default: $100 per trade (instead of $10,000 for paper)
            LIVE_POSITION_USD = float(os.getenv('LIVE_POSITION_SIZE', '100'))
            
            # Check if we have enough balance
            if available_balance < LIVE_POSITION_USD:
                log_data['execution_reason'] = f"Insufficient balance (need ${LIVE_POSITION_USD}, have ${available_balance:.2f})"
                db_log.log_strategy_run(log_data)
                print(f"❌ [{strategy_name.upper()}] Insufficient balance: ${available_balance:.2f} < ${LIVE_POSITION_USD}")
                continue
            
            # Calculate partial positions
            partial_position_usd = LIVE_POSITION_USD / 2  # $50 each
            
            entry = risk_mgmt['entry']
            original_sl = risk_mgmt['stop_loss']
            
            # Calculate TPs
            if strategy_name == 'intraday2' and 'take_profit_1' in risk_mgmt:
                partial_tp = risk_mgmt['take_profit_1']
                full_tp = risk_mgmt['take_profit_2']
            else:
                full_tp = risk_mgmt['take_profit']
                if action == 'LONG':
                    tp_distance = full_tp - entry
                    partial_tp = entry + (tp_distance * 0.5)
                else:  # SHORT
                    tp_distance = entry - full_tp
                    partial_tp = entry - (tp_distance * 0.5)
            
            # DIFFERENT SL for each partial trade (same as paper trading)
            # Partial 1: Original SL (needs to close first)
            # Partial 2: Tighter SL (50% tighter - break-even style)
            if action == 'LONG':
                sl_partial1 = original_sl  # Original SL for quick exit
                sl_partial2 = entry - (entry - original_sl) * 0.5  # 50% tighter
            else:  # SHORT
                sl_partial1 = original_sl  # Original SL for quick exit
                sl_partial2 = entry + (original_sl - entry) * 0.5  # 50% tighter
            
            # Calculate quantity (quantity precision matters!)
            # Round to appropriate precision for the symbol
            size_partial = partial_position_usd / entry
            
            # Round quantity based on symbol (SOL = 3 decimals, BTC = 3 decimals, ETH = 3 decimals)
            # TODO: Get precision from exchange info
            quantity_precision = 3
            size_partial = round(size_partial, quantity_precision)
            
            if size_partial <= 0:
                log_data['execution_reason'] = f"Position size too small: {size_partial}"
                db_log.log_strategy_run(log_data)
                print(f"❌ [{strategy_name.upper()}] Position size too small: {size_partial}")
                continue
            
            # EXECUTE LIVE TRADE
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            
            try:
                # 1. Open position with SINGLE MARKET order (for entire position)
                order_side = 'BUY' if action == 'LONG' else 'SELL'
                total_quantity = size_partial * 2  # Total quantity for entire position
                
                print(f"\n🚀 [{strategy_name.upper()}] Opening LIVE {action} position...")
                print(f"   Position: ${LIVE_POSITION_USD:.2f} total")
                print(f"   Quantity: {total_quantity} {symbol[:3]} (split to 2 partials)")
                print(f"   Entry: ~${entry} | SL1: ${round(sl_partial1, 2)} | SL2: ${round(sl_partial2, 2)}")
                print(f"   TP1: ${partial_tp} | TP2: ${full_tp}")
                
                # SINGLE MARKET ORDER for entire position
                print(f"\n   📤 Placing market order for entire position...")
                order = binance.place_market_order(
                    symbol=symbol,
                    side=order_side,
                    quantity=total_quantity
                )
                
                avg_entry = order['avg_price']
                print(f"   ✅ Order filled @ ${avg_entry:.2f} (Qty: {total_quantity})")
                
                # 2. Place STOP LOSS orders (2 separate SL for each partial)
                sl_side = 'SELL' if action == 'LONG' else 'BUY'
                
                print(f"\n   🛡️  Placing STOP LOSS orders...")
                
                # SL1: Original SL for first partial
                sl1_order = binance.place_stop_market_order(
                    symbol=symbol,
                    side=sl_side,
                    quantity=size_partial,
                    stop_price=round(sl_partial1, 2),
                    reduce_only=True
                )
                print(f"   ✅ SL1 @ ${round(sl_partial1, 2)} (Order ID: {sl1_order['order_id']})")
                
                # SL2: Tighter SL for second partial (break-even style)
                sl2_order = binance.place_stop_market_order(
                    symbol=symbol,
                    side=sl_side,
                    quantity=size_partial,
                    stop_price=round(sl_partial2, 2),
                    reduce_only=True
                )
                print(f"   ✅ SL2 @ ${round(sl_partial2, 2)} (Order ID: {sl2_order['order_id']})")
                
                # 3. Place TAKE PROFIT orders (2 partials)
                print(f"\n   🎯 Placing TAKE PROFIT orders...")
                
                # TP1: Partial (50% of position)
                tp1_order = binance.place_take_profit_market_order(
                    symbol=symbol,
                    side=sl_side,
                    quantity=size_partial,
                    stop_price=partial_tp,
                    reduce_only=True
                )
                print(f"   ✅ TP1 @ ${partial_tp} (Order ID: {tp1_order['order_id']})")
                
                # TP2: Full (remaining 50%)
                tp2_order = binance.place_take_profit_market_order(
                    symbol=symbol,
                    side=sl_side,
                    quantity=size_partial,
                    stop_price=full_tp,
                    reduce_only=True
                )
                print(f"   ✅ TP2 @ ${full_tp} (Order ID: {tp2_order['order_id']})")
                
                # LOG TO DATABASE (for tracking and statistics)
                db = TradingDatabase()
                
                # TRADE 1 DATABASE ENTRY (uses sl_partial1 calculated earlier)
                trade_data_1 = {
                    "symbol": symbol,
                    "strategy": strategy_name,
                    "action": action,
                    "confidence": recommendation.get('confidence', 'unknown'),
                    "entry_price": avg_entry,
                    "stop_loss": round(sl_partial1, 2),
                    "take_profit": round(partial_tp, 2),
                    "size": size_partial,
                    "risk_amount": risk_mgmt['risk_amount'] / 2,
                    "reward_amount": risk_mgmt['reward_amount'] / 4,
                    "risk_reward_ratio": 1.0,
                    "atr": risk_mgmt['atr'],
                    "entry_setup": strategy_analysis.get('entry_quality', 'unknown'),
                    "entry_time": datetime.now(timezone.utc).isoformat(),
                    "reasoning": f"{recommendation.get('reasoning', '')} [LIVE PARTIAL 1/2 - ${partial_position_usd:.0f}]",
                    "analysis_data": {
                        "strategy": strategy_name,
                        "partial": "1/2",
                        "position_usd": partial_position_usd,
                        "confluence": strategy_analysis.get('confluence'),
                        "entry_quality": strategy_analysis.get('entry_quality'),
                        "live_trade": True,
                        "binance_order_id": order['order_id'],
                        "sl_order_id": sl1_order['order_id'],
                        "tp_order_id": tp1_order['order_id']
                    }
                }
                
                # TRADE 2 DATABASE ENTRY (uses sl_partial2 calculated earlier)
                trade_data_2 = {
                    "symbol": symbol,
                    "strategy": strategy_name,
                    "action": action,
                    "confidence": recommendation.get('confidence', 'unknown'),
                    "entry_price": avg_entry,
                    "stop_loss": round(sl_partial2, 2),
                    "take_profit": full_tp,
                    "size": size_partial,
                    "risk_amount": risk_mgmt['risk_amount'] / 2,
                    "reward_amount": risk_mgmt['reward_amount'] / 2,
                    "risk_reward_ratio": risk_mgmt['risk_reward_ratio'],
                    "atr": risk_mgmt['atr'],
                    "entry_setup": strategy_analysis.get('entry_quality', 'unknown'),
                    "entry_time": datetime.now(timezone.utc).isoformat(),
                    "reasoning": f"{recommendation.get('reasoning', '')} [LIVE FULL 2/2 - ${partial_position_usd:.0f}]",
                    "analysis_data": {
                        "strategy": strategy_name,
                        "partial": "2/2",
                        "position_usd": partial_position_usd,
                        "confluence": strategy_analysis.get('confluence'),
                        "entry_quality": strategy_analysis.get('entry_quality'),
                        "live_trade": True,
                        "binance_order_id": order['order_id'],
                        "sl_order_id": sl2_order['order_id'],
                        "tp_order_id": tp2_order['order_id']
                    }
                }
                
                # Store trades in database
                trade_id_1 = f"{symbol}_LIVE_{timestamp}_{strategy_name}_partial1"
                trade_id_2 = f"{symbol}_LIVE_{timestamp}_{strategy_name}_partial2"
                
                # Manual insert with fees
                conn = db.conn = __import__('sqlite3').connect(db.db_path)
                cursor = conn.cursor()
                
                fee_rate = config.TRADING_FEE_RATE
                
                for tid, tdata in [(trade_id_1, trade_data_1), (trade_id_2, trade_data_2)]:
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
                        tdata.get('size', 0),
                        tdata.get('risk_amount'),
                        tdata.get('reward_amount'),
                        tdata.get('risk_reward_ratio'),
                        tdata.get('atr'),
                        tdata.get('entry_setup'),
                        'OPEN',
                        tdata.get('entry_time'),
                        entry_fee,
                        0,
                        entry_fee,
                        __import__('json').dumps(tdata.get('analysis_data', {})),
                        tdata.get('reasoning')
                    ))
                
                conn.commit()
                conn.close()
                
                # LOG SUCCESSFUL EXECUTION
                log_data['executed'] = True
                log_data['execution_reason'] = f"LIVE trades executed: {trade_id_1[:30]}, {trade_id_2[:30]}"
                log_data['binance_order_ids'] = [order['order_id']]
                db_log.log_strategy_run(log_data)
                
                print(f"\n✅ [{strategy_name.upper()}] LIVE TRADES EXECUTED SUCCESSFULLY!")
                print(f"   💵 Position: ${LIVE_POSITION_USD:.2f} | Qty: {total_quantity} {symbol[:3]}")
                print(f"   📊 Entry: ${avg_entry:.2f}")
                print(f"   🛡️  SL1: ${round(sl_partial1, 2)} (Order: {sl1_order['order_id']})")
                print(f"   🛡️  SL2: ${round(sl_partial2, 2)} (Order: {sl2_order['order_id']})")
                print(f"   🎯 TP1: ${partial_tp} (Order: {tp1_order['order_id']})")
                print(f"   🎯 TP2: ${full_tp} (Order: {tp2_order['order_id']})")
                print(f"   🔑 Trade IDs: {trade_id_1[:40]}, {trade_id_2[:40]}")
                print(f"   🌐 Entry Order: {order['order_id']}")
                
                executed_trades.append({
                    "strategy": strategy_name,
                    "trade_id": f"{trade_id_1}, {trade_id_2}",
                    "action": action,
                    "partial": True,
                    "live": True,
                    "binance_order_ids": [order['order_id']]
                })
                
            except Exception as e:
                error_msg = f"Failed to execute live trade: {str(e)}"
                print(f"❌ [{strategy_name.upper()}] {error_msg}")
                import traceback
                traceback.print_exc()
                
                # Log failed execution
                log_data['executed'] = False
                log_data['execution_reason'] = error_msg
                db_log.log_strategy_run(log_data)
                
                # Try to cancel any partially filled orders
                try:
                    print(f"   🗑️  Attempting to cancel any open orders...")
                    binance.cancel_all_orders(symbol)
                except:
                    pass
        
        # Get statistics
        if executed_trades:
            db = TradingDatabase()
            stats_all = db.get_trade_stats(state['symbol'])
            
            print(f"\n📊 LIVE Trading Performance:")
            print(f"   OVERALL: {stats_all['total_trades']} trades total")
            if stats_all.get('closed_trades', 0) > 0:
                print(f"      Win rate: {stats_all['win_rate']:.1f}% | P&L: ${stats_all['total_pnl']:.2f}")
            
            state['trade_execution'] = {
                "executed": True,
                "trades": executed_trades,
                "live": True,
                "stats": stats_all
            }
        else:
            state['trade_execution'] = {
                "executed": False,
                "reason": "No trades executed",
                "live": True
            }
        
    except Exception as e:
        error_msg = f"Error executing live trades: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        state['trade_execution'] = {
            "executed": False,
            "error": error_msg,
            "live": True
        }
    
    return state

