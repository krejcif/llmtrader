#!/usr/bin/env python
"""Test script for dynamic strategy system"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from strategy_config import (
    get_active_strategies, 
    get_all_intervals,
    get_strategies_by_interval,
    get_min_interval,
    StrategyConfig
)


def test_strategy_system():
    """Test that strategy configuration system works"""
    print("="*70)
    print("TESTING DYNAMIC STRATEGY SYSTEM")
    print("="*70)
    
    # Test 1: Get active strategies
    print("\n1️⃣  Testing get_active_strategies()...")
    active = get_active_strategies()
    print(f"   ✅ Found {len(active)} active strategies:")
    for s in active:
        print(f"      - {s.name}: {s.timeframe_higher}/{s.timeframe_lower} every {s.interval_minutes}min")
    
    assert len(active) > 0, "No active strategies found!"
    assert all(s.enabled for s in active), "Non-enabled strategy in active list!"
    
    # Test 2: Get all intervals
    print("\n2️⃣  Testing get_all_intervals()...")
    intervals = get_all_intervals()
    print(f"   ✅ Found {len(intervals)} unique intervals: {intervals} minutes")
    
    assert len(intervals) > 0, "No intervals found!"
    assert all(isinstance(i, int) for i in intervals), "Non-integer interval!"
    
    # Test 3: Get strategies by interval
    print("\n3️⃣  Testing get_strategies_by_interval()...")
    for interval in intervals:
        strats = get_strategies_by_interval(interval)
        print(f"   ✅ Interval {interval}min: {len(strats)} strategy/strategies")
        for s in strats:
            print(f"      - {s.name}")
        assert len(strats) > 0, f"No strategies for interval {interval}!"
    
    # Test 4: Get minimum interval
    print("\n4️⃣  Testing get_min_interval()...")
    min_int = get_min_interval()
    print(f"   ✅ Minimum interval: {min_int} minutes")
    
    assert min_int == min(intervals), "Min interval doesn't match!"
    
    # Test 5: Strategy config structure
    print("\n5️⃣  Testing StrategyConfig structure...")
    for s in active:
        print(f"   Checking {s.name}...")
        assert hasattr(s, 'name'), f"{s.name}: Missing 'name'"
        assert hasattr(s, 'decision_func'), f"{s.name}: Missing 'decision_func'"
        assert hasattr(s, 'timeframe_higher'), f"{s.name}: Missing 'timeframe_higher'"
        assert hasattr(s, 'timeframe_lower'), f"{s.name}: Missing 'timeframe_lower'"
        assert hasattr(s, 'interval_minutes'), f"{s.name}: Missing 'interval_minutes'"
        assert hasattr(s, 'enabled'), f"{s.name}: Missing 'enabled'"
        assert callable(s.decision_func), f"{s.name}: decision_func not callable!"
        print(f"   ✅ {s.name} structure OK")
    
    # Test 6: State keys
    print("\n6️⃣  Testing state key generation...")
    for s in active:
        assert s.market_data_key == f"market_data_{s.name}", f"Wrong market_data_key for {s.name}"
        assert s.analysis_key == f"analysis_{s.name}", f"Wrong analysis_key for {s.name}"
        assert s.recommendation_key == f"recommendation_{s.name}", f"Wrong recommendation_key for {s.name}"
        print(f"   ✅ {s.name} keys: {s.market_data_key}, {s.analysis_key}, {s.recommendation_key}")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    
    # Summary
    print("\n📊 SYSTEM SUMMARY:")
    print(f"   Active strategies: {len(active)}")
    print(f"   Unique intervals: {intervals}")
    print(f"   Fastest strategy runs every: {min_int} minutes")
    print(f"\n   Strategy breakdown:")
    for interval in sorted(intervals):
        strats = get_strategies_by_interval(interval)
        print(f"      Every {interval}min: {', '.join(s.name for s in strats)}")
    
    print("\n🚀 System is ready! Run with:")
    print("   cd src && python trading_bot_dynamic.py")
    print()


def test_add_new_strategy():
    """Demonstrate how easy it is to add a new strategy"""
    print("\n" + "="*70)
    print("DEMO: Adding a new strategy")
    print("="*70)
    
    print("\n📝 Steps to add a new strategy:")
    print("   1. Create decision function in src/agents/decision_<name>.py")
    print("   2. Import it in src/strategy_config.py")
    print("   3. Add StrategyConfig to STRATEGIES list")
    print("   4. That's it! Bot will automatically use it.")
    
    print("\n💡 Example code to add in strategy_config.py:")
    print("""
    StrategyConfig(
        name="my_new_strategy",
        decision_func=make_decision_my_new_strategy,
        timeframe_higher="4h",
        timeframe_lower="1h",
        interval_minutes=60,
        enabled=True
    ),
    """)
    
    print("✅ No workflow changes needed!")
    print("✅ No bot.py modifications needed!")
    print("✅ Just add config and go!")
    print()


if __name__ == "__main__":
    try:
        test_strategy_system()
        test_add_new_strategy()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

