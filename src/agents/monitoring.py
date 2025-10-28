"""
Monitoring Agent for automated system health checks and maintenance tasks.

This agent runs every minute (independently of trading cycles) to:
- Check for orphaned orders (orders without corresponding positions)
- Cancel orphaned orders to prevent unexpected executions
- Log monitoring activities

Author: DeepTrader
"""

import sys
import os
# Fix imports when running standalone
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import List, Dict, Optional
from datetime import datetime
from utils.binance_client import BinanceClient
import config

logger = logging.getLogger(__name__)


class MonitoringAgent:
    """
    Monitoring agent that performs system health checks and maintenance.
    Runs independently every minute.
    """
    
    def __init__(self, logger_instance=None):
        """
        Initialize monitoring agent
        
        Args:
            logger_instance: Optional logger instance to use (defaults to module logger)
        """
        self.client = BinanceClient()
        self.last_run = None
        self.run_count = 0
        self.orphaned_orders_cancelled = 0
        self.logger = logger_instance if logger_instance else logger
    
    def run(self) -> Dict:
        """
        Execute all monitoring tasks.
        
        Returns:
            Dict with monitoring results
        """
        self.run_count += 1
        self.last_run = datetime.now()
        
        self.logger.info(f"🔍 [MONITORING] Starting monitoring cycle #{self.run_count}")
        
        results = {
            'timestamp': self.last_run.isoformat(),
            'run_count': self.run_count,
            'tasks': {}
        }
        
        # Task 1: Check and cancel orphaned orders
        orphaned_result = self.check_and_cancel_orphaned_orders()
        results['tasks']['orphaned_orders'] = orphaned_result
        
        self.logger.info(f"🔍 [MONITORING] Cycle #{self.run_count} complete")
        
        return results
    
    def check_and_cancel_orphaned_orders(self) -> Dict:
        """
        Check for orphaned orders (orders without corresponding open positions).
        Cancel any orphaned orders found.
        
        An order is considered orphaned if:
        - It's a TP or SL order
        - There's no open position for the same symbol
        
        Returns:
            Dict with task results
        """
        try:
            self.logger.info("🔍 [MONITORING] Checking for orphaned orders...")
            
            # Get all open orders
            open_orders = self.client.get_open_orders()
            
            if not open_orders:
                self.logger.info("🔍 [MONITORING] ✅ No open orders found")
                return {
                    'status': 'success',
                    'open_orders_count': 0,
                    'orphaned_orders_found': 0,
                    'orphaned_orders_cancelled': 0
                }
            
            self.logger.info(f"🔍 [MONITORING] Found {len(open_orders)} open orders")
            
            # Get all open positions
            open_positions = self.client.get_open_positions()
            position_symbols = {pos['symbol'] for pos in open_positions}
            
            self.logger.info(f"🔍 [MONITORING] Found {len(open_positions)} open positions: {sorted(position_symbols)}")
            
            # Find orphaned orders (orders without corresponding positions)
            orphaned_orders = []
            for order in open_orders:
                symbol = order['symbol']
                order_type = order.get('type', '')
                
                # Check if order's symbol has an open position
                if symbol not in position_symbols:
                    orphaned_orders.append(order)
                    self.logger.info(f"🔍 [MONITORING] ⚠️  Orphaned order found: {symbol} - {order_type} (Order ID: {order['order_id']})")
            
            # Cancel orphaned orders
            cancelled_count = 0
            if orphaned_orders:
                self.logger.info(f"🔍 [MONITORING] ❌ Found {len(orphaned_orders)} orphaned orders, cancelling...")
                
                for order in orphaned_orders:
                    try:
                        symbol = order['symbol']
                        order_id = order['order_id']
                        order_type = order.get('type', '')
                        
                        # Cancel the order
                        self.client.cancel_order(symbol, order_id)
                        cancelled_count += 1
                        self.orphaned_orders_cancelled += 1
                        
                        self.logger.info(f"🔍 [MONITORING] ✅ Cancelled orphaned order: {symbol} - {order_type} (ID: {order_id})")
                        
                    except Exception as e:
                        self.logger.error(f"🔍 [MONITORING] ❌ Error cancelling order {order_id} for {symbol}: {e}")
            else:
                self.logger.info("🔍 [MONITORING] ✅ No orphaned orders found")
            
            return {
                'status': 'success',
                'open_orders_count': len(open_orders),
                'orphaned_orders_found': len(orphaned_orders),
                'orphaned_orders_cancelled': cancelled_count,
                'position_symbols': sorted(position_symbols),
                'orphaned_orders': [
                    {
                        'symbol': o['symbol'],
                        'order_id': o['order_id'],
                        'type': o.get('type', 'UNKNOWN'),
                        'side': o.get('side', 'UNKNOWN')
                    }
                    for o in orphaned_orders
                ]
            }
            
        except Exception as e:
            self.logger.error(f"🔍 [MONITORING] ❌ Error checking orphaned orders: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_stats(self) -> Dict:
        """
        Get monitoring agent statistics.
        
        Returns:
            Dict with statistics
        """
        return {
            'total_runs': self.run_count,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'total_orphaned_orders_cancelled': self.orphaned_orders_cancelled
        }


def run_monitoring_cycle() -> Dict:
    """
    Convenience function to run a single monitoring cycle.
    Can be called from the main bot.
    
    Returns:
        Dict with monitoring results
    """
    agent = MonitoringAgent()
    return agent.run()


if __name__ == "__main__":
    # For testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)8s | %(message)s'
    )
    
    print("\n" + "="*80)
    print("MONITORING AGENT TEST RUN")
    print("="*80 + "\n")
    
    agent = MonitoringAgent()
    results = agent.run()
    
    print("\n" + "="*80)
    print("MONITORING RESULTS:")
    print("="*80)
    import json
    print(json.dumps(results, indent=2))
    
    stats = agent.get_stats()
    print("\n" + "="*80)
    print("AGENT STATISTICS:")
    print("="*80)
    print(json.dumps(stats, indent=2))

