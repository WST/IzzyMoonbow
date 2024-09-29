import logging
import pandas as pd
import numpy as np
from typing import List

class Market:
    def __init__(self, exchange, symbol: str, max_candles: int = 100):
        self.exchange = exchange
        self.symbol = symbol
        self.max_candles = max_candles
        self.candles_15m = pd.DataFrame()
        self.candles_4h = pd.DataFrame()
        self.logger = logging.getLogger(__name__)

    def update(self, session):
        self.logger.info(f"Updating market for {self.symbol}")
        new_candles_15m = self.exchange.get_kline(self.symbol, interval="15", limit=self.max_candles)
        new_candles_4h = self.exchange.get_kline(self.symbol, interval="240", limit=self.max_candles)
        
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
        
        self.candles_15m = self._process_candles(new_candles_15m, columns)
        self.candles_4h = self._process_candles(new_candles_4h, columns)
        
        self.logger.info(f"Updated {self.symbol} - 15m candles: {len(self.candles_15m)}, 4h candles: {len(self.candles_4h)}")

    def _process_candles(self, candles_data, columns):
        df = pd.DataFrame(candles_data, columns=columns)
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        df.set_index('timestamp', inplace=True)
        for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
            df[col] = df[col].astype(float)
        return df.sort_index()  # Sort by timestamp to ensure correct order

    def get_candles(self, timeframe: str) -> pd.DataFrame:
        if timeframe == '15m':
            return self.candles_15m
        elif timeframe == '4h':
            return self.candles_4h
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")

    def is_price_in_extreme_range(self, timeframe: str) -> str:
        candles = self.get_candles(timeframe)
        if candles.empty:
            return 'normal'
        
        current_price = candles['close'].iloc[-1]
        high = candles['high'].max()
        low = candles['low'].min()
        
        range_size = high - low
        upper_threshold = high - 0.1 * range_size
        lower_threshold = low + 0.1 * range_size
        
        if current_price >= upper_threshold:
            return 'high'
        elif current_price <= lower_threshold:
            return 'low'
        else:
            return 'normal'

    def get_mark_price(self) -> float:
        return self.candles_15m['close'].iloc[-1] if not self.candles_15m.empty else None

    def get_chart_time_range(self, timeframe: str) -> str:
        candles = self.get_candles(timeframe)
        if candles.empty:
            return "Unknown time range"
        
        start_time = candles.index[0]
        end_time = candles.index[-1]
        duration = end_time - start_time
        
        days = duration.days
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        if days > 0:
            return f"{days} days {hours} hours"
        elif hours > 0:
            return f"{hours} hours {minutes} minutes"
        else:
            return f"{minutes} minutes"
