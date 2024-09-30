import logging
import pandas as pd
from typing import List, Optional
from .chart_generator import ChartGenerator
from .fvg import FVG
from .chart import Chart
from .candle import Candle

class Market:
    def __init__(self, exchange, symbol: str):
        self.exchange = exchange
        self.symbol = symbol
        self.max_candles = 100
        self.candles_15m: List[Candle] = []
        self.candles_4h: List[Candle] = []
        self.logger = logging.getLogger(__name__)
        self.chart_generator = ChartGenerator()
        self.high_threshold = None
        self.low_threshold = None

    def update_from_data(self, data):
        self.candles_15m = self._process_candles(data['15m'])
        self.candles_4h = self._process_candles(data['4h'])

    def update(self, session):
        new_candles_15m = self.exchange.get_kline(self.symbol, interval="15", limit=self.max_candles)
        new_candles_4h = self.exchange.get_kline(self.symbol, interval="240", limit=self.max_candles)
        
        self.candles_15m = self._process_candles(new_candles_15m)
        self.candles_4h = self._process_candles(new_candles_4h)

    def _process_candles(self, candles_data: pd.DataFrame) -> List[Candle]:
        candles = [Candle(row) for _, row in candles_data.iterrows()]
        for i in range(1, len(candles)):
            candles[i].prev = candles[i-1]
            candles[i-1].next = candles[i]
        return candles

    def get_candles(self, timeframe: str) -> List[Candle]:
        if timeframe == '15m':
            return self.candles_15m
        elif timeframe == '4h':
            return self.candles_4h
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")

    def get_fvgs(self, timeframe: str) -> List[FVG]:
        candles = self.get_candles(timeframe)
        return [fvg for candle in candles if (fvg := candle.get_fvg()) is not None]

    def get_chart(self, timeframe: str) -> Optional[Chart]:
        candles = self.get_candles(timeframe)
        if not candles:
            self.logger.error(f"No candle data for {self.symbol} on {timeframe} timeframe")
            return None

        df = pd.DataFrame([c.data for c in candles])
        time_range = self.get_chart_time_range(timeframe)
        title = f"{self.symbol} - {timeframe} ({time_range})"
        
        try:
            chart = self.chart_generator.generate_candlestick_chart(df, title)
            return chart
        except Exception as e:
            self.logger.exception(f"Error generating chart for {self.symbol}")
            return None

    def get_chart_with_fvgs(self, timeframe: str) -> Optional[Chart]:
        chart = self.get_chart(timeframe)
        if chart is None:
            return None

        fvgs = self.get_fvgs(timeframe)
        chart.draw_fvgs(fvgs)
        return chart

    def is_price_in_extreme_range(self, timeframe: str) -> str:
        candles = self.get_candles(timeframe)
        if not candles:
            return 'normal'
        
        current_price = candles[-1].close
        high = max(candle.high for candle in candles)
        low = min(candle.low for candle in candles)
        
        range_size = high - low
        self.high_threshold = high - 0.1 * range_size
        self.low_threshold = low + 0.1 * range_size
        
        if current_price >= self.high_threshold:
            return 'high'
        elif current_price <= self.low_threshold:
            return 'low'
        else:
            return 'normal'

    def get_mark_price(self) -> float:
        return self.candles_15m[-1].close if self.candles_15m else None

    def get_chart_time_range(self, timeframe: str) -> str:
        candles = self.get_candles(timeframe)
        if not candles:
            return "Unknown time range"
        
        start_time = candles[0].timestamp
        end_time = candles[-1].timestamp
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