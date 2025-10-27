"""Momentum Analysis for Intraday Trading"""
import pandas as pd
import numpy as np
from typing import Dict, List


def analyze_recent_candles(candles: pd.DataFrame, n: int = 5) -> Dict:
    """
    Analyze recent N candles for momentum patterns
    
    Args:
        candles: DataFrame with OHLCV data
        n: Number of recent candles to analyze
        
    Returns:
        Dict with recent candle analysis
    """
    recent = candles.tail(n)
    
    candle_analysis = []
    bullish_count = 0
    total_volume_ratio = 0
    
    for idx, row in recent.iterrows():
        change_pct = ((row['close'] - row['open']) / row['open']) * 100
        is_bullish = row['close'] > row['open']
        
        # Volume vs average
        avg_volume = candles['volume'].tail(20).mean()
        volume_ratio = row['volume'] / avg_volume if avg_volume > 0 else 1.0
        
        candle_type = "BULLISH" if is_bullish else "BEARISH"
        if abs(change_pct) < 0.05:
            candle_type = "neutral"
        
        candle_analysis.append({
            'open': round(row['open'], 2),
            'close': round(row['close'], 2),
            'change_pct': round(change_pct, 2),
            'volume_ratio': round(volume_ratio, 2),
            'type': candle_type
        })
        
        if is_bullish:
            bullish_count += 1
        total_volume_ratio += volume_ratio
    
    # Detect pattern
    if bullish_count >= 4:
        pattern = "Strong bullish momentum"
    elif bullish_count >= 3:
        pattern = "Building bullish momentum"
    elif bullish_count <= 1:
        pattern = "Strong bearish momentum"
    elif bullish_count <= 2:
        pattern = "Building bearish momentum"
    else:
        pattern = "Mixed/choppy"
    
    avg_volume_ratio = total_volume_ratio / n
    
    return {
        'candles': candle_analysis,
        'bullish_count': bullish_count,
        'bearish_count': n - bullish_count,
        'pattern': pattern,
        'avg_volume_ratio': round(avg_volume_ratio, 2)
    }


def analyze_volume_momentum(candles: pd.DataFrame) -> Dict:
    """
    Analyze volume momentum and detect spikes
    
    Args:
        candles: DataFrame with OHLCV data
        
    Returns:
        Dict with volume momentum analysis
    """
    current_volume = candles['volume'].iloc[-1]
    prev_volume = candles['volume'].iloc[-2] if len(candles) >= 2 else current_volume
    
    # Calculate averages
    avg_20 = candles['volume'].tail(20).mean()
    avg_50 = candles['volume'].tail(50).mean() if len(candles) >= 50 else avg_20
    
    # Volume ratios
    current_vs_avg = current_volume / avg_20 if avg_20 > 0 else 1.0
    prev_vs_avg = prev_volume / avg_20 if avg_20 > 0 else 1.0
    
    # Volume change
    volume_change_pct = ((current_volume - prev_volume) / prev_volume * 100) if prev_volume > 0 else 0
    
    # Detect trend
    if current_vs_avg > 1.5:
        status = "⚠️ VOLUME SPIKE (potential breakout)"
        trend = "SURGING"
    elif current_vs_avg > 1.2:
        status = "High volume"
        trend = "INCREASING"
    elif current_vs_avg < 0.7:
        status = "Low volume"
        trend = "DECREASING"
    else:
        status = "Normal volume"
        trend = "STABLE"
    
    return {
        'current': round(current_volume, 2),
        'previous': round(prev_volume, 2),
        'avg_20': round(avg_20, 2),
        'current_vs_avg': round(current_vs_avg, 2),
        'prev_vs_avg': round(prev_vs_avg, 2),
        'change_pct': round(volume_change_pct, 2),
        'trend': trend,
        'status': status,
        'is_spike': current_vs_avg > 1.5
    }


def find_immediate_levels(candles: pd.DataFrame, lookback: int = 30) -> Dict:
    """
    Find immediate support/resistance from recent swing points
    
    Args:
        candles: DataFrame with OHLCV data
        lookback: Number of candles to look back
        
    Returns:
        Dict with immediate levels
    """
    recent = candles.tail(lookback)
    current_price = candles['close'].iloc[-1]
    
    # Find swing highs (local maxima)
    highs = recent['high'].values
    swing_highs = []
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swing_highs.append(highs[i])
    
    # Find swing lows (local minima)
    lows = recent['low'].values
    swing_lows = []
    for i in range(2, len(lows) - 2):
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
           lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swing_lows.append(lows[i])
    
    # Get most recent
    recent_high = max(swing_highs) if swing_highs else recent['high'].max()
    recent_low = min(swing_lows) if swing_lows else recent['low'].min()
    
    # Calculate distances
    dist_to_high = ((recent_high - current_price) / current_price) * 100
    dist_to_low = ((current_price - recent_low) / current_price) * 100
    
    # Position analysis
    if dist_to_high < 0.2:
        position = "AT resistance (breakout watch)"
    elif dist_to_low < 0.2:
        position = "AT support (bounce watch)"
    elif dist_to_high < dist_to_low:
        position = "Near resistance"
    else:
        position = "Near support"
    
    return {
        'recent_high': round(recent_high, 2),
        'recent_low': round(recent_low, 2),
        'distance_to_high_pct': round(dist_to_high, 2),
        'distance_to_low_pct': round(dist_to_low, 2),
        'position': position,
        'range_size_pct': round(((recent_high - recent_low) / recent_low) * 100, 2)
    }


