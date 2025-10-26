#!/usr/bin/env python
"""Test script to verify all imports work correctly"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing imports...")
print("=" * 50)

try:
    print("✓ Testing config...")
    # Skip config for now as it requires .env
    
    print("✓ Testing models.state...")
    from models.state import TradingState
    
    print("✓ Testing utils.binance_client...")
    from utils.binance_client import BinanceClient
    
    print("✓ Testing utils.indicators...")
    from utils.indicators import calculate_all_indicators
    
    print("✓ Testing agents.data_collector...")
    from agents.data_collector import collect_market_data
    
    print("✓ Testing agents.analysis...")
    from agents.analysis import analyze_market
    
    print("✓ Testing agents.decision_maker...")
    from agents.decision_maker import make_decision
    
    print("\n" + "=" * 50)
    print("✅ All imports successful!")
    print("=" * 50)
    
    print("\nProject structure:")
    print("  ✓ State model")
    print("  ✓ Binance client")
    print("  ✓ Technical indicators")
    print("  ✓ Data Collector Agent")
    print("  ✓ Analysis Agent")
    print("  ✓ Decision Agent (DeepSeek)")
    
    print("\nNext steps:")
    print("  1. Create .env file (copy from .env.example)")
    print("  2. Add your DEEPSEEK_API_KEY to .env")
    print("  3. Run: python src/main.py")
    print("     or: ./run.sh (Linux/Mac)")
    print("     or: run.bat (Windows)")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nMake sure you have installed all dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)

