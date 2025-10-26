# Quick Start Guide 🚀

Rychlý návod k spuštění Multi-Agent Trading System.

## 1️⃣ Instalace dependencies

```bash
# Vytvořte virtual environment
python3 -m venv venv

# Aktivujte virtual environment
source venv/bin/activate  # Linux/Mac
# nebo
venv\Scripts\activate  # Windows

# Nainstalujte dependencies
pip install -r requirements.txt
```

## 2️⃣ Konfigurace

```bash
# Vytvořte .env soubor
cp .env.example .env

# Editujte .env a přidejte váš DeepSeek API key
nano .env  # nebo použijte váš oblíbený editor
```

V souboru `.env` nastavte:
```env
DEEPSEEK_API_KEY=your_actual_api_key_here
```

**Získání DeepSeek API key:**
1. Jděte na https://platform.deepseek.com
2. Zaregistrujte se / přihlaste se
3. Vytvořte nový API key
4. Zkopírujte do `.env` souboru

## 3️⃣ Spuštění

### Varianta A: Pomocí run scriptu (doporučeno)

Linux/Mac:
```bash
./run.sh
```

Windows:
```bat
run.bat
```

### Varianta B: Přímé spuštění

```bash
cd src
python main.py
```

## 4️⃣ Co očekávat

Systém provede:

1. **Data Collection** 📊
   - Stáhne aktuální SOLUSDT data z Binance Futures
   - Získá 100 1h candlesticks
   - Získá funding rate

2. **Technical Analysis** 🔬
   - Vypočítá RSI, MACD, EMA
   - Vypočítá Bollinger Bands
   - Najde Support/Resistance levels
   - Analyzuje volume

3. **AI Decision** 🤖
   - Zavolá DeepSeek AI
   - Dostane doporučení: LONG/SHORT/NEUTRAL
   - S reasoning a confidence level

4. **Output** 💾
   - Zobrazí výsledek v terminálu
   - Uloží JSON soubor s detaily

## ⏱️ Časová náročnost

- První spuštění: ~10-30 sekund
  - Data collection: 2-5s
  - Analysis: 1-2s
  - AI decision: 5-15s
  
## 🔍 Troubleshooting

### "No module named 'X'"
```bash
pip install -r requirements.txt
```

### "DEEPSEEK_API_KEY is required"
Nastavte API key v `.env` souboru

### Import errors
Ujistěte se, že spouštíte z root složky nebo src/ složky:
```bash
cd /path/to/langtest
python src/main.py
```

### Binance API errors
- Public data nepotřebují API key
- Zkontrolujte internetové připojení
- Zkuste později (rate limits)

## 📊 Výstupní soubory

Každé spuštění vytvoří JSON soubor ve složce `results/`:
```
results/result_SOLUSDT_YYYYMMDD_HHMMSS.json
```

Složka `results/` se vytvoří automaticky při prvním spuštění.

Obsahuje:
- Trading recommendation
- All technical indicators
- Sentiment analysis
- Timestamp a current price

## 🎯 Next Steps

Po prvním úspěšném spuštění můžete:

1. **Upravit konfigurace** v `.env`:
   - Změnit symbol (např. BTCUSDT)
   - Změnit timeframe (4h, 1d)
   - Změnit počet candles

2. **Experimentovat s promptem**:
   - Upravte `src/agents/decision_maker.py`
   - Změňte prompt pro DeepSeek AI
   - Přidejte další faktory

3. **Přidat další indikátory**:
   - Rozšiřte `src/utils/indicators.py`
   - Přidejte do `src/agents/analysis.py`

4. **Automatizovat**:
   - Vytvořte cron job / scheduled task
   - Pravidelné spouštění analýzy
   - Logging výsledků

## 💡 Tip

Pro rychlé testování bez čekání:
```bash
# Spusťte s menším počtem candles
cd src
CANDLES_LIMIT=20 python main.py
```

---

**Hotovo! 🎉 Máte funkční multi-agent trading system!**