def calculate_momentum_score(candles: pd.DataFrame, rsi_7: float) -> Dict:
    """
    Calculate overall momentum score
    
    Args:
        candles: DataFrame with OHLCV data
        rsi_7: Current RSI(7) value
        
    Returns:
        Dict with momentum score and components
    """
    current_price = candles['close'].iloc[-1]
    
    # Price velocity (15min and 30min)
    if len(candles) >= 3:
        price_15min_ago = candles['close'].iloc[-3]  # ~15min ago on 5m
        velocity_15min = ((current_price - price_15min_ago) / price_15min_ago) * 100
    else:
        velocity_15min = 0
    
    if len(candles) >= 6:
        price_30min_ago = candles['close'].iloc[-6]  # ~30min ago on 5m
        velocity_30min = ((current_price - price_30min_ago) / price_30min_ago) * 100
    else:
        velocity_30min = 0
    
    # Volume trend
    current_vol = candles['volume'].iloc[-1]
    vol_1h_ago = candles['volume'].iloc[-12] if len(candles) >= 12 else current_vol
    vol_change = ((current_vol - vol_1h_ago) / vol_1h_ago * 100) if vol_1h_ago > 0 else 0
    
    # RSI momentum (rising/falling)
    if len(candles) >= 3:
        rsi_prev = 50  # Placeholder, would need to calculate
        rsi_momentum = "Rising" if rsi_7 > 50 else "Falling"
    else:
        rsi_momentum = "Neutral"
    
    # Calculate score (0-10)
    score = 5  # Start neutral
    
    # Price velocity component (+/- 2 points)
    if velocity_15min > 0.5:
        score += 2
    elif velocity_15min > 0.2:
        score += 1
    elif velocity_15min < -0.5:
        score -= 2
    elif velocity_15min < -0.2:
        score -= 1
    
    # Volume component (+/- 1 point)
    if vol_change > 20:
        score += 1
    elif vol_change < -20:
        score -= 1
    
    # RSI component (+/- 2 points)
    if rsi_7 > 60:
        score += 1
    elif rsi_7 < 40:
        score -= 1
    
    # Clamp to 0-10
    score = max(0, min(10, score))
    
    # Interpret
    if score >= 7:
        interpretation = "STRONG BULLISH"
        direction = "UP"
    elif score >= 6:
        interpretation = "MODERATE BULLISH"
        direction = "UP"
    elif score <= 3:
        interpretation = "STRONG BEARISH"
        direction = "DOWN"
    elif score <= 4:
        interpretation = "MODERATE BEARISH"
        direction = "DOWN"
    else:
        interpretation = "NEUTRAL"
        direction = "SIDEWAYS"
    
    return {
        'score': score,
        'interpretation': interpretation,
        'direction': direction,
        'velocity_15min': round(velocity_15min, 2),
        'velocity_30min': round(velocity_30min, 2),
        'volume_change_pct': round(vol_change, 2),
        'rsi_momentum': rsi_momentum
    }


def analyze_current_candle(candles: pd.DataFrame) -> Dict:
    """
    Analyze the current candle in progress
    
    Args:
        candles: DataFrame with OHLCV data
        
    Returns:
        Dict with current candle analysis
    """
    current = candles.iloc[-1]
    
    open_price = current['open']
    close_price = current['close']
    high = current['high']
    low = current['low']
    
    # Candle body
    body = close_price - open_price
    body_pct = (body / open_price) * 100
    
    # Wicks
    upper_wick = high - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low
    
    body_size = abs(body)
    wick_total = upper_wick + lower_wick
    
    # Candle type
    if body_pct > 0.1:
        if upper_wick < body_size * 0.3:
            candle_type = "Strong bullish (no rejection)"
        else:
            candle_type = "Bullish with upper wick (some resistance)"
    elif body_pct < -0.1:
        if lower_wick < body_size * 0.3:
            candle_type = "Strong bearish (no support)"
        else:
            candle_type = "Bearish with lower wick (some support)"
    else:
        if wick_total > body_size * 3:
            candle_type = "Doji/indecision (high rejection)"
        else:
            candle_type = "Small body (consolidation)"
    
    # Pressure
    if body_pct > 0.05:
        pressure = "BUYING pressure"
    elif body_pct < -0.05:
        pressure = "SELLING pressure"
    else:
        pressure = "Balanced/indecision"
    
    return {
        'open': round(open_price, 2),
        'close': round(close_price, 2),
        'high': round(high, 2),
        'low': round(low, 2),
        'body_pct': round(body_pct, 2),
        'upper_wick': round(upper_wick, 2),
        'lower_wick': round(lower_wick, 2),
        'type': candle_type,
        'pressure': pressure,
        'is_bullish': body > 0
    }



