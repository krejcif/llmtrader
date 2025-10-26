# Orderbook Analysis 📖

## Přehled

Orderbook analýza je klíčová součást systému, která poskytuje okamžitý pohled na reálnou supply/demand dynamiku na trhu.

## Co analyzujeme

### 1. **Bid/Ask Imbalance**
Poměr mezi objemem nákupních (bid) a prodejních (ask) orderů.

- **Bid Percentage**: % celkového objemu v buy orders
- **Ask Percentage**: % celkového objemu v sell orders
- **Ratio**: Poměr bid/ask (> 1 = více kupujících, < 1 = více prodávajících)

**Interpretace:**
- Ratio > 1.3: **Strong Buy Pressure** - silná poptávka
- Ratio 1.1-1.3: **Buy Pressure** - mírná poptávka
- Ratio 0.9-1.1: **Balanced** - vyrovnaný trh
- Ratio 0.7-0.9: **Sell Pressure** - mírný prodejní tlak
- Ratio < 0.7: **Strong Sell Pressure** - silný prodejní tlak

### 2. **Order Depth**
Analýza objemu na různých cenových úrovních.

Měříme objem v:
- **0.5%** od aktuální ceny (okamžitá likvidita)
- **1.0%** od aktuální ceny (blízká likvidita)
- **2.0%** od aktuální ceny (širší trh)

**Význam:**
- Vysoký depth = silná podpora/rezistence
- Nízký depth = slabá úroveň, snadný průraz

### 3. **Large Orders (Walls)**
Detekce velkých orderů (3x větší než průměr).

**Bid Walls** (velké buy orders):
- Ukazují silnou podporu
- Mohou bránit poklesu ceny
- Bullish signál

**Ask Walls** (velké sell orders):
- Ukazují silnou rezistenci
- Mohou bránit růstu ceny
- Bearish signál

**Pozor:** Walls mohou být fake a zmizet (spoofing)

### 4. **Spread Analysis**
Rozdíl mezi best bid a best ask.

- **Tight spread** (< 0.05%): Vysoká likvidita, zdravý trh
- **Normal spread** (0.05-0.1%): Standardní podmínky
- **Wide spread** (> 0.1%): Nízká likvidita, volatilní podmínky

## Jak to používáme

### V Analysis Agentu
```python
orderbook_analysis = analyze_orderbook(
    market_data['orderbook'],
    market_data['current_price']
)
```

Výstup:
```python
{
    "imbalance": {
        "bid_percentage": 52.3,
        "ask_percentage": 47.7,
        "ratio": 1.10,
        "pressure": "buy"
    },
    "depth": {
        "bid_volumes": {"0.5%": 1234.5, "1.0%": 2456.8, "2.0%": 4321.0},
        "ask_volumes": {"0.5%": 1123.4, "1.0%": 2234.5, "2.0%": 3987.6}
    },
    "spread": {
        "absolute": 0.05,
        "percentage": 0.0345
    },
    "walls": {
        "bid_walls": [{"price": 144.50, "size": 5678.9}],
        "ask_walls": [{"price": 146.20, "size": 4321.0}],
        "has_significant_walls": true
    }
}
```

### V DeepSeek Prompt
Orderbook data jsou součástí promptu:
```
ORDERBOOK ANALÝZA:
- Bid/Ask Imbalance: 52.3% / 47.7% (ratio: 1.10)
- Pressure: buy
- Spread: 0.0345%
- Large orders (walls): Ano
```

## Trading Signály

### Bullish Signály
✅ Bid percentage > 55%  
✅ Strong buy pressure (ratio > 1.3)  
✅ Bid walls přítomny  
✅ Tight spread  

### Bearish Signály
❌ Ask percentage > 55%  
❌ Strong sell pressure (ratio < 0.7)  
❌ Ask walls přítomny  
❌ Wide spread  

### Neutral/Mixed
⚠️ Balanced ratio (0.9-1.1)  
⚠️ Walls na obou stranách  
⚠️ Normal spread  

## Kombinace s Technical Indicators

Orderbook analýza je nejsilnější v kombinaci s technickými indikátory:

**Bullish Confluence:**
- MACD bullish crossover
- RSI < 70 (ne překoupeno)
- **Buy pressure v orderbooku**
- **Bid walls pod cenou**

**Bearish Confluence:**
- MACD bearish crossover
- RSI > 30 (ne překoupeno)
- **Sell pressure v orderbooku**
- **Ask walls nad cenou**

## Limitace

1. **Spoofing**: Velké ordery mohou být fake a zmizí
2. **High Frequency**: Orderbook se mění velmi rychle
3. **Snapshot**: Vidíme pouze momentální stav
4. **Market Orders**: Nevidíme incoming market orders

## Best Practices

✅ Kombinuj s technickými indikátory  
✅ Sleduj trend imbalance (ne jen jeden snapshot)  
✅ Dávej pozor na abnormální walls  
✅ Porovnávej s historical patterns  
✅ Používej jako confirmation, ne main signal  

## Příklad Interpretace

```
Scenario: SOLUSDT @ $145.32

Orderbook:
- Bid/Ask: 58.2% / 41.8%
- Ratio: 1.39
- Pressure: strong_buy
- Bid wall @ $144.50 (5000 SOL)
- Spread: 0.028%

Technical:
- RSI: 62 (neutral)
- MACD: bullish crossover
- EMA: bullish trend

Sentiment:
- Funding: neutral
- Volume: increasing

Interpretation:
🟢 BULLISH CONFLUENCE
- Silná buying pressure v orderbooku (58%)
- Bid wall poskytuje podporu
- Technické indikátory potvrzují uptrend
- Tight spread = dobrá likvidita

Recommendation: LONG s vysokou confidence
```

---

**Orderbook analýza poskytuje real-time pohled na market microstructure a je kritická pro přesné trading rozhodnutí.**

