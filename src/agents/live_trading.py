"""Live Trading Agent - Executes real trades on Binance (Multi-Strategy)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState
from utils.database import TradingDatabase
from utils.binance_client import BinanceClient
from datetime import datetime, timezone, timedelta
import config
import json
import logging

# Get parent logger (will use DynamicTradingBot's logger)
logger = logging.getLogger('DynamicTradingBot.LiveTrading')


def get_quantity_precision(step_size: float) -> int:
    """Helper: Calculate quantity precision from step size"""
    return len(str(step_size).rstrip('0').split('.')[-1])


def execute_live_trade(state: TradingState, strategy_configs: dict) -> TradingState:
    """
    Execute LIVE trades for strategies with live_trading=True
    Mirrors paper_trading.py functionality with real Binance orders
    
    Args:
        state: Current trading state with recommendations from all strategies
        strategy_configs: Dict of strategy_name -> StrategyConfig
        
    Returns:
        Updated state with trade execution info
    """
    demo_mode_str = "TESTNET/DEMO" if config.BINANCE_DEMO else "REAL ACCOUNT"
    logger.info(f"\n🔴 === LIVE TRADING EXECUTION START ({demo_mode_str}) ===")
    logger.info(f"🔴 Processing LIVE trades for all strategies...")
    
    try:
        # Initialize Binance client
        client = BinanceClient()
        
        if not client.has_credentials:
            logger.info("🔴 ❌ Binance API credentials not configured!")
            logger.info("🔴 === LIVE TRADING EXECUTION END (No credentials) ===\n")
            return state
        
        if config.BINANCE_DEMO:
            logger.info("🔴 🧪 Using Binance TESTNET (Demo Mode)")
        else:
            logger.info("🔴 ⚠️  Using REAL Binance account - REAL MONEY AT RISK!")
        
        recommendations = []
        
        # Collect recommendations for strategies with live_trading=True
        for key, value in state.items():
            if key.startswith('recommendation_') and value is not None:
                strategy_name = key.replace('recommendation_', '')
                
                # Check if strategy has live trading enabled
                strategy_config = strategy_configs.get(strategy_name)
                if strategy_config and strategy_config.live_trading:
                    recommendations.append((strategy_name, value, strategy_config))
        
        if not recommendations:
            logger.info("🔴 ℹ️  No live trading recommendations (all strategies have live_trading=False)")
            logger.info("🔴 === LIVE TRADING EXECUTION END (No recommendations) ===\n")
            return state
        
        logger.info(f"🔴 ✅ Found {len(recommendations)} LIVE recommendation(s): {', '.join(r[0] for r in recommendations)}")
        
        # FIX #3: Load account balance ONCE at the beginning
        try:
            account = client.client.futures_account()
            available_balance = float(account['availableBalance'])
            logger.info(f"🔴 💰 Available Balance: ${available_balance:.2f} USDT")
        except Exception as e:
            logger.info(f"🔴 ❌ Failed to fetch account balance: {str(e)}")
            logger.info(f"🔴 === LIVE TRADING EXECUTION END (API error) ===\n")
            return state
        
        executed_trades = []
        
        # Single DB instance for all operations (FIX #8)
        db = TradingDatabase()
        
        # Try to get analysis and market_data (may be strategy-specific)
        analysis = state.get('analysis')
        market_data = state.get('market_data')
        
        # Execute trade for each strategy with live_trading=True
        for strategy_name, recommendation, strategy_config in recommendations:
            logger.info(f"\n🔴 [{strategy_name.upper()}] Processing LIVE recommendation...")
            action = recommendation['action']
            confidence = recommendation.get('confidence', 'unknown')
            symbol = recommendation.get('symbol', strategy_config.symbol)
            logger.info(f"🔴 [{strategy_name.upper()}] Decision: {action} (confidence: {confidence})")
            logger.info(f"🔴 [{strategy_name.upper()}] Symbol: {symbol}")
            
            # Get strategy-specific data if available, otherwise use generic
            strategy_market_data = state.get(f'market_data_{strategy_name}') or market_data
            strategy_analysis = state.get(f'analysis_{strategy_name}') or analysis
            
            # Ensure we have valid data (not None)
            if not strategy_analysis:
                logger.info(f"🔴 ❌ [{strategy_name.upper()}] SKIPPED - No analysis data available")
                logger.info(f"🔴 [{strategy_name.upper()}] Reason: analysis is None or empty")
                continue
            
            # LOG STRATEGY RUN (always log, even if not executed)
            log_data = {
                'symbol': symbol,
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
                'live_trade': True
            }
            
            # Only execute for LONG or SHORT
            if action not in ['LONG', 'SHORT']:
                log_data['execution_reason'] = f"No trade - {action}"
                db.log_strategy_run(log_data)
                logger.info(f"🔴 ℹ️  [{strategy_name.upper()}] NO TRADE EXECUTED - Action is {action} (not LONG or SHORT)")
                logger.info(f"🔴 [{strategy_name.upper()}] Trade skipped - waiting for LONG or SHORT signal")
                continue
            
            # Check existing positions on BINANCE (single source of truth for live trading)
            try:
                binance_positions = client.get_open_positions(symbol)
            except Exception as e:
                logger.info(f"🔴 ❌ [{strategy_name.upper()}] Error checking Binance positions: {str(e)}")
                log_data['execution_reason'] = f"Error checking positions: {str(e)}"
                db.log_strategy_run(log_data)
                continue
            
            logger.info(f"🔴 [{strategy_name.upper()}] Binance positions check: {len(binance_positions)} open position(s)")
            
            if binance_positions:
                # IMPORTANT: We only allow ONE position per SYMBOL (not per strategy)
                # This is because Binance Futures doesn't support multiple positions on same symbol
                position = binance_positions[0]
                existing_direction = position['side']  # 'LONG' or 'SHORT'
                position_amt = position['position_amt']
                entry_price = position['entry_price']
                
                opposite_direction = (existing_direction == 'LONG' and action == 'SHORT') or \
                                   (existing_direction == 'SHORT' and action == 'LONG')
                
                if opposite_direction:
                    logger.info(f"🔴 [{strategy_name.upper()}] 🔄 OPPOSITE SIGNAL DETECTED!")
                    logger.info(f"🔴 [{strategy_name.upper()}] Existing Binance position: {existing_direction}, New signal: {action}")
                    logger.info(f"🔴 [{strategy_name.upper()}] Closing {existing_direction} position ({abs(position_amt)} {symbol})")
                    
                    # Close position on Binance
                    try:
                        # Cancel all open orders first (SL/TP)
                        try:
                            client.client.futures_cancel_all_open_orders(symbol=symbol)
                            logger.info(f"   ✅ Cancelled all open orders for {symbol}")
                        except:
                            pass
                        
                        # Close position with market order
                        close_side = 'SELL' if position_amt > 0 else 'BUY'
                        close_order = client.client.futures_create_order(
                            symbol=symbol,
                            side=close_side,
                            type='MARKET',
                            quantity=abs(position_amt),
                            reduceOnly=True
                        )
                        
                        ticker = client.client.futures_symbol_ticker(symbol=symbol)
                        exit_price = float(ticker['price'])
                        
                        # Calculate P&L for logging
                        if existing_direction == 'LONG':
                            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                        else:  # SHORT
                            pnl_pct = ((entry_price - exit_price) / entry_price) * 100
                        
                        logger.info(f"   ✅ Closed Binance position: order {close_order['orderId']}")
                        logger.info(f"   Entry: ${entry_price:.2f} → Exit: ${exit_price:.2f} | P&L: {pnl_pct:+.2f}%")
                        
                        # DO NOT open new trade - cooldown applies
                        logger.info(f"🔴 [{strategy_name.upper()}] ⏸️  COOLDOWN ACTIVATED - No new {action} trade will be opened")
                        logger.info(f"🔴 [{strategy_name.upper()}] Reason: Risk management - waiting for next clear signal")
                        
                        log_data['executed'] = False
                        log_data['execution_reason'] = f"Closed {existing_direction} on opposite {action} signal - cooldown active"
                        db.log_strategy_run(log_data)
                        
                        continue
                        
                    except Exception as e:
                        logger.info(f"🔴 ❌ [{strategy_name.upper()}] Error closing opposite position: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        log_data['execution_reason'] = f"Error closing opposite position: {str(e)}"
                        db.log_strategy_run(log_data)
                        continue
                    
                else:
                    # Same direction - skip (don't double up)
                    log_data['execution_reason'] = f"Already has open {existing_direction} position on Binance"
                    db.log_strategy_run(log_data)
                    logger.info(f"🔴 ⚠️  [{strategy_name.upper()}] NO TRADE EXECUTED - Already have open {existing_direction} position")
                    logger.info(f"🔴 [{strategy_name.upper()}] Position: {abs(position_amt)} {symbol} @ ${entry_price:.2f}")
                    logger.info(f"🔴 [{strategy_name.upper()}] Reason: Risk management - one position per symbol at a time")
                    continue
            
            # COOLDOWN CHECK - kontroluj Binance trade history
            try:
                recent_trades = client.get_account_trades(symbol, limit=50)
                
                # Najdi poslední "closing" trade (realized PnL != 0 znamená zavření pozice)
                last_position_close_time = None
                for trade in recent_trades:
                    if trade['realized_pnl'] != 0:
                        # Toto byl closing trade
                        last_position_close_time = trade['timestamp']
                        break
                
                if last_position_close_time:
                    from datetime import datetime as dt
                    close_time = dt.fromtimestamp(last_position_close_time / 1000, tz=timezone.utc)
                    current_time = dt.now(timezone.utc)
                    time_since_close = (current_time - close_time).total_seconds() / 60
                    
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
                    
                    cooldown_minutes = COOLDOWN_MAP.get(strategy_name, 30)
                    
                    if time_since_close < cooldown_minutes:
                        remaining = cooldown_minutes - time_since_close
                        log_data['execution_reason'] = f"COOLDOWN - Wait {remaining:.1f}min"
                        db.log_strategy_run(log_data)
                        logger.info(f"🔴 ⏳ [{strategy_name.upper()}] NO TRADE EXECUTED - COOLDOWN ACTIVE")
                        logger.info(f"🔴 [{strategy_name.upper()}] Cooldown period: {cooldown_minutes} minutes")
                        logger.info(f"🔴 [{strategy_name.upper()}] Time since last position close: {time_since_close:.1f} minutes")
                        logger.info(f"🔴 [{strategy_name.upper()}] Remaining cooldown: {remaining:.1f} minutes")
                        logger.info(f"🔴 [{strategy_name.upper()}] Reason: Risk management - preventing over-trading")
                        continue
                    else:
                        logger.info(f"🔴 [{strategy_name.upper()}] ✅ Cooldown check passed ({time_since_close:.1f}min since last position close)")
                else:
                    logger.info(f"🔴 [{strategy_name.upper()}] ✅ No recent position closes found in Binance history")
                    
            except Exception as e:
                # If we can't check cooldown, log warning but continue (don't block trading)
                logger.info(f"🔴 ⚠️  [{strategy_name.upper()}] Warning: Could not check cooldown via Binance: {str(e)}")
                logger.info(f"🔴 [{strategy_name.upper()}] Proceeding with trade execution")
            
            logger.info(f"🔴 [{strategy_name.upper()}] ✅ All pre-checks passed - Proceeding with LIVE trade execution")
            
            # Check if we have risk management
            if 'risk_management' not in recommendation:
                log_data['execution_reason'] = "No risk management data"
                db.log_strategy_run(log_data)
                logger.info(f"🔴 ❌ [{strategy_name.upper()}] NO TRADE EXECUTED - Missing risk management data")
                logger.info(f"🔴 [{strategy_name.upper()}] Reason: Cannot execute trade without SL/TP levels")
                continue
            
            logger.info(f"🔴 [{strategy_name.upper()}] ✅ All pre-checks passed - Proceeding with LIVE trade execution")
            risk_mgmt = recommendation['risk_management']
            
            # FIX #4: Validate stop_loss exists
            original_sl = risk_mgmt.get('stop_loss')
            if not original_sl:
                log_data['execution_reason'] = "Missing stop loss in risk management"
                db.log_strategy_run(log_data)
                logger.info(f"🔴 ❌ [{strategy_name.upper()}] Missing stop loss value - cannot execute trade")
                continue
            
            # Get current price and entry price
            try:
                ticker = client.client.futures_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                
                # FIX #5: Use entry price from risk management (AI calculated optimal entry)
                entry = risk_mgmt.get('entry', current_price)
                
                # Calculate TPs and SLs
                # NOTE: Live trading používá JEDEN order s DVĚMA TP levels a DVĚMA SL levels
                # SL1: Původní SL pro 50% pozice (quick exit)
                # SL2: Tighter SL pro druhou půlku (50% těsnější, breakeven style)
                tp2 = risk_mgmt.get('take_profit')
                if not tp2:
                    log_data['execution_reason'] = "Missing take profit in risk management"
                    db.log_strategy_run(log_data)
                    logger.info(f"❌ [{strategy_name.upper()}] No take profit in risk management!")
                    continue
                
                # Calculate TP1 as 50% of distance to TP2
                if action == 'LONG':
                    tp_distance = tp2 - entry
                    tp1 = entry + (tp_distance * 0.5)  # 50% TP
                else:  # SHORT
                    tp_distance = entry - tp2
                    tp1 = entry - (tp_distance * 0.5)
                
                # Calculate TWO stop loss levels (same as paper trading)
                logger.info(f"🔴 [{strategy_name.upper()}] SL Calculation:")
                logger.info(f"   Action: {action}")
                logger.info(f"   Entry (from risk_mgmt): ${entry:.6f}")
                logger.info(f"   Current Price: ${current_price:.6f}")
                logger.info(f"   Original SL: ${original_sl:.6f}")
                logger.info(f"   TP2: ${tp2:.6f}")
                
                if action == 'LONG':
                    sl1 = original_sl  # Original SL for first 50%
                    sl2 = entry - (entry - original_sl) * 0.5  # 50% tighter (breakeven style)
                    logger.info(f"   LONG: sl2 = {entry:.6f} - ({entry:.6f} - {original_sl:.6f}) * 0.5 = ${sl2:.6f}")
                else:  # SHORT
                    sl1 = original_sl  # Original SL for first 50%
                    sl2 = entry + (original_sl - entry) * 0.5  # 50% tighter
                    logger.info(f"   SHORT: sl2 = {entry:.6f} + ({original_sl:.6f} - {entry:.6f}) * 0.5 = ${sl2:.6f}")
                
                # Validation: Check if SL/TP are far enough from entry
                min_distance_pct = 0.001  # 0.1% minimum distance
                min_distance = current_price * min_distance_pct
                
                if action == 'LONG':
                    if sl1 >= entry or sl2 >= entry:
                        log_data['execution_reason'] = f"Invalid SL for LONG: sl1={sl1:.6f}, sl2={sl2:.6f} >= entry={entry:.6f}"
                        db.log_strategy_run(log_data)
                        logger.info(f"🔴 ❌ [{strategy_name.upper()}] {log_data['execution_reason']}")
                        continue
                    if tp2 <= entry or tp1 <= entry:
                        log_data['execution_reason'] = f"Invalid TP for LONG: tp1={tp1:.6f}, tp2={tp2:.6f} <= entry={entry:.6f}"
                        db.log_strategy_run(log_data)
                        logger.info(f"🔴 ❌ [{strategy_name.upper()}] {log_data['execution_reason']}")
                        continue
                    if (entry - sl1) < min_distance or (tp2 - entry) < min_distance:
                        log_data['execution_reason'] = f"SL/TP too close to entry (min {min_distance:.6f}): SL distance={(entry-sl1):.6f}, TP distance={(tp2-entry):.6f}"
                        db.log_strategy_run(log_data)
                        logger.info(f"🔴 ❌ [{strategy_name.upper()}] {log_data['execution_reason']}")
                        continue
                else:  # SHORT
                    if sl1 <= entry or sl2 <= entry:
                        log_data['execution_reason'] = f"Invalid SL for SHORT: sl1={sl1:.6f}, sl2={sl2:.6f} <= entry={entry:.6f}"
                        db.log_strategy_run(log_data)
                        logger.info(f"🔴 ❌ [{strategy_name.upper()}] {log_data['execution_reason']}")
                        continue
                    if tp2 >= entry or tp1 >= entry:
                        log_data['execution_reason'] = f"Invalid TP for SHORT: tp1={tp1:.6f}, tp2={tp2:.6f} >= entry={entry:.6f}"
                        db.log_strategy_run(log_data)
                        logger.info(f"🔴 ❌ [{strategy_name.upper()}] {log_data['execution_reason']}")
                        continue
                    if (sl1 - entry) < min_distance or (entry - tp2) < min_distance:
                        log_data['execution_reason'] = f"SL/TP too close to entry (min {min_distance:.6f}): SL distance={(sl1-entry):.6f}, TP distance={(entry-tp2):.6f}"
                        db.log_strategy_run(log_data)
                        logger.info(f"🔴 ❌ [{strategy_name.upper()}] {log_data['execution_reason']}")
                        continue
                
                # FIX #1: Use percentage of available balance instead of hardcoded $10,000
                position_size_pct = risk_mgmt.get('position_size', 0.1)  # Default 10%
                position_value_usd = available_balance * position_size_pct
                
                # Safety check: minimum $10, maximum 50% of balance
                position_value_usd = max(10.0, min(position_value_usd, available_balance * 0.5))
                
                # Calculate quantity using CURRENT price (market order will execute at market)
                total_quantity = position_value_usd / current_price
                
                # Get symbol info for precision
                exchange_info = client.client.futures_exchange_info()
                symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
                
                if not symbol_info:
                    logger.info(f"❌ [{strategy_name.upper()}] Symbol {symbol} not found on exchange")
                    continue
                
                # FIX #9: Use helper function for precision calculation
                quantity_precision = None
                for filter in symbol_info['filters']:
                    if filter['filterType'] == 'LOT_SIZE':
                        step_size = float(filter['stepSize'])
                        quantity_precision = get_quantity_precision(step_size)
                        break
                
                # Round quantity to precision
                if quantity_precision is not None:
                    total_quantity = round(total_quantity, quantity_precision)
                
                # Check minimum position size
                actual_position_value = total_quantity * current_price
                if actual_position_value < 10:
                    logger.info(f"⚠️  [{strategy_name.upper()}] Position value too small: ${actual_position_value:.2f} (min $10)")
                    log_data['execution_reason'] = f"Position value too small: ${actual_position_value:.2f}"
                    db.log_strategy_run(log_data)
                    continue
                
                # Set leverage (default 1x for safety)
                leverage = risk_mgmt.get('leverage', 1)
                client.client.futures_change_leverage(symbol=symbol, leverage=leverage)
                
                # ═══════════════════════════════════════════════════════════════
                # LIVE TRADING: JEDEN order s DVĚMA TP levels a JEDNÍM SL
                # ═══════════════════════════════════════════════════════════════
                # Důvod: U live tradingu je žádoucí mít jeden order na Binance
                # s nastavenými multiple TP levels (50%, 100%) místo dvou 
                # separátních orderů. Toto je standardní best practice pro 
                # scale-out strategii na futures exchanges.
                #
                # Paper trading používá 2 separate trades v DB pro simulaci,
                # ale live trading má 1 skutečný order na Binance.
                # ═══════════════════════════════════════════════════════════════
                
                side = 'BUY' if action == 'LONG' else 'SELL'
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                
                logger.info(f"🚀 [{strategy_name.upper()}] Executing {action} trade:")
                logger.info(f"   Position Size: ${actual_position_value:.2f} ({position_size_pct*100:.1f}% of balance)")
                logger.info(f"   Quantity: {total_quantity} {symbol}")
                logger.info(f"   Leverage: {leverage}x")
                
                # Calculate fees (Binance Futures taker fee)
                fee_rate = config.TRADING_FEE_RATE
                
                # Execute ONE market order
                order = client.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=total_quantity
                )
                
                logger.info(f"   ✅ Market order placed: {order['orderId']} ({total_quantity} {symbol})")
                
                # FIX #2: Place STOP LOSS and TAKE PROFIT orders on Binance
                # Strategy: 2 TP levels + 2 SL levels for scale-out
                try:
                    sl_side = 'SELL' if action == 'LONG' else 'BUY'
                    half_quantity = round(total_quantity / 2, quantity_precision) if quantity_precision else total_quantity / 2
                    
                    # Get price precision for the symbol
                    price_precision = 2  # default
                    for filter in symbol_info['filters']:
                        if filter['filterType'] == 'PRICE_FILTER':
                            tick_size = float(filter['tickSize'])
                            price_precision = get_quantity_precision(tick_size)
                            break
                    
                    # Stop Loss 1: Původní SL pro 50% pozice (quick exit on original SL)
                    sl1_rounded = round(sl1, price_precision)
                    sl1_order = client.client.futures_create_order(
                        symbol=symbol,
                        side=sl_side,
                        type='STOP',
                        stopPrice=sl1_rounded,
                        price=sl1_rounded,
                        quantity=half_quantity,
                        reduceOnly=True,
                        timeInForce='GTC'
                    )
                    logger.info(f"   ✅ Stop Loss 1: {sl1_order['orderId']} @ ${sl1:.6f} (50% position)")
                    
                    # Stop Loss 2: Tighter SL pro druhou půlku (50% těsnější, breakeven style)
                    sl2_rounded = round(sl2, price_precision)
                    sl2_order = client.client.futures_create_order(
                        symbol=symbol,
                        side=sl_side,
                        type='STOP',
                        stopPrice=sl2_rounded,
                        price=sl2_rounded,
                        quantity=half_quantity,
                        reduceOnly=True,
                        timeInForce='GTC'
                    )
                    logger.info(f"   ✅ Stop Loss 2: {sl2_order['orderId']} @ ${sl2:.6f} (50% position, tighter)")
                    
                    # Take Profit 1: 50% pozice @ 50% TP
                    tp1_rounded = round(tp1, price_precision)
                    tp1_order = client.client.futures_create_order(
                        symbol=symbol,
                        side=sl_side,
                        type='TAKE_PROFIT',
                        stopPrice=tp1_rounded,
                        price=tp1_rounded,
                        quantity=half_quantity,
                        reduceOnly=True,
                        timeInForce='GTC'
                    )
                    logger.info(f"   ✅ Take Profit 1: {tp1_order['orderId']} @ ${tp1:.6f} (50% position)")
                    
                    # Take Profit 2: zbylých 50% @ 100% TP
                    tp2_rounded = round(tp2, price_precision)
                    tp2_order = client.client.futures_create_order(
                        symbol=symbol,
                        side=sl_side,
                        type='TAKE_PROFIT',
                        stopPrice=tp2_rounded,
                        price=tp2_rounded,
                        quantity=half_quantity,
                        reduceOnly=True,
                        timeInForce='GTC'
                    )
                    logger.info(f"   ✅ Take Profit 2: {tp2_order['orderId']} @ ${tp2:.6f} (50% position)")
                    
                except Exception as e:
                    logger.info(f"   ⚠️  Warning: Failed to place SL/TP orders: {str(e)}")
                    # Continue anyway - trade is open on Binance
                
                # NOTE: Live trades are NOT stored in DB trades table
                # Binance is the single source of truth for live positions
                # We only log execution in strategy_runs for audit
                
                logger.info(f"   ✅ Trade executed successfully on Binance")
                logger.info(f"   Entry: ${current_price:.6f}")
                logger.info(f"   SL1 (50%): ${sl1:.6f} | SL2 (50%, tighter): ${sl2:.6f}")
                logger.info(f"   TP1 (50%): ${tp1:.6f} | TP2 (50%): ${tp2:.6f}")
                
                # Log successful execution in strategy_runs
                log_data['executed'] = True
                log_data['execution_reason'] = f"Executed LIVE trade on Binance"
                log_data['binance_order_id'] = order['orderId']
                log_data['entry_price'] = current_price
                log_data['quantity'] = total_quantity
                log_data['position_value'] = actual_position_value
                log_data['sl1'] = sl1
                log_data['sl2'] = sl2
                log_data['tp1'] = tp1
                log_data['tp2'] = tp2
                db.log_strategy_run(log_data)
                
                executed_trades.append({
                    'strategy': strategy_name,
                    'binance_order_id': order['orderId'],
                    'action': action,
                    'symbol': symbol,
                    'entry_price': current_price,
                    'quantity': total_quantity,
                    'tp1': tp1,
                    'tp2': tp2,
                    'sl1': sl1,
                    'sl2': sl2
                })
                
            except Exception as e:
                logger.info(f"❌ [{strategy_name.upper()}] Error executing live trade: {str(e)}")
                log_data['execution_reason'] = f"Error: {str(e)}"
                db.log_strategy_run(log_data)
                import traceback
                traceback.print_exc()
                continue
        
        # FIX #6: Get statistics per strategy, not just by symbol
        if executed_trades:
            logger.info(f"\n📊 Live Trading Performance:")
            
            # Get overall stats
            first_symbol = executed_trades[0]['symbol']
            stats_all = db.get_trade_stats(first_symbol)
            logger.info(f"   OVERALL ({first_symbol}): {stats_all['total_trades']} trades total")
            if stats_all.get('closed_trades', 0) > 0:
                logger.info(f"      Win rate: {stats_all['win_rate']:.1f}% | P&L: ${stats_all['total_pnl']:.2f}")
            
            # Get per-strategy stats
            strategy_stats = {}
            for trade_info in executed_trades:
                strategy = trade_info['strategy']
                symbol = trade_info['symbol']
                stats = db.get_trade_stats(symbol, strategy)
                strategy_stats[strategy] = stats
                
                if stats['total_trades'] > 0:
                    if stats.get('closed_trades', 0) > 0:
                        logger.info(f"   {strategy.upper()}: {stats['total_trades']} trades | Win: {stats['win_rate']:.1f}% | P&L: ${stats['total_pnl']:.2f}")
                    else:
                        logger.info(f"   {strategy.upper()}: {stats['total_trades']} trades")
            
            # Update state (same format as paper trading)
            state['trade_execution'] = {
                "executed": True,
                "trades": executed_trades,
                "live": True,
                "stats": {
                    "overall": stats_all,
                    "strategies": strategy_stats
                }
            }
        else:
            state['trade_execution'] = {
                "executed": False,
                "live": True,
                "reason": "All strategies returned NEUTRAL or skipped"
            }
        
        # Final summary
        executed_count = len([t for t in executed_trades]) if 'executed_trades' in locals() else 0
        if executed_count > 0:
            logger.info(f"\n🔴 === LIVE TRADING EXECUTION END ===")
            logger.info(f"🔴 ✅ Successfully executed {executed_count} LIVE trade(s)")
        else:
            logger.info(f"\n🔴 === LIVE TRADING EXECUTION END ===")
            logger.info(f"🔴 ℹ️  No trades executed this cycle")
        logger.info("")
        
        return state
        
    except Exception as e:
        logger.info(f"🔴 ❌ LIVE TRADING ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        state['trade_execution'] = {
            "executed": False,
            "live": True,
            "error": str(e)
        }
        logger.info(f"\n🔴 === LIVE TRADING EXECUTION END (Error) ===\n")
        return state
