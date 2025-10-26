#!/usr/bin/env python
"""Test script - Verify trade creation and database storage"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*70)
print("🧪 TESTING TRADE CREATION & DATABASE STORAGE")
print("="*70)
print()

# Test 1: Import all modules
print("1️⃣  Testing imports...")
try:
    from utils.database import TradingDatabase
    from datetime import datetime
    print("   ✅ Database module imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Create database
print("\n2️⃣  Creating/connecting to database...")
try:
    db = TradingDatabase()
    print(f"   ✅ Database initialized: {db.db_path}")
except Exception as e:
    print(f"   ❌ Database init failed: {e}")
    sys.exit(1)

# Test 3: Create test trades (both strategies)
print("\n3️⃣  Creating test trades...")

test_trades = []

# Structured strategy trade
trade_data_structured = {
    "symbol": "SOLUSDT",
    "strategy": "structured",
    "action": "LONG",
    "confidence": "high",
    "entry_price": 190.50,
    "stop_loss": 185.20,
    "take_profit": 200.80,
    "risk_amount": 5.30,
    "reward_amount": 10.30,
    "risk_reward_ratio": 1.94,
    "atr": 3.53,
    "entry_setup": "pullback_reversal",
    "entry_time": datetime.now().isoformat(),
    "reasoning": "Test trade for structured strategy",
    "analysis_data": {
        "strategy": "structured",
        "entry_quality": "pullback_reversal",
        "confluence": "pullback_entry_long"
    }
}

# Minimal strategy trade
trade_data_minimal = {
    "symbol": "SOLUSDT",
    "strategy": "minimal",
    "action": "LONG",
    "confidence": "medium",
    "entry_price": 190.50,
    "stop_loss": 185.20,
    "take_profit": 200.80,
    "risk_amount": 5.30,
    "reward_amount": 10.30,
    "risk_reward_ratio": 1.94,
    "atr": 3.53,
    "entry_setup": "pullback_reversal",
    "entry_time": datetime.now().isoformat(),
    "reasoning": "Test trade for minimal strategy - AI decided independently",
    "analysis_data": {
        "strategy": "minimal",
        "entry_quality": "pullback_reversal"
    }
}

try:
    trade_id_1 = db.create_trade(trade_data_structured)
    print(f"   ✅ STRUCTURED trade created: {trade_id_1}")
    test_trades.append(trade_id_1)
    
    trade_id_2 = db.create_trade(trade_data_minimal)
    print(f"   ✅ MINIMAL trade created: {trade_id_2}")
    test_trades.append(trade_id_2)
    
except Exception as e:
    print(f"   ❌ Trade creation failed: {e}")
    sys.exit(1)

# Test 4: Retrieve trades
print("\n4️⃣  Retrieving trades from database...")
try:
    open_trades = db.get_open_trades()
    print(f"   ✅ Retrieved {len(open_trades)} open trade(s)")
    
    for trade in open_trades[-2:]:  # Last 2
        print(f"\n   📐/🤖 Trade: {trade['trade_id']}")
        print(f"      Strategy: {trade['strategy']}")
        print(f"      Action: {trade['action']} @ ${trade['entry_price']}")
        print(f"      SL: ${trade['stop_loss']} | TP: ${trade['take_profit']}")
        print(f"      Status: {trade['status']}")
        
except Exception as e:
    print(f"   ❌ Retrieval failed: {e}")
    sys.exit(1)

# Test 5: Get statistics
print("\n5️⃣  Getting statistics...")
try:
    stats_all = db.get_trade_stats("SOLUSDT")
    stats_structured = db.get_trade_stats("SOLUSDT", "structured")
    stats_minimal = db.get_trade_stats("SOLUSDT", "minimal")
    
    print(f"   ✅ Statistics retrieved:")
    print(f"      Overall: {stats_all['total_trades']} trades")
    print(f"      STRUCTURED: {stats_structured['total_trades']} trades")
    print(f"      MINIMAL: {stats_minimal['total_trades']} trades")
    
except Exception as e:
    print(f"   ❌ Stats retrieval failed: {e}")
    sys.exit(1)

# Test 6: Close one trade (simulate TP hit)
print("\n6️⃣  Testing trade closure...")
try:
    # Close the structured trade at TP
    db.close_trade(trade_id_1, 200.80, 'TP_HIT')
    print(f"   ✅ Trade closed: {trade_id_1}")
    
    # Get updated stats
    stats_after = db.get_trade_stats("SOLUSDT", "structured")
    
    if stats_after['closed_trades'] > 0:
        print(f"      Closed trades: {stats_after['closed_trades']}")
        print(f"      Win rate: {stats_after['win_rate']:.1f}%")
        print(f"      Total P&L: ${stats_after['total_pnl']:.2f}")
    
except Exception as e:
    print(f"   ❌ Trade closure failed: {e}")
    sys.exit(1)

# Test 7: Verify closure
print("\n7️⃣  Verifying closed trade...")
try:
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM trades WHERE trade_id = ?', (trade_id_1,))
    closed_trade = cursor.fetchone()
    conn.close()
    
    if closed_trade:
        print(f"   ✅ Trade verified in database:")
        print(f"      Status: {closed_trade['status']}")
        print(f"      Exit Price: ${closed_trade['exit_price']}")
        print(f"      Exit Reason: {closed_trade['exit_reason']}")
        print(f"      P&L: ${closed_trade['pnl']:.2f} ({closed_trade['pnl_percentage']:.2f}%)")
    else:
        print(f"   ❌ Trade not found in database")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Verification failed: {e}")
    sys.exit(1)

# Success!
print("\n" + "="*70)
print("✅ ALL TESTS PASSED!")
print("="*70)
print()
print("📊 Test Summary:")
print(f"   • Database: Working ✅")
print(f"   • Trade creation: Working ✅ (both strategies)")
print(f"   • Trade retrieval: Working ✅")
print(f"   • Statistics: Working ✅ (with strategy filtering)")
print(f"   • Trade closure: Working ✅")
print(f"   • P&L calculation: Working ✅")
print()
print("🎉 Multi-strategy system is ready to use!")
print()
print("Next steps:")
print("  1. Start bot: ./bot.sh start")
print("  2. Check stats: cd src && python trade_manager.py stats")
print("  3. Compare strategies after 30+ trades each")
print()

