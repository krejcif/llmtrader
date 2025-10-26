# Implementační plán - Multi-Agent Trading System

## Přehled projektu
Vytvoření MVP multi-agent systému pomocí LangGraph pro analýzu Binance futures SOLUSDT a poskytování trading doporučení (short/long/neutral) s využitím DeepSeek AI.

## Technologický stack

### Hlavní technologie
- **LangGraph** - orchestrace multi-agent systému (state machine, workflow)
- **DeepSeek AI** - AI model pro finální trading rozhodování
- **Binance Futures API** - získávání market dat (SOLUSDT)
- **Python 3.10+** - hlavní programovací jazyk

### Pomocné knihovny
- `python-binance` - Binance API wrapper
- `pandas` - zpracování dat
- `ta` - technické indikátory (jednodušší než ta-lib)
- `openai` - DeepSeek API client (OpenAI-compatible)
- `python-dotenv` - správa konfigurace

## Architektura systému

### Multi-Agent Structure

#### 1. **Data Collector Agent**
- **Odpovědnost**: Získávání dat z Binance futures API
- **Výstupy**:
  - Aktuální cena SOLUSDT
  - Historická data (candlesticks, 1h timeframe, 100 candles)
  - Volume data
  - Funding rate

#### 2. **Analysis Agent**
- **Odpovědnost**: Výpočet technických indikátorů a sentiment analýza
- **Indikátory**:
  - RSI (14 period)
  - MACD (12, 26, 9)
  - EMA 20/50 (trend direction)
  - Bollinger Bands
  - Support/Resistance levels
  - Volume trend
- **Sentiment**:
  - Funding rate sentiment (bullish/bearish/neutral)
  - Volume momentum
- **Výstup**: Strukturovaná data s indikátory a jejich interpretací

#### 3. **Decision Agent (DeepSeek AI)**
- **Odpovědnost**: Finální rozhodnutí pomocí DeepSeek AI modelu
- **Vstupy**:
  - Aktuální market data
  - Technické indikátory s interpretací
  - Sentiment indikace
- **Výstup**: Doporučení (LONG/SHORT/NEUTRAL) s reasoning a confidence
- **Model**: DeepSeek Chat (přes OpenAI-compatible API)

### LangGraph State Machine

```
START
  ↓
[Data Collector Agent]
  ↓
[Analysis Agent]
  ↓
[Decision Agent (DeepSeek)]
  ↓
END
```

**Poznámka**: LangGraph samotný zajišťuje orchestraci a state management. Nepotřebujeme samostatný Coordinator Agent pro MVP.

## Implementační kroky

### Fáze 1: Příprava prostředí (1-2 hodiny)

1. **Struktura projektu**
   ```
   langtest/
   ├── .env.example
   ├── .env
   ├── requirements.txt
   ├── README.md
   ├── PLAN.md
   └── src/
       ├── __init__.py
       ├── main.py
       ├── config.py
       ├── agents/
       │   ├── __init__.py
       │   ├── data_collector.py
       │   ├── analysis.py
       │   └── decision_maker.py
       ├── models/
       │   ├── __init__.py
       │   └── state.py
       └── utils/
           ├── __init__.py
           ├── binance_client.py
           └── indicators.py
   ```

2. **Instalace závislostí**
   - Vytvoření virtual environment
   - Instalace balíčků: langgraph, langchain, python-binance, pandas, ta, numpy

3. **Konfigurace**
   - Binance API keys (read-only testnet)
   - DeepSeek API key
   - Environment variables setup

### Fáze 2: Binance API integrace (2-3 hodiny)

1. **Implementace Binance client** (`utils/binance_client.py`)
   - Připojení k Binance Futures API
   - Funkce pro získání:
     - Aktuální ceny SOLUSDT
     - OHLCV data (1h timeframe, 100 candles)
     - Volume data
     - Funding rate

2. **Testování API spojení**
   - Verify API credentials (může být prázdné pro public data)
   - Test data retrieval
   - Error handling

