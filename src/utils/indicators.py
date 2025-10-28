"""Technical indicators calculation utilities"""
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands
from typing import Dict, List, Tuple


def calculate_rsi(df: pd.DataFrame, period: int = 14, return_series: bool = False) -> Dict:
    """
    Calculate RSI indicator
    
    Args:
        df: DataFrame with 'close' column
        period: RSI period (default 14)
        
    Returns:
        Dictionary with RSI value and signal
    """
    rsi = RSIIndicator(close=df['close'], window=period)
    rsi_series = rsi.rsi()
    rsi_value = rsi_series.iloc[-1]
    
    # Determine signal
    if rsi_value < 30:
        signal = "oversold"
    elif rsi_value > 70:
        signal = "overbought"
    else:
        signal = "neutral"
    
    # Detect RSI turning (for reversal detection)
    turning = "none"
    if len(rsi_series) >= 3:
        rsi_3 = rsi_series.iloc[-3]
        rsi_2 = rsi_series.iloc[-2]
        rsi_1 = rsi_series.iloc[-1]
        
        # Turning up (bullish reversal)
        if rsi_3 > rsi_2 and rsi_1 > rsi_2 and rsi_1 > rsi_3:
            turning = "turning_up"
        # Turning down (bearish reversal)
        elif rsi_3 < rsi_2 and rsi_1 < rsi_2 and rsi_1 < rsi_3:
            turning = "turning_down"
    
    if return_series:
        return rsi_series
    
    return {
        "value": round(rsi_value, 2),
        "signal": signal,
        "turning": turning
    }


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """
    Calculate MACD indicator
    
    Args:
        df: DataFrame with 'close' column
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
        
    Returns:
        Dictionary with MACD values and signal
    """
    macd = MACD(close=df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
    
    macd_line = macd.macd().iloc[-1]
    signal_line = macd.macd_signal().iloc[-1]
    histogram = macd.macd_diff().iloc[-1]
    
    # Determine signal based on histogram and crossover
    if histogram > 0:
        macd_signal = "bullish"
    elif histogram < 0:
        macd_signal = "bearish"
    else:
        macd_signal = "neutral"
    
    return {
        "macd": round(macd_line, 4),
        "signal_line": round(signal_line, 4),
        "histogram": round(histogram, 4),
        "signal": macd_signal
    }


def calculate_ema(df: pd.DataFrame, periods: List[int] = [20, 50]) -> Dict:
    """
    Calculate EMA indicators
    
    Args:
        df: DataFrame with 'close' column
        periods: List of EMA periods
        
    Returns:
        Dictionary with EMA values and trend
    """
    result = {}
    
    for period in periods:
        ema = EMAIndicator(close=df['close'], window=period)
        result[f"ema_{period}"] = round(ema.ema_indicator().iloc[-1], 2)
    
    # Determine trend
    if len(periods) >= 2:
        short_ema = result[f"ema_{periods[0]}"]
        long_ema = result[f"ema_{periods[1]}"]
        
        if short_ema > long_ema:
            result["trend"] = "bullish"
        elif short_ema < long_ema:
            result["trend"] = "bearish"
        else:
            result["trend"] = "neutral"
    
    return result


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict:
    """
    Calculate Bollinger Bands
    
    Args:
        df: DataFrame with 'close' column
        period: Moving average period
        std_dev: Standard deviation multiplier
        
    Returns:
        Dictionary with BB values and position
    """
    bb = BollingerBands(close=df['close'], window=period, window_dev=std_dev)
    
    upper = bb.bollinger_hband().iloc[-1]
    middle = bb.bollinger_mavg().iloc[-1]
    lower = bb.bollinger_lband().iloc[-1]
    current_price = df['close'].iloc[-1]
    
    # Determine position
    band_width = upper - lower
    upper_threshold = middle + (band_width * 0.4)
    lower_threshold = middle - (band_width * 0.4)
    
    if current_price > upper:
        position = "above"
    elif current_price >= upper_threshold:
        position = "upper"
    elif current_price <= lower_threshold:
        position = "lower"
    elif current_price < lower:
        position = "below"
    else:
        position = "middle"
    
    # Check for squeeze (low volatility)
    avg_band_width = (df['close'].rolling(window=20).std() * 2 * 2).mean()
    squeeze = band_width < avg_band_width * 0.5
    
    return {
        "upper": round(upper, 2),
        "middle": round(middle, 2),
        "lower": round(lower, 2),
        "position": position,
        "squeeze": bool(squeeze)
    }


def find_support_resistance(df: pd.DataFrame, window: int = 10) -> Dict:
    """
    Find support and resistance levels using swing highs and lows
    
    Args:
        df: DataFrame with 'high' and 'low' columns
        window: Window for finding local extremes
        
    Returns:
        Dictionary with support/resistance levels
    """
    # Find local maxima (resistance)
    highs = df['high'].values
    resistance_levels = []
    
    for i in range(window, len(highs) - window):
        if highs[i] == max(highs[i-window:i+window+1]):
            resistance_levels.append(highs[i])
    
    # Find local minima (support)
    lows = df['low'].values
    support_levels = []
    
    for i in range(window, len(lows) - window):
        if lows[i] == min(lows[i-window:i+window+1]):
            support_levels.append(lows[i])
    
    current_price = df['close'].iloc[-1]
    
    # Find nearest levels
    resistance_above = [r for r in resistance_levels if r > current_price]
    support_below = [s for s in support_levels if s < current_price]
    
    nearest_resistance = min(resistance_above) if resistance_above else current_price * 1.05
    nearest_support = max(support_below) if support_below else current_price * 0.95
    
    # Determine position
    resistance_distance = nearest_resistance - current_price
    support_distance = current_price - nearest_support
    
    if support_distance < resistance_distance * 0.5:
        position = "near_support"
    elif resistance_distance < support_distance * 0.5:
        position = "near_resistance"
    else:
        position = "middle"
    
    return {
        "nearest_resistance": round(nearest_resistance, 2),
        "nearest_support": round(nearest_support, 2),
        "current_price": round(current_price, 2),
        "position": position
    }


def calculate_volume_analysis(df: pd.DataFrame, period: int = 20) -> Dict:
    """
    Analyze volume trends
    
    Args:
        df: DataFrame with 'volume' column
        period: Period for volume moving average
        
    Returns:
        Dictionary with volume analysis
    """
    current_volume = df['volume'].iloc[-1]
    avg_volume = df['volume'].rolling(window=period).mean().iloc[-1]
    
    current_vs_avg = current_volume / avg_volume if avg_volume > 0 else 1.0
    
    # Determine trend
    recent_volumes = df['volume'].tail(5).values
    if len(recent_volumes) >= 3:
        if recent_volumes[-1] > recent_volumes[-2] > recent_volumes[-3]:
            trend = "increasing"
        elif recent_volumes[-1] < recent_volumes[-2] < recent_volumes[-3]:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    return {
        "current_vs_avg": round(current_vs_avg, 2),
        "trend": trend
    }


def analyze_orderbook(orderbook: Dict, current_price: float) -> Dict:
    """
    Analyze orderbook for buying/selling pressure
    
    Args:
        orderbook: Dictionary with bids and asks [[price, qty], ...]
        current_price: Current market price
        
    Returns:
        Dictionary with orderbook analysis
    """
    bids = orderbook['bids']  # Buy orders
    asks = orderbook['asks']  # Sell orders
    
    # Calculate total volume at different depths
    def calculate_depth_volume(orders, depth_levels=[0.5, 1.0, 2.0]):
        """Calculate volume within percentage depth"""
        volumes = {}
        for depth_pct in depth_levels:
            volume = 0
            for price, qty in orders:
                price_diff_pct = abs((price - current_price) / current_price * 100)
                if price_diff_pct <= depth_pct:
                    volume += qty
            volumes[f"{depth_pct}%"] = volume
        return volumes
    
    bid_volumes = calculate_depth_volume(bids)
    ask_volumes = calculate_depth_volume(asks)
    
    # Calculate bid/ask imbalance
    total_bid_volume = sum(qty for _, qty in bids[:20])  # Top 20 levels
    total_ask_volume = sum(qty for _, qty in asks[:20])
    
    total_volume = total_bid_volume + total_ask_volume
    if total_volume > 0:
        bid_percentage = (total_bid_volume / total_volume) * 100
        ask_percentage = (total_ask_volume / total_volume) * 100
        imbalance_ratio = total_bid_volume / total_ask_volume if total_ask_volume > 0 else 0
    else:
        bid_percentage = 50
        ask_percentage = 50
        imbalance_ratio = 1.0
    
    # Determine pressure signal
    if imbalance_ratio > 1.3:  # 30% more buying
        pressure = "strong_buy"
    elif imbalance_ratio > 1.1:
        pressure = "buy"
    elif imbalance_ratio < 0.7:  # 30% more selling
        pressure = "strong_sell"
    elif imbalance_ratio < 0.9:
        pressure = "sell"
    else:
        pressure = "balanced"
    
    # Calculate spread
    best_bid = bids[0][0] if bids else current_price
    best_ask = asks[0][0] if asks else current_price
    spread = best_ask - best_bid
    spread_pct = (spread / current_price) * 100 if current_price > 0 else 0
    
    # Find large orders (walls)
    avg_bid_size = np.mean([qty for _, qty in bids[:20]]) if bids else 0
    avg_ask_size = np.mean([qty for _, qty in asks[:20]]) if asks else 0
    
    bid_walls = []
    ask_walls = []
    
    for price, qty in bids[:20]:
        if qty > avg_bid_size * 3:  # 3x average = wall
            bid_walls.append({"price": round(price, 2), "size": round(qty, 2)})
    
    for price, qty in asks[:20]:
        if qty > avg_ask_size * 3:
            ask_walls.append({"price": round(price, 2), "size": round(qty, 2)})
    
    return {
        "imbalance": {
            "bid_percentage": round(bid_percentage, 2),
            "ask_percentage": round(ask_percentage, 2),
            "ratio": round(imbalance_ratio, 2),
            "pressure": pressure
        },
        "depth": {
            "bid_volumes": {k: round(v, 2) for k, v in bid_volumes.items()},
            "ask_volumes": {k: round(v, 2) for k, v in ask_volumes.items()}
        },
        "spread": {
            "absolute": round(spread, 2),
            "percentage": round(spread_pct, 4)
        },
        "walls": {
            "bid_walls": bid_walls[:3],  # Top 3 walls
            "ask_walls": ask_walls[:3],
            "has_significant_walls": len(bid_walls) > 0 or len(ask_walls) > 0
        }
    }


def calculate_atr(df: pd.DataFrame, period: int = 14) -> Dict:
    """
    Calculate Average True Range (ATR) for volatility-based stops
    
    Args:
        df: DataFrame with high, low, close columns
        period: ATR period (default 14)
        
    Returns:
        Dictionary with ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range calculation
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    current_atr = atr.iloc[-1]
    current_price = close.iloc[-1]
    
    # ATR as percentage of price
    atr_percentage = (current_atr / current_price) * 100
    
    return {
        "value": round(current_atr, 2),
        "percentage": round(atr_percentage, 2),
        "current_price": round(current_price, 2)
    }


def calculate_stop_take_profit(df: pd.DataFrame, direction: str, 
                                atr_multiplier_stop: float = 1.0, 
                                atr_multiplier_tp: float = 2.0,
                                max_stop_pct: float = 1.5,
                                max_tp_pct: float = 3.0) -> Dict:
    """
    Calculate hybrid stop loss and take profit (ATR + % cap for intraday)
    
    Args:
        df: DataFrame with OHLCV data
        direction: 'bullish' or 'bearish'
        atr_multiplier_stop: ATR multiplier for stop loss (default 1.0 for intraday)
        atr_multiplier_tp: ATR multiplier for take profit (default 2.0 for intraday)
        max_stop_pct: Maximum stop loss % (default 1.5% cap for intraday)
        max_tp_pct: Maximum take profit % (default 3.0% cap for intraday)
        
    Returns:
        Dictionary with stop loss and take profit levels
    """
    atr_data = calculate_atr(df)
    current_price = atr_data['current_price']
    atr = atr_data['value']
    
    if direction == 'bullish':
        # Long position - ATR-based
        atr_stop_loss = current_price - (atr * atr_multiplier_stop)
        atr_take_profit = current_price + (atr * atr_multiplier_tp)
        
        # Fixed %-based (caps)
        pct_stop_loss = current_price * (1 - max_stop_pct / 100)
        pct_take_profit = current_price * (1 + max_tp_pct / 100)
        
        # HYBRID: Use tighter of the two (safer for intraday)
        stop_loss = max(atr_stop_loss, pct_stop_loss)  # Tighter stop
        take_profit = min(atr_take_profit, pct_take_profit)  # Closer target
        
        risk = current_price - stop_loss
        reward = take_profit - current_price
    else:
        # Short position
        atr_stop_loss = current_price + (atr * atr_multiplier_stop)
        atr_take_profit = current_price - (atr * atr_multiplier_tp)
        
        pct_stop_loss = current_price * (1 + max_stop_pct / 100)
        pct_take_profit = current_price * (1 - max_tp_pct / 100)
        
        # HYBRID: Tighter of two
        stop_loss = min(atr_stop_loss, pct_stop_loss)  # Tighter stop
        take_profit = max(atr_take_profit, pct_take_profit)  # Closer target
        
        risk = stop_loss - current_price
        reward = current_price - take_profit
    
    risk_reward_ratio = reward / risk if risk > 0 else 0
    
    # Calculate position size for 1% risk (example with $10,000 account)
    account_size = 10000  # Example
    risk_percentage = 0.01  # 1% risk
    risk_amount = account_size * risk_percentage
    position_size = risk_amount / abs(risk) if risk > 0 else 0
    
    # Check which method was used
    if direction == 'bullish':
        stop_method = 'ATR' if stop_loss == atr_stop_loss else '% Cap'
        tp_method = 'ATR' if take_profit == atr_take_profit else '% Cap'
    else:
        stop_method = 'ATR' if stop_loss == atr_stop_loss else '% Cap'
        tp_method = 'ATR' if take_profit == atr_take_profit else '% Cap'
    
    # Use more precision for crypto with low prices (DOGE, etc.)
    precision = 6 if current_price < 1 else 2
    
    return {
        "entry": round(current_price, precision),
        "stop_loss": round(stop_loss, precision),
        "take_profit": round(take_profit, precision),
        "risk_amount": round(abs(risk), precision),
        "reward_amount": round(reward, precision),
        "risk_reward_ratio": round(risk_reward_ratio, 2),
        "atr": round(atr, precision),
        "atr_percentage": atr_data['percentage'],
        "stop_distance_percentage": round((abs(risk) / current_price) * 100, 2),
        "tp_distance_percentage": round((reward / current_price) * 100, 2),
        "stop_method": stop_method,
        "tp_method": tp_method
    }


def detect_trend_pattern(df: pd.DataFrame, lookback: int = 20) -> Dict:
    """
    Detect trend patterns (Higher Highs/Lows, Lower Highs/Lows)
    
    Args:
        df: DataFrame with OHLCV data
        lookback: Period for pattern detection
        
    Returns:
        Dictionary with trend pattern information
    """
    # Get recent highs and lows
    recent_data = df.tail(lookback)
    
    # Find swing points
    highs = recent_data['high'].values
    lows = recent_data['low'].values
    
    # Identify swing highs (local maxima)
    swing_highs = []
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swing_highs.append(highs[i])
    
    # Identify swing lows (local minima)
    swing_lows = []
    for i in range(2, len(lows) - 2):
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swing_lows.append(lows[i])
    
    # Determine pattern
    pattern = "unclear"
    trend_direction = "neutral"
    
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        # Check for Higher Highs and Higher Lows (uptrend)
        higher_highs = swing_highs[-1] > swing_highs[-2] if len(swing_highs) >= 2 else False
        higher_lows = swing_lows[-1] > swing_lows[-2] if len(swing_lows) >= 2 else False
        
        # Check for Lower Highs and Lower Lows (downtrend)
        lower_highs = swing_highs[-1] < swing_highs[-2] if len(swing_highs) >= 2 else False
        lower_lows = swing_lows[-1] < swing_lows[-2] if len(swing_lows) >= 2 else False
        
        if higher_highs and higher_lows:
            pattern = "higher_highs_lows"
            trend_direction = "bullish"
        elif lower_highs and lower_lows:
            pattern = "lower_highs_lows"
            trend_direction = "bearish"
        elif higher_highs and not higher_lows:
            pattern = "higher_highs_only"
            trend_direction = "weakening_bearish"
        elif lower_lows and not lower_highs:
            pattern = "lower_lows_only"
            trend_direction = "weakening_bullish"
        elif higher_lows and lower_highs:
            pattern = "converging"
            trend_direction = "consolidating"
    
    return {
        "pattern": pattern,
        "trend_direction": trend_direction,
        "swing_highs_count": len(swing_highs),
        "swing_lows_count": len(swing_lows),
        "last_swing_high": round(swing_highs[-1], 2) if swing_highs else None,
        "last_swing_low": round(swing_lows[-1], 2) if swing_lows else None
    }


def detect_trend_reversal(indicators_current: Dict, indicators_previous: Dict, 
                         current_price: float) -> Dict:
    """
    Detect trend reversal with multi-factor confirmation
    
    Args:
        indicators_current: Current timeframe indicators
        indicators_previous: Previous/higher timeframe indicators
        current_price: Current market price
        
    Returns:
        Dictionary with reversal analysis
    """
    # Get trend directions
    current_ema_trend = indicators_current['ema']['trend']
    previous_ema_trend = indicators_previous['ema']['trend']
    
    current_macd = indicators_current['macd']['signal']
    previous_macd = indicators_previous['macd']['signal']
    
    current_pattern = indicators_current.get('trend_pattern', {}).get('trend_direction', 'neutral')
    previous_pattern = indicators_previous.get('trend_pattern', {}).get('trend_direction', 'neutral')
    
    # Reversal detection
    reversal_type = "none"
    reversal_strength = 0
    confirmation_factors = []
    
    # Bullish reversal detection
    if previous_ema_trend in ['bearish', 'neutral'] and current_ema_trend == 'bullish':
        reversal_type = "bullish_reversal"
        reversal_strength += 30
        confirmation_factors.append("EMA crossover bullish")
        
        # Additional confirmations
        if current_macd == 'bullish' and previous_macd != 'bullish':
            reversal_strength += 25
            confirmation_factors.append("MACD bullish crossover")
        
        if current_pattern == 'bullish':
            reversal_strength += 20
            confirmation_factors.append("Higher highs/lows pattern")
        
        if indicators_current['rsi']['value'] > 50 and indicators_current['rsi']['signal'] != 'overbought':
            reversal_strength += 15
            confirmation_factors.append("RSI bullish zone")
        
        if indicators_current['volume']['trend'] == 'increasing':
            reversal_strength += 10
            confirmation_factors.append("Volume surge")
    
    # Bearish reversal detection
    elif previous_ema_trend in ['bullish', 'neutral'] and current_ema_trend == 'bearish':
        reversal_type = "bearish_reversal"
        reversal_strength += 30
        confirmation_factors.append("EMA crossover bearish")
        
        # Additional confirmations
        if current_macd == 'bearish' and previous_macd != 'bearish':
            reversal_strength += 25
            confirmation_factors.append("MACD bearish crossover")
        
        if current_pattern == 'bearish':
            reversal_strength += 20
            confirmation_factors.append("Lower highs/lows pattern")
        
        if indicators_current['rsi']['value'] < 50 and indicators_current['rsi']['signal'] != 'oversold':
            reversal_strength += 15
            confirmation_factors.append("RSI bearish zone")
        
        if indicators_current['volume']['trend'] == 'increasing':
            reversal_strength += 10
            confirmation_factors.append("Volume surge")
    
    # Classify reversal strength
    if reversal_strength >= 75:
        strength_label = "strong"
    elif reversal_strength >= 60:
        strength_label = "medium"
    elif reversal_strength >= 40:
        strength_label = "weak"
    else:
        strength_label = "none"
        reversal_type = "none"
    
    return {
        "reversal_detected": reversal_type != "none",
        "reversal_type": reversal_type,
        "strength": reversal_strength,
        "strength_label": strength_label,
        "confirmation_count": len(confirmation_factors),
        "confirmation_factors": confirmation_factors
    }


def detect_choppy_market(indicators: Dict, current_price: float) -> Dict:
    """
    Detect if market is ranging/choppy (hybrid detection without ADX)
    
    Args:
        indicators: All calculated indicators
        current_price: Current market price
        
    Returns:
        Dictionary with choppy market analysis
    """
    choppy_score = 0
    signals = []
    
    # 1. Bollinger Band squeeze
    if indicators['bollinger_bands'].get('squeeze', False):
        choppy_score += 2
        signals.append("BB squeeze (low volatility)")
    
    # 2. Low ATR (low volatility)
    atr_pct = indicators['atr']['percentage']
    if atr_pct < 1.5:
        choppy_score += 2
        signals.append(f"Low ATR ({atr_pct:.1f}%)")
    
    # 3. EMA convergence (no clear trend) - dynamic detection
    ema_keys = [k for k in indicators['ema'].keys() if k.startswith('ema_')]
    if len(ema_keys) >= 2:
        # Sort by period (e.g., ema_7, ema_20, ema_25, ema_50)
        ema_keys_sorted = sorted(ema_keys, key=lambda x: int(x.split('_')[1]))
        ema_short = indicators['ema'][ema_keys_sorted[0]]
        ema_long = indicators['ema'][ema_keys_sorted[1]]
        ema_distance = abs(ema_short - ema_long) / current_price * 100
        
        if ema_distance < 0.5:  # EMAs very close
            choppy_score += 2
            signals.append(f"EMA convergence ({ema_distance:.2f}%)")
    
    # 4. Narrow Support/Resistance range
    sr = indicators['support_resistance']
    if sr['nearest_resistance'] and sr['nearest_support']:
        sr_range = (sr['nearest_resistance'] - sr['nearest_support']) / current_price * 100
        if sr_range < 3:
            choppy_score += 1
            signals.append(f"Narrow S/R range ({sr_range:.1f}%)")
    
    # 5. Neutral trend
    if indicators['ema']['trend'] == 'neutral':
        choppy_score += 1
        signals.append("Neutral EMA trend")
    
    # Classify
    if choppy_score >= 5:
        condition = "choppy"
        warning = "AVOID trend trading!"
    elif choppy_score >= 3:
        condition = "ranging"
        warning = "Caution - weak trend"
    else:
        condition = "trending"
        warning = None
    
    return {
        "condition": condition,
        "choppy_score": choppy_score,
        "signals": signals,
        "warning": warning
    }


def calculate_all_indicators(df: pd.DataFrame) -> Dict:
    """
    Calculate all technical indicators including RSI_7
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Dictionary with all indicators
    """
    indicators = {
        "rsi": calculate_rsi(df, period=14),
        "rsi_7": calculate_rsi(df, period=7),  # Fast RSI for reversal detection
        "macd": calculate_macd(df),
        "ema": calculate_ema(df, [20, 50]),
        "bollinger_bands": calculate_bollinger_bands(df),
        "support_resistance": find_support_resistance(df),
        "volume": calculate_volume_analysis(df),
        "atr": calculate_atr(df),
        "trend_pattern": detect_trend_pattern(df)
    }
    
    # Detect choppy market
    current_price = df['close'].iloc[-1]
    indicators['market_condition'] = detect_choppy_market(indicators, current_price)
    
    return indicators


def calculate_all_indicators_custom(df: pd.DataFrame, ema_periods: List[int] = [20, 50]) -> Dict:
    """
    Calculate all technical indicators with custom EMA periods
    
    Args:
        df: DataFrame with OHLCV data
        ema_periods: Custom EMA periods (e.g., [7, 25])
        
    Returns:
        Dictionary with all indicators
    """
    indicators = {
        "rsi": calculate_rsi(df, period=14),
        "rsi_7": calculate_rsi(df, period=7),  # Fast RSI for reversal detection
        "macd": calculate_macd(df),
        "ema": calculate_ema(df, ema_periods),
        "bollinger_bands": calculate_bollinger_bands(df),
        "support_resistance": find_support_resistance(df),
        "volume": calculate_volume_analysis(df),
        "atr": calculate_atr(df),
        "trend_pattern": detect_trend_pattern(df)
    }
    
    # Detect choppy market
    current_price = df['close'].iloc[-1]
    indicators['market_condition'] = detect_choppy_market(indicators, current_price)
    
    return indicators
