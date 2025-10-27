"""Configuration management"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AI API Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Stock News API
STOCKNEWS_API_KEY = os.getenv("STOCKNEWS_API_KEY")

# Trading Configuration
SYMBOL = os.getenv("SYMBOL", "SOLUSDT")
TIMEFRAME_HIGHER = os.getenv("TIMEFRAME_HIGHER", "1h")  # Trend timeframe
TIMEFRAME_LOWER = os.getenv("TIMEFRAME_LOWER", "15m")   # Entry timeframe
CANDLES_LIMIT = int(os.getenv("CANDLES_LIMIT", "100"))

# Binance API Configuration (optional for public data)
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# Bot Configuration
BOT_ANALYSIS_INTERVAL = int(os.getenv("BOT_ANALYSIS_INTERVAL", "900"))  # 15 min
BOT_MONITOR_INTERVAL = int(os.getenv("BOT_MONITOR_INTERVAL", "60"))     # 1 min

# Trading Fees (Binance Futures)
# Maker: 0.02% (0.0002), Taker: 0.05% (0.0005)
TRADING_FEE_RATE = float(os.getenv("TRADING_FEE_RATE", "0.0005"))  # Default: 0.05% (taker)

# Live Trading Configuration
ENABLE_LIVE_TRADING = os.getenv("ENABLE_LIVE_TRADING", "false").lower() == "true"
LIVE_POSITION_SIZE = float(os.getenv("LIVE_POSITION_SIZE", "100"))  # Default: $100 per trade

# Validation
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is required in .env file")

# Optional: Warn if macro strategy APIs missing
if not STOCKNEWS_API_KEY:
    import warnings
    warnings.warn("STOCKNEWS_API_KEY not set - MACRO strategy will have limited data")