### Fáze 3: Technical indicators utility (2 hodiny)

1. **Implementace indicators** (`utils/indicators.py`)
   - RSI calculation
   - MACD calculation
   - EMA calculation
   - Bollinger Bands calculation (20 period, 2 std dev)
   - Support/Resistance detection (lokální minima/maxima, swing points)
   - Volume analysis functions
   - Pomocné funkce pro interpretaci hodnot

### Fáze 4: Implementace agentů (5-8 hodin)

#### 4.1 Data Collector Agent (1 hodina)
- Implementace `agents/data_collector.py`
- Funkce:
  - `collect_market_data(state)` - stažení market dat pomocí Binance client
  - Validace dat
  - Error handling
- Output: Aktualizovaný state s market daty

#### 4.2 Analysis Agent (3-4 hodiny)
- Implementace `agents/analysis.py`
- Výpočet indikátorů (pomocí `utils/indicators.py`):
  - RSI (14 period)
  - MACD (12, 26, 9)
  - EMA (20, 50)
  - Bollinger Bands (20, 2)
  - Support/Resistance levels (local extremes)
  - Volume trend
- Sentiment analýza:
  - Funding rate interpretation
  - Volume momentum
- Interpretace všech hodnot
- Output: Aktualizovaný state s analýzou

#### 4.3 Decision Agent (1-2 hodiny)
- Implementace `agents/decision_maker.py`
- Integrace s **DeepSeek AI** (přes OpenAI-compatible API)
- Setup: `OpenAI(base_url="https://api.deepseek.com", api_key=...)`
- Model: `deepseek-chat`
- Prompt engineering pro správné rozhodování
- Parsování a validace AI odpovědi (JSON format)
- Output: Aktualizovaný state s finálním doporučením

### Fáze 5: LangGraph State Machine (2-3 hodiny)

1. **State Model** (`models/state.py`)
   ```python
   class TradingState(TypedDict):
       symbol: str
       market_data: dict | None
       analysis: dict | None
       recommendation: dict | None
       error: str | None
   ```

2. **Graph Construction** (`main.py`)
   - Definice nodes (3 agenty)
   - Definice edges (lineární flow: data -> analysis -> decision)
   - Error handling v každém node
   - Compile graph

3. **Integration**
   - Propojení všech agentů do graph
   - Initial state setup
   - Testing celého flow s print statements

### Fáze 6: Testování a ladění (1-2 hodiny)

1. **Manual testing s reálnými daty**
   - Spuštění celého workflow
   - Kontrola každého kroku (print outputs)
   - Validace logiky rozhodování

2. **Edge cases**
   - API failure handling
   - Invalid data handling
   - Timeout scenarios

3. **Fine-tuning**
   - Úprava promptu pro DeepSeek podle výstupů
   - Optimalizace interpretací indikátorů
   - Performance check

### Fáze 7: Dokumentace a finalizace (1 hodina)

1. **README.md update**
   - Installation guide
   - Quick start
   - Configuration guide (DeepSeek API key)
   - Usage example

2. **Code cleanup**
   - Základní docstrings
   - Type hints
   - Remove debug prints

3. **Sample output**
   - Uložit příklad výstupu do README

## Datové modely

### Market Data Structure
```python
{
    "symbol": "SOLUSDT",
    "current_price": 145.32,
    "timestamp": "2025-10-23T10:00:00Z",
    "candles": [...],  # pandas DataFrame se sloupci: timestamp, open, high, low, close, volume
    "funding_rate": 0.0001
}
```

