"""Binance Futures API client for market data"""
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, List


class BinanceClient:
    """Client for fetching Binance Futures market data"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize Binance client
        
        Args:
            api_key: Optional API key (not required for public data)
            api_secret: Optional API secret (not required for public data)
        """
        self.client = Client(api_key, api_secret)
        
    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'SOLUSDT')
            
        Returns:
            Current price as float
        """
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            raise Exception(f"Error fetching current price: {e}")
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """
        Get historical klines (candlestick data)
        
        Args:
            symbol: Trading pair (e.g., 'SOLUSDT')
            interval: Timeframe (e.g., '1h', '4h')
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            klines = self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Keep only relevant columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # Remove last candle (incomplete/currently forming) for data integrity
            # This ensures we only use CLOSED candles for analysis
            if len(df) > 1:
                df = df.iloc[:-1].reset_index(drop=True)
            
            return df
        except BinanceAPIException as e:
            raise Exception(f"Error fetching klines: {e}")
    
    def get_funding_rate(self, symbol: str) -> float:
        """
        Get current funding rate
        
        Args:
            symbol: Trading pair (e.g., 'SOLUSDT')
            
        Returns:
            Current funding rate as float
        """
        try:
            funding_rate = self.client.futures_funding_rate(symbol=symbol, limit=1)
            if funding_rate:
                return float(funding_rate[0]['fundingRate'])
            return 0.0
        except BinanceAPIException as e:
            raise Exception(f"Error fetching funding rate: {e}")
    
    def get_orderbook(self, symbol: str, limit: int = 100) -> Dict:
        """
        Get orderbook (depth) data
        
        Args:
            symbol: Trading pair (e.g., 'SOLUSDT')
            limit: Depth limit (5, 10, 20, 50, 100, 500, 1000)
            
        Returns:
            Dictionary with bids and asks
        """
        try:
            depth = self.client.futures_order_book(symbol=symbol, limit=limit)
            
            # Convert to lists of [price, quantity]
            bids = [[float(price), float(qty)] for price, qty in depth['bids']]
            asks = [[float(price), float(qty)] for price, qty in depth['asks']]
            
            return {
                "bids": bids,  # Buy orders [[price, quantity], ...]
                "asks": asks,  # Sell orders [[price, quantity], ...]
                "last_update_id": depth['lastUpdateId']
            }
        except BinanceAPIException as e:
            raise Exception(f"Error fetching orderbook: {e}")
    
    def get_market_data(self, symbol: str, interval: str, limit: int = 100) -> Dict:
        """
        Get complete market data package for single timeframe
        
        Args:
            symbol: Trading pair
            interval: Timeframe
            limit: Number of candles
            
        Returns:
            Dictionary with all market data
        """
        current_price = self.get_current_price(symbol)
        candles = self.get_klines(symbol, interval, limit)
        funding_rate = self.get_funding_rate(symbol)
        orderbook = self.get_orderbook(symbol, limit=100)
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "timestamp": datetime.now().isoformat(),
            "candles": candles,
            "funding_rate": funding_rate,
            "orderbook": orderbook
        }
    
    def get_multi_timeframe_data(self, symbol: str, timeframes: List[str], limit: int = 100) -> Dict:
        """
        Get market data for multiple timeframes
        
        Args:
            symbol: Trading pair
            timeframes: List of timeframes (e.g., ['1h', '15m'])
            limit: Number of candles per timeframe
            
        Returns:
            Dictionary with multi-timeframe data
        """
        current_price = self.get_current_price(symbol)
        funding_rate = self.get_funding_rate(symbol)
        orderbook = self.get_orderbook(symbol, limit=100)
        
        # Get candles for each timeframe
        timeframe_data = {}
        for tf in timeframes:
            candles = self.get_klines(symbol, tf, limit)
            timeframe_data[tf] = candles
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "timestamp": datetime.now().isoformat(),
            "timeframes": timeframe_data,
            "funding_rate": funding_rate,
            "orderbook": orderbook
        }

