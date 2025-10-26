# Changelog

## [Latest] - Bot Management + Candle Synchronization

### ✅ Added
- **Bot Control Script** (`bot.sh`)
  - Background execution (nohup)
  - Start/stop/restart/status commands
  - PID file management
  - Automatic health checks
  - Integrated stats display
  
- **Candle Synchronization**
  - First analysis runs immediately
  - Subsequent analyses align to TF candle start
  - Automatic calculation for any timeframe
  - Perfect timing for accurate indicators
  - Example: 15m TF → analyses at XX:00, XX:15, XX:30, XX:45

- **Autonomous Trading Bot** (`trading_bot.py`)
  - Runs analysis + monitoring in one process
  - Continuous operation (24/7)
  - Configurable intervals
  - Graceful shutdown (Ctrl+C)
  - Heartbeat monitoring

- **Comprehensive Logging System**
  - 3-tier logging (main, detailed, errors)
  - Automatic log rotation (10MB/50MB/5MB)
  - Structured format with timestamps
  - Function-level tracing
  - Error stack traces
  - Interactive log viewer (`view_logs.sh`)
  - Searchable history

- **Trend Reversal Detection**
  - Pattern recognition (Higher Highs/Lows, Lower Highs/Lows)
  - Multi-factor confirmation (5 factors)
  - Strength scoring (0-100 points)
  - Reversal type classification (bullish/bearish)
  - Early trend change detection
  - Integration in AI prompt
  - Visual alerts in console

- **Paper Trading System**
  - Paper Trading Agent (4th agent)
  - SQLite database for trade storage
  - Automatic trade execution and tracking
  - Performance statistics (win rate, P&L)
  - Trade Manager CLI tool
  - Complete trade lifecycle (OPEN → CLOSED)
  - P&L calculation on SL/TP hits

- **ATR-Based Risk Management**
  - ATR (Average True Range) calculation
  - Dynamic stop loss: 1.5x ATR
  - Dynamic take profit: 3.0x ATR
  - Volatility-adjusted positioning
  - Risk/Reward ratio calculation
  - Automatic calculation při LONG/SHORT

- **Flexible Entry Strategy**
  - AI rozhoduje sám (pullback vs aligned)
  - Context-aware decisions
  - Not rigid rules
  - Může vstoupit i při aligned running s confirmací

- **Enhanced AI Prompt**
  - ATR data v promptu
  - Entry setup pros/cons
  - Examples kdy vstoupit/nevstoupit
  - Risk management awareness

### 🔧 Changed
- LangGraph: Added 4th agent (Paper Trading)
- State model: Added trade_execution field
- Main output: Added trade execution section with stats
- Decision Agent: Auto-calculates SL/TP after AI decision
- Output: Zobrazuje risk management + paper trade info
- Analysis: Flexible entry quality assessment
- Documentation: More nuanced guidance
- .gitignore: Ignore data/ directory

### 📊 Technical Details
- **Bot control**: bot.sh (start/stop/status/logs/restart)
- **Execution**: Background (nohup + PID file)
- **Timing**: First analysis immediate, then candle-synced
- **Analysis**: Aligned to TF candle start (accurate data)
- **Monitoring**: Every 60s (configurable)
- **Logging**: 3 files (main 10MB, detailed 50MB, errors 5MB)
- **Log rotation**: Automatic, keeps 10/5/5 files
- **Reversal factors**: 5 (EMA, MACD, Pattern, RSI, Volume)
- **Reversal threshold**: 75+ strong, 60-74 medium, 40-59 weak
- **Pattern lookback**: 20 periods
- **ATR period**: 14 (standard)
- **Stop/TP**: 1.5x/3.0x ATR
- **Min R/R**: 1:2.0 (1:4+ for reversals)
- **Database**: SQLite3 (data/paper_trades.db)
- **Operation**: 24/7 autonomous

---

## [v1.2] - Multi-Timeframe + Results Directory

### ✅ Added
- **Multi-Timeframe Analysis**
  - 1h timeframe pro trend analysis
  - 15m timeframe pro entry timing
  - Timeframe confluence detection
  - Enhanced DeepSeek prompt s MTF data
  - Aligned vs divergent signal detection

- **Results Directory**
  - Automatické vytváření `results/` složky
  - JSON výsledky se ukládají do `results/`
  - UTF-8 encoding pro správné zobrazení českých znaků
  - README v results složce

- **Documentation**
  - `MULTI_TIMEFRAME.md` - kompletní MTF guide
  - `ORDERBOOK_ANALYSIS.md` - orderbook guide
  - `ORDERBOOK_FEATURE_SUMMARY.md` - orderbook feature summary

### 🔧 Changed
- Config: `TIMEFRAME` → `TIMEFRAME_HIGHER` + `TIMEFRAME_LOWER`
- Analysis Agent: Analyzuje oba timeframes
- Decision Agent: Enhanced prompt s MTF confluence
- Main output: Multi-timeframe summary display
- `.gitignore`: Ignoruje results/ složku

### 📊 Technical Details
- API calls: +1 per timeframe (celkem +1 call)
- Data structure: Nested timeframe indicators
- Performance impact: +200-400ms (další timeframe)

---

## [v1.1] - Orderbook Analysis

### ✅ Added
- **Orderbook Analysis**
  - Bid/Ask imbalance calculation
  - Order depth analysis (0.5%, 1.0%, 2.0%)
  - Large orders detection (walls)
  - Spread analysis
  - Real-time pressure signals

- **Integration**
  - Binance client: `get_orderbook()` method
  - Analysis Agent: Orderbook integration
  - Decision Agent: Orderbook v AI promptu
  - Main output: Orderbook display section

### 📊 Metrics
- 100 bid levels + 100 ask levels analyzováno
- Pressure signals: strong_buy/buy/balanced/sell/strong_sell
- Wall detection: 3x average = wall

---

## [v1.0] - Initial Release

### ✅ Core Features
- **Multi-Agent System**
  - Data Collector Agent
  - Analysis Agent
  - Decision Agent (DeepSeek AI)
  - LangGraph orchestration

- **Technical Indicators**
  - RSI (14 period)
  - MACD (12, 26, 9)
  - EMA 20/50
  - Bollinger Bands
  - Support/Resistance levels
  - Volume analysis

- **Sentiment Analysis**
  - Funding rate sentiment
  - Volume momentum

- **AI Integration**
  - DeepSeek AI for decisions
  - Structured prompts
  - JSON response parsing

- **Output**
  - Console display
  - JSON export
  - Comprehensive logging

---

## Planned Features

### 🔮 Future Enhancements
- [ ] Backtesting module
- [ ] Web dashboard
- [ ] Multiple symbols support
- [ ] Email/Telegram notifications
- [ ] Risk management module
- [ ] Position sizing calculator
- [ ] Historical results analysis
- [ ] Performance metrics tracking

### 🎯 Short-term
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance optimization
- [ ] Error recovery improvements

---

**Latest Version**: Multi-Timeframe Analysis + Results Directory
**Status**: ✅ Production Ready