### Analysis Structure
```python
{
    "indicators": {
        "rsi": {
            "value": 65.4,
            "signal": "neutral"  # oversold/neutral/overbought
        },
        "macd": {
            "macd": 2.34,
            "signal_line": 1.98,
            "histogram": 0.36,
            "signal": "bullish"  # bullish/bearish/neutral
        },
        "ema": {
            "ema_20": 143.5,
            "ema_50": 140.2,
            "trend": "bullish"  # bullish/bearish/neutral
        },
        "bollinger_bands": {
            "upper": 148.5,
            "middle": 145.0,
            "lower": 141.5,
            "position": "middle",  # upper/middle/lower/above/below
            "squeeze": False
        },
        "support_resistance": {
            "nearest_resistance": 150.0,
            "nearest_support": 140.0,
            "current_price": 145.32,
            "position": "middle"  # near_support/near_resistance/middle
        },
        "volume": {
            "current_vs_avg": 1.25,
            "trend": "increasing"  # increasing/decreasing/stable
        }
    },
    "sentiment": {
        "funding_rate": 0.0001,
        "funding_sentiment": "neutral",  # bullish/bearish/neutral
        "volume_momentum": "positive"
    },
    "summary": "Technicky bullish s neutrálním sentimentem. RSI v healthy zóně, MACD bullish crossover."
}
```

### Recommendation Structure (zjednodušeno pro MVP)
```python
{
    "action": "LONG",  # LONG/SHORT/NEUTRAL
    "confidence": "high",  # low/medium/high
    "reasoning": "Detailní vysvětlení rozhodnutí založené na technických indikátorech a sentimentu.",
    "key_factors": [
        "MACD bullish crossover indikuje momentum",
        "RSI v healthy zóně (ne překoupeno)",
        "EMA trend je bullish"
    ]
}
```

## Konfigurace (.env)

```env
# DeepSeek API (REQUIRED)
DEEPSEEK_API_KEY=your_deepseek_api_key

# Trading Configuration
SYMBOL=SOLUSDT
TIMEFRAME=1h
CANDLES_LIMIT=100

# Optional: Binance API (ne nutné pro public data)
# BINANCE_API_KEY=
# BINANCE_API_SECRET=
```

**Poznámka**: Pro získání public market dat z Binance není nutné API key. API key je potřeba pouze pro private data nebo trading.

## Requirements.txt

```
langgraph>=0.2.0
langchain-core>=0.3.0
openai>=1.0.0
python-binance>=1.0.19
pandas>=2.0.0
ta>=0.11.0
python-dotenv>=1.0.0
```

**Poznámka**: DeepSeek má OpenAI-compatible API, takže použijeme `openai` package s custom base URL.

## Prompt Templates

### Decision Agent Prompt
```
Jsi expert na trading analýzu kryptoměn. Na základě poskytnutých technických indikátorů a market sentimentu rozhodneš o trading doporučení pro {symbol}.

AKTUÁLNÍ CENA: {current_price} USDT

ANALÝZA:
{analysis_summary}

TECHNICKÉ INDIKÁTORY:
- RSI: {rsi_value} ({rsi_signal})
- MACD: {macd_signal}
- EMA Trend: {ema_trend}
- Bollinger Bands: {bb_position}
- Support/Resistance: {sr_position}
- Volume: {volume_trend}

SENTIMENT:
- Funding rate: {funding_sentiment}
- Volume momentum: {volume_momentum}

Na základě těchto dat rozhodneš:
1. Action: LONG (bullish), SHORT (bearish), nebo NEUTRAL (žádný jasný signál)
2. Confidence: low/medium/high
3. Reasoning: Stručné vysvětlení (2-3 věty)
4. Key factors: 3 hlavní důvody pro rozhodnutí

Odpověz POUZE v tomto JSON formátu:
{{
  "action": "LONG",
  "confidence": "high",
  "reasoning": "...",
  "key_factors": ["factor1", "factor2", "factor3"]
}}
```

## Rizika a jejich mitigace

### 1. API Rate Limits
- **Riziko**: Překročení rate limitů Binance API
- **Mitigace**: 
  - Implementace rate limiting
  - Caching dat
  - Optimalizace requests

### 2. API Errors
- **Riziko**: Výpadky API nebo chyby
- **Mitigace**:
  - Retry logic s exponential backoff
  - Fallback mechanismy
  - Comprehensive error handling

