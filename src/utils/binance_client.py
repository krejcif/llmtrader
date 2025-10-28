"""Binance Futures API client for market data and live trading"""
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, List
import config


class BinanceClient:
    """Client for fetching Binance Futures market data and executing trades"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, demo: Optional[bool] = None):
        """
        Initialize Binance client
        
        Args:
            api_key: Optional API key (not required for public data)
            api_secret: Optional API secret (not required for public data)
            demo: Optional demo mode flag (uses testnet if True)
        """
        # Use config values if not provided
        self.api_key = api_key if api_key else config.BINANCE_API_KEY
        self.api_secret = api_secret if api_secret else config.BINANCE_API_SECRET
        self.demo = demo if demo is not None else config.BINANCE_DEMO
        
        # Initialize client with testnet URL if demo mode
        if self.demo:
            self.client = Client(
                self.api_key, 
                self.api_secret,
                testnet=True
            )
            print("🧪 Using Binance Futures TESTNET (Demo Mode)")
        else:
            self.client = Client(self.api_key, self.api_secret)
        
        self.has_credentials = bool(self.api_key and self.api_secret)
        
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
    
    # =============================================================================
    # LIVE TRADING FUNCTIONS (Require API credentials)
    # =============================================================================
    
    def check_credentials(self):
        """Check if API credentials are available"""
        if not self.has_credentials:
            raise Exception("API credentials required for live trading. Set BINANCE_API_KEY and BINANCE_API_SECRET in .env")
    
    def get_account_balance(self) -> Dict:
        """
        Get futures account balance
        
        Returns:
            Dictionary with account balance info
        """
        self.check_credentials()
        try:
            account = self.client.futures_account()
            
            # Extract relevant balance info
            total_balance = float(account['totalWalletBalance'])
            available_balance = float(account['availableBalance'])
            unrealized_pnl = float(account['totalUnrealizedProfit'])
            
            # Get USDT asset specifically
            usdt_asset = next((asset for asset in account['assets'] if asset['asset'] == 'USDT'), None)
            
            return {
                'total_balance': total_balance,
                'available_balance': available_balance,
                'unrealized_pnl': unrealized_pnl,
                'usdt_balance': float(usdt_asset['walletBalance']) if usdt_asset else 0,
                'usdt_available': float(usdt_asset['availableBalance']) if usdt_asset else 0,
                'timestamp': datetime.now().isoformat()
            }
        except BinanceAPIException as e:
            raise Exception(f"Error fetching account balance: {e}")
    
    def get_open_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open futures positions
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open positions
        """
        self.check_credentials()
        try:
            positions = self.client.futures_position_information()
            
            # Filter positions with non-zero amount
            open_positions = []
            for pos in positions:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:
                    if symbol is None or pos['symbol'] == symbol:
                        open_positions.append({
                            'symbol': pos['symbol'],
                            'position_amt': position_amt,
                            'entry_price': float(pos['entryPrice']),
                            'unrealized_pnl': float(pos['unRealizedProfit']),
                            'leverage': int(pos['leverage']),
                            'side': 'LONG' if position_amt > 0 else 'SHORT',
                            'liquidation_price': float(pos['liquidationPrice'])
                        })
            
            return open_positions
        except BinanceAPIException as e:
            raise Exception(f"Error fetching open positions: {e}")
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        Set leverage for a symbol
        
        Args:
            symbol: Trading pair
            leverage: Leverage value (1-125)
            
        Returns:
            Response from API
        """
        self.check_credentials()
        try:
            response = self.client.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            return response
        except BinanceAPIException as e:
            raise Exception(f"Error setting leverage: {e}")
    
    def place_market_order(self, symbol: str, side: str, quantity: float, 
                          reduce_only: bool = False) -> Dict:
        """
        Place a market order (immediate execution)
        
        Args:
            symbol: Trading pair (e.g., 'SOLUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity (in base asset, e.g., SOL)
            reduce_only: If True, only reduces position (won't open new)
            
        Returns:
            Order response from API
        """
        self.check_credentials()
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity
            }
            
            if reduce_only:
                params['reduceOnly'] = 'true'
            
            order = self.client.futures_create_order(**params)
            
            return {
                'order_id': order['orderId'],
                'client_order_id': order['clientOrderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'status': order['status'],
                'executed_qty': float(order['executedQty']),
                'avg_price': float(order.get('avgPrice', 0)),
                'timestamp': order['updateTime']
            }
        except BinanceAPIException as e:
            raise Exception(f"Error placing market order: {e}")
    
    def place_stop_market_order(self, symbol: str, side: str, quantity: float,
                                stop_price: float, reduce_only: bool = True) -> Dict:
        """
        Place a stop-market order (triggers at stop price)
        Used for stop-loss orders
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            stop_price: Trigger price
            reduce_only: If True, only reduces position
            
        Returns:
            Order response from API
        """
        self.check_credentials()
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'STOP_MARKET',
                'quantity': quantity,
                'stopPrice': stop_price
            }
            
            if reduce_only:
                params['reduceOnly'] = 'true'
            
            order = self.client.futures_create_order(**params)
            
            return {
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'status': order['status'],
                'quantity': float(order['origQty']),
                'stop_price': float(order['stopPrice']),
                'timestamp': order['updateTime']
            }
        except BinanceAPIException as e:
            raise Exception(f"Error placing stop order: {e}")
    
    def place_take_profit_market_order(self, symbol: str, side: str, quantity: float,
                                       stop_price: float, reduce_only: bool = True) -> Dict:
        """
        Place a take-profit market order (triggers at TP price)
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            stop_price: Trigger price (take profit)
            reduce_only: If True, only reduces position
            
        Returns:
            Order response from API
        """
        self.check_credentials()
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'TAKE_PROFIT_MARKET',
                'quantity': quantity,
                'stopPrice': stop_price
            }
            
            if reduce_only:
                params['reduceOnly'] = 'true'
            
            order = self.client.futures_create_order(**params)
            
            return {
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'status': order['status'],
                'quantity': float(order['origQty']),
                'stop_price': float(order['stopPrice']),
                'timestamp': order['updateTime']
            }
        except BinanceAPIException as e:
            raise Exception(f"Error placing take profit order: {e}")
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """
        Cancel an open order
        
        Args:
            symbol: Trading pair
            order_id: Order ID to cancel
            
        Returns:
            Cancellation response
        """
        self.check_credentials()
        try:
            result = self.client.futures_cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            return {
                'order_id': result['orderId'],
                'symbol': result['symbol'],
                'status': result['status']
            }
        except BinanceAPIException as e:
            raise Exception(f"Error canceling order: {e}")
    
    def cancel_all_orders(self, symbol: str) -> Dict:
        """
        Cancel all open orders for a symbol
        
        Args:
            symbol: Trading pair
            
        Returns:
            Cancellation response
        """
        self.check_credentials()
        try:
            result = self.client.futures_cancel_all_open_orders(symbol=symbol)
            return {'cancelled': True, 'symbol': symbol}
        except BinanceAPIException as e:
            raise Exception(f"Error canceling all orders: {e}")
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get all open orders
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open orders
        """
        self.check_credentials()
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            orders = self.client.futures_get_open_orders(**params)
            
            return [{
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'status': order['status'],
                'quantity': float(order['origQty']),
                'price': float(order.get('price', 0)),
                'stop_price': float(order.get('stopPrice', 0)),
                'timestamp': order['time']
            } for order in orders]
        except BinanceAPIException as e:
            raise Exception(f"Error fetching open orders: {e}")

