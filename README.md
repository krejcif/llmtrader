# Autonomous Trading Bot 🤖

**Plně autonomní multi-agent trading systém** využívající **LangGraph** a **DeepSeek AI**.

Běží 24/7, analyzuje Binance Futures, detekuje trendy a reversaly, vytváří paper trades, monitoruje pozice a trackuje performance. Všechno automaticky. 🚀

## ⚡ Quick Start

```bash
# 1. Setup (5 min)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Add your DEEPSEEK_API_KEY

# 2. Start bot (1 command)
./bot.sh start

# 3. Check status
./bot.sh status

# 4. View logs
./bot.sh logs

# Stop when needed
./bot.sh stop
```

**To je všechno!** Bot běží na pozadí, analyzuje přesně na začátku každého timeframe candle, traduje a monitoruje autonomně.

## 🎯 Funkce

- **Data Collection**: Automatické stahování market dat z Binance Futures API
- **Multi-Timeframe Analysis**: Analýza na 2 timeframes pro **optimal entry timing**:
  - **1h (Higher TF)**: Určení celkového trendu a směru
  - **15m (Lower TF)**: Detekce pullback reversal pro entry
  - **Pullback Entry Strategy**: Vstup při návratu do trendu (lepší R/R než pozdní entry)
  - Entry setup classification (pullback_reversal, trend_following, wait, avoid)
- **Trend Reversal Detection**: Detekce skutečné změny trendu
  - **Pattern Recognition**: Higher Highs/Lows, Lower Highs/Lows detection
  - **Multi-Factor Confirmation**: 5 faktorů (EMA, MACD, Pattern, RSI, Volume)
  - **Strength Scoring**: 0-100 (strong/medium/weak/none)
  - **Early Entry**: Catching major trend changes pro huge R/R (1:4+)
- **Technical Analysis**: Výpočet komplexních technických indikátorů:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - EMA 20/50 (Exponential Moving Averages)
  - Bollinger Bands
  - Support/Resistance levels
  - Volume analysis
- **Orderbook Analysis**: Analýza orderbooku v reálném čase:
  - Bid/Ask imbalance (buying vs selling pressure)
  - Order depth analysis
  - Large orders detection (walls)
  - Spread analysis
- **Sentiment Analysis**: Analýza funding rate, volume momentum a orderbook pressure
- **AI Decision Making**: DeepSeek AI model pro finální trading rozhodnutí
  - **Flexible Strategy**: AI rozhoduje sám kdy vstoupit (pullback reversal vs aligned running)
  - **Context-Aware**: Zvažuje všechny faktory (orderbook, RSI, volume, S/R)
  - **Not Rigid**: Může vstoupit i při aligned running pokud všechno potvrzuje
- **Risk Management**: ATR-driven stop loss a take profit
  - **Dynamic Stops**: 1.5x ATR (adjusts to volatility)
  - **Profit Targets**: 3.0x ATR (minimum 1:2 R/R ratio)
  - **Volatility-Adjusted**: Široké stops ve volatile markets, tight v klidných
- **Paper Trading**: Automatické ukládání trades do SQLite databáze
  - **Trade Execution**: Každý LONG/SHORT signál = paper trade
  - **Performance Tracking**: Win rate, P&L, statistics
  - **Trade History**: Kompletní historie všech trades
  - **CLI Manager**: Zobrazení a správa trades
- **Multi-Agent Architecture**: Modulární design s 4 specializovanými agenty

## 📋 Požadavky