### 3. Data Quality
- **Riziko**: Neúplná nebo chybná data
- **Mitigace**:
  - Data validation
  - Sanity checks
  - Logging problematických dat

### 4. AI Model Reliability
- **Riziko**: Nespolehlivé nebo nekonzistentní AI odpovědi
- **Mitigace**:
  - Kvalitní prompt engineering s jasnou strukturou
  - JSON response validation
  - Retry s better error message pokud JSON parsing selže

## Testovací scénáře

### 1. Bullish Scenario
- Silný uptrend
- Pozitivní technické indikátory
- Vysoký volume
- Očekávaný výstup: LONG s vysokou confidence

### 2. Bearish Scenario
- Downtrend
- Negativní indikátory
- Negativní funding rate
- Očekávaný výstup: SHORT s vysokou confidence

### 3. Neutral/Uncertain Scenario
- Mixed signals
- Low volume
- Ranging market
- Očekávaný výstup: NEUTRAL

### 4. Error Handling
- API failures
- Invalid data
- Timeout scenarios

## Metriky úspěšnosti MVP

1. **Funkčnost**
   - ✅ Úspěšné získání dat z Binance
   - ✅ Výpočet všech plánovaných indikátorů
   - ✅ Funkční komunikace s DeepSeek
   - ✅ Kompletní workflow bez chyb

2. **Kvalita výstupu**
   - ✅ Strukturovaný a čitelný output
   - ✅ Konzistentní rozhodování
   - ✅ Smysluplné reasoning

3. **Performance**
   - ✅ Celková analýza pod 30 sekund
   - ✅ Úspěšnost API calls > 95%

## Budoucí rozšíření (mimo MVP)

1. **Enhanced Analysis**
   - Order book analysis
   - On-chain metrics
   - Social media sentiment

2. **Multiple Timeframes**
   - Multi-timeframe analysis
   - Timeframe confluence

3. **Backtesting**
   - Historical performance testing
   - Strategy optimization

4. **Real Trading Integration**
   - Automated order placement
   - Portfolio management
   - Risk management

5. **Web Interface**
   - Dashboard pro vizualizaci
   - Real-time updates
   - Historical tracking

6. **Multiple Assets**
   - Support pro více trading párů
   - Cross-asset analysis
   - Portfolio recommendations

## Časový odhad

- **Celkový čas na MVP**: 14-18 hodin práce
- **Rozložení**:
  - Setup a příprava: 1-2 hodiny
  - Binance API integrace: 2-3 hodiny
  - Technical indicators: 2 hodiny (včetně BB a S/R)
  - Implementace agentů: 5-8 hodin
  - LangGraph integrace: 2-3 hodiny
  - Testování a ladění: 1-2 hodiny
  - Dokumentace: 1 hodina

## Závěr

Tento plán poskytuje strukturovaný přístup k vytvoření **MVP** multi-agent trading systému. Klíčové principy:

1. **Jednoduchost**: 3 agenty (data -> analysis -> decision), lineární flow
2. **Fokus na MVP**: Komplexní technické indikátory (RSI, MACD, EMA, Bollinger Bands, Support/Resistance)
3. **Modularita**: Každý agent má jasnou odpovědnost a může být testován samostatně
4. **AI-powered rozhodování**: **DeepSeek AI** dělá finální rozhodnutí na základě strukturované analýzy

**MVP output**: Systém vezme aktuální SOLUSDT data z Binance Futures, spočítá technické indikátory včetně Bollinger Bands a Support/Resistance levels, a pomocí **DeepSeek AI modelu** poskytne trading doporučení (LONG/SHORT/NEUTRAL) s reasoning. Celý proces pod 30 sekund.

**Není v MVP** (budoucí rozšíření):
- Entry/stop-loss/take-profit automatika
- Backtesting
- Multiple timeframes
- Web interface
- Real trading execution