- Python 3.10+
- DeepSeek API key (získejte na [platform.deepseek.com](https://platform.deepseek.com))

## 🔧 Instalace

1. **Naklonujte/stáhněte projekt**

2. **Vytvořte virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# nebo
venv\Scripts\activate  # Windows
```

3. **Nainstalujte závislosti**
```bash
pip install -r requirements.txt
```

4. **Nakonfigurujte environment**

Vytvořte soubor `.env` v root složce projektu:
```bash
cp .env.example .env
```

Upravte `.env` a doplňte váš DeepSeek API key:
```env
# DeepSeek API (REQUIRED)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Trading Configuration
SYMBOL=SOLUSDT
TIMEFRAME_HIGHER=1h   # Trend timeframe
TIMEFRAME_LOWER=15m   # Entry timeframe
CANDLES_LIMIT=100
```

## 🚀 Použití

### 🤖 Autonomous Bot (Recommended)

**Bot Management:**

```bash
./bot.sh start      # Start bot in background
./bot.sh status     # Check bot status + stats
./bot.sh logs       # View live logs
./bot.sh stop       # Stop bot gracefully
./bot.sh restart    # Restart bot
```

**Bot features:**
- ✅ Běží na pozadí (background)
- ✅ První analýza ihned
- ✅ Další analýzy **3s PO uzavření TF candle** (garantuje complete data!)
  - Example 15m TF: analýzy v 00:00:03, 00:15:03, 00:30:03, 00:45:03
  - Binance API má čas finalizovat svíčku
  - ✅ Pouze CLOSED candles = accurate indicators
- ✅ Monitoruje trades každou minutu
- ✅ Zavírá při SL/TP automaticky
- ✅ Kompletní logging do logs/

**Nebo manuální způsob (2 parts):**

### Spuštění analýzy:
```bash
./run.sh
```

### Spuštění monitoru (povinné pro complete tracking):
```bash
# Option 1: Continuous (recommended for day trading)
./monitor.sh --continuous

# Option 2: Manual check (kdykoli)
./monitor.sh

# Option 3: Cron job (automatic každou hodinu)
crontab -e
# Add: 0 * * * * cd /path/to/langtest && ./monitor.sh >> monitor.log 2>&1
```

### Co systém dělá:
1. Stažení aktuálních dat z Binance Futures (SOLUSDT)
2. Výpočet technických indikátorů a sentiment analýzu na obou timeframes
3. AI-powered rozhodnutí pomocí DeepSeek
4. **Paper trade execution** - uložení do SQLite databáze
5. Zobrazení doporučení a uložení výsledku do `results/` složky

## 📊 Příklad výstupu

```
============================================================
🚀 Multi-Agent Trading System
   Powered by LangGraph & DeepSeek AI
============================================================

🔄 Starting analysis for SOLUSDT...

📊 Collecting multi-timeframe market data for SOLUSDT...
   Timeframes: 1h (trend), 15m (entry)
✅ Market data collected:
   Current price: $145.32
   Funding rate: 0.000100
   1h: 100 bars
   15m: 100 bars
   Orderbook: 100 bids, 100 asks

🔬 Analyzing market data...
   Analyzing 1h (trend)...
   Analyzing 15m (entry)...

✅ Multi-timeframe analysis completed:

   📈 1H (Trend Timeframe):
      RSI: 65.4 (neutral)
      MACD: bullish
      EMA Trend: bullish
      S/R: middle

   ⚡ 15M (Entry Timeframe):
      RSI: 58.2 (neutral)
      MACD: bullish
      EMA Trend: bullish
      BB: middle

   🔄 TREND REVERSAL DETECTED!
      Type: bullish_reversal
      Strength: STRONG (85/100)
      Confirmations (5):
         ✓ EMA crossover bullish
         ✓ MACD bullish crossover
         ✓ Higher highs/lows pattern
         ✓ RSI bullish zone
         ✓ Volume surge
      💎 Strong reversal - high probability setup!

   🎯 Entry Setup: PULLBACK REVERSAL
      Status: pullback entry long
      💡 Pullback reversal - Usually better R/R

🤖 Making trading decision with DeepSeek AI...
   Calling DeepSeek API...
✅ Decision made:
   Action: LONG
   Confidence: high
   Reasoning: Strong bullish momentum with MACD crossover...

============================================================
📈 TRADING RECOMMENDATION
============================================================

📊 Market: SOLUSDT
💰 Current Price: $145.32
📅 Time: 2025-10-23 12:34:56

🎯 RECOMMENDATION: LONG
🔒 Confidence: HIGH

💰 RISK MANAGEMENT (ATR-Driven):
   Entry Price:   $190.38
   Stop Loss:     $185.20 (-2.72%)
   Take Profit:   $200.74 (+5.44%)
   
   Risk:   $5.18 (2.72%)
   Reward: $10.36 (5.44%)
   R/R Ratio: 1:2.0
   
   ATR (14): $3.45 (1.81% of price)
   Stop: 1.5x ATR | Target: 3.0x ATR

💡 Reasoning:
   Pullback reversal s excellent confirmací. MACD crossover,
   orderbook buy pressure 58%, RSI healthy 52. Optimal entry timing.

🔑 Key Factors:
   1. Strong trend reversal (85/100) - catching trend change early
   2. 5 confirmation factors align perfectly
   3. Orderbook 62% buy pressure confirms new direction

📊 Multi-Timeframe Technical Summary:

   📈 1H (Trend):
      EMA: bullish
      MACD: bullish
      RSI: 65.4 (neutral)

   ⚡ 15M (Entry):
      EMA: bullish
      MACD: bullish
      RSI: 58.2 (neutral)
      BB: middle

   🎯 Entry Setup: PULLBACK REVERSAL
      Status: pullback entry long
      💡 OPTIMAL - Pullback reversal entry (best R/R)

📖 Orderbook:
   Bid/Ask: 52.3% / 47.7%
   Pressure: buy
   Spread: 0.0123%

💭 Sentiment:
   Funding: neutral
   Volume: positive
   Orderbook: buy

============================================================

💼 PAPER TRADE EXECUTION:
   Status: ✅ EXECUTED
   Trade ID: SOLUSDT_20251023_123456
   Stored in database: paper_trades.db

   📊 Your Trading Stats:
      Total trades: 5
      Open: 2 | Closed: 3
      Win rate: 66.7%
      Total P&L: $15.23

============================================================

💾 Result saved to: result_SOLUSDT_20251023_123456.json
   Location: /path/to/langtest/results/result_SOLUSDT_20251023_123456.json
```

Všechny výsledky se automaticky ukládají do složky `results/` a trades do `data/paper_trades.db`.

## 🏗️ Architektura

Systém používá **LangGraph** pro orchestraci 3 specializovaných agentů:

```
START
  ↓
[Data Collector Agent]
  │  - Získává data z Binance Futures API
  │  - Multi-timeframe data (1h + 15m)
  │  - Current price, funding rate, orderbook
  ↓
[Analysis Agent]
  │  - Počítá technické indikátory pro oba timeframes
  │  - Detekuje trend patterns (HH/HL, LH/LL)
  │  - Detekuje trend reversals (multi-factor)
  │  - Detekuje entry setups (pullback/aligned)
  │  - Analyzuje orderbook
  │  - Analyzuje sentiment
  ↓
[Decision Agent (DeepSeek AI)]
  │  - Finální rozhodnutí pomocí AI
  │  - ATR-based risk management
  ↓
[Paper Trading Agent]
  │  - Executes simulated trade
  │  - Stores in SQLite database
  │  - Tracks performance
  ↓
END
```

## 📁 Struktura projektu

```
langtest/
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .env                   # Your configuration (create this)
├── run.sh / run.bat       # Run analysis
├── monitor.sh / monitor.bat  # Monitor trades (NEW!)
├── README.md
├── PLAN.md               # Implementation plan
├── results/              # Trading results (auto-created)
│   └── result_*.json    # Analysis results
├── data/                 # Database directory (auto-created)
│   └── paper_trades.db  # SQLite database with trades
├── logs/                 # Bot logs (auto-created)
│   ├── trading_bot.log     # Main log (10MB rotating)
│   ├── bot_detailed.log    # Detailed log (50MB rotating)
│   └── bot_errors.log      # Error log (5MB rotating)
└── src/
    ├── config.py         # Configuration management
    ├── main.py           # Main application & LangGraph workflow
    ├── trade_manager.py  # CLI for viewing/managing trades
    ├── monitor_trades.py # Trade monitoring automation
    ├── trading_bot.py    # Autonomous bot (all-in-one)
    ├── agents/
    │   ├── data_collector.py   # Data Collection Agent
    │   ├── analysis.py         # Analysis Agent
    │   ├── decision_maker.py   # Decision Agent (DeepSeek)
    │   └── paper_trading.py    # Paper Trading Agent
    ├── models/
    │   └── state.py           # State definition
    └── utils/
        ├── binance_client.py  # Binance API wrapper
        ├── indicators.py      # Technical indicators
        └── database.py        # SQLite database utilities
```

## 📋 Bot Logging

Bot automaticky loguje všechny akce do `logs/` složky:

### Log Files
- **`trading_bot.log`** - Main log (analyses, trades, closures)
- **`bot_detailed.log`** - Detailed debug log
- **`bot_errors.log`** - Errors only

### Viewing Logs
```bash
# Interactive menu
./view_logs.sh

# Direct commands
./view_logs.sh live        # Live tail main log
./view_logs.sh errors      # Live errors
./view_logs.sh analyses    # Show recent analyses
./view_logs.sh closures    # Show trade closures
./view_logs.sh wins        # Winning trades
./view_logs.sh losses      # Losing trades
./view_logs.sh stats       # Log statistics
```

### Log Format
```
2025-10-23 14:30:00 | INFO | ANALYSIS #15 STARTED
2025-10-23 14:30:05 | INFO | LONG signal: Entry $190.38, SL $185.20, TP $200.74
2025-10-23 14:30:06 | INFO | Paper trade created: SOLUSDT_20251023_143000
2025-10-25 18:45:23 | INFO | TRADE CLOSED: SOLUSDT_20251023_143000
2025-10-25 18:45:23 | INFO |   P&L: +$10.36 (+5.44%)
```

**Logs rotují automaticky** (10MB main log, 50MB detailed, 5MB errors)

## 💼 Paper Trading Management

Systém automaticky ukládá každý LONG/SHORT signál jako paper trade do SQLite databáze.

### ⚠️ Důležité: Trade Monitoring

**Trades se ukládají jako OPEN, ale musíte je monitorovat!**

```bash
# Start automated monitor (DOPORUČENO)
./monitor.sh --continuous

# Nebo nastavte cron job (kontrola každou hodinu)
crontab -e
# Přidejte: 0 * * * * cd /path/to/langtest && ./monitor.sh >> monitor.log 2>&1
```

Monitor automaticky:
- ✅ Kontroluje open trades
- ✅ Zavírá je když cena dosáhne SL/TP
- ✅ Počítá P&L
- ✅ Aktualizuje statistiky

**Bez monitoru trades zůstanou OPEN navždy!**

### Zobrazení trades

```bash
# List všech trades
cd src
python trade_manager.py list

# List pouze open trades
python trade_manager.py list --status open

# List pouze closed trades
python trade_manager.py list --status closed

# Show statistics
python trade_manager.py stats

# Statistics pro konkrétní symbol
python trade_manager.py stats --symbol SOLUSDT
```

### Manuální uzavření trade

```bash
# Uzavřít trade pokud máš důvod (např. manuální exit)
python trade_manager.py close --trade-id SOLUSDT_20251023_123456 --price 195.50
```

### Database Location

- **Path**: `data/paper_trades.db`
- **Format**: SQLite3
- **Accessible**: Libovolný SQLite browser/tool

## 🔑 DeepSeek API

Systém používá **DeepSeek AI** model pro finální trading rozhodnutí. 

- Model: `deepseek-chat`
- API je OpenAI-compatible
- Získejte API key na: [platform.deepseek.com](https://platform.deepseek.com)

## ⚠️ Důležité upozornění

**Tento systém je určen pouze pro vzdělávací a analytické účely.**

- ❌ Nejedná se o finanční poradenství
- ❌ Není určeno pro real trading bez důkladného testování
- ❌ Autor neručí za ztráty při použití systému
- ✅ Vždy proveďte vlastní analýzu před jakýmkoliv obchodem
- ✅ Použijte risk management

## 🛠️ Troubleshooting

### Import errors
Pokud máte problémy s importy, spusťte z `src/` složky:
```bash
cd src
python main.py
```

### API errors
- Zkontrolujte platnost DeepSeek API key v `.env`
- Pro Binance public data nejsou potřeba API keys
- Zkontrolujte internetové připojení

### Dependencies
Pokud máte problémy s instalací `ta-lib`:
```bash
# ta-lib je optional, systém používá 'ta' package, které je čistě Python
pip install ta
```

## 📝 Licence

MIT License - Volně použitelné pro vzdělávací účely.

## 🤝 Contributing

Contributions jsou vítány! Otevřete issue nebo pull request.

---

**Vytvořeno s ❤️ pomocí LangGraph a DeepSeek AI**
