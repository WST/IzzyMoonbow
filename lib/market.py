from .candle import Candle
from collections import deque
from typing import List, Deque

class Market:
    def __init__(self, exchange, symbol: str, max_candles: int = 100):
        self.exchange = exchange
        self.symbol = symbol
        self.mark_price = 0.0
        self.max_candles = max_candles
        self.candles_15m: Deque[Candle] = deque(maxlen=max_candles)
        self.candles_4h: Deque[Candle] = deque(maxlen=max_candles)

    def get_mark_price(self) -> float:
        return self.mark_price

    def update(self, session):
        # Смотрим 15-минутные свечки
        seconds_in_15m = 15 * 60
        klines_15m = session.get_kline(symbol=self.symbol, interval='15')["result"]["list"]
        new_candles_15m = [Candle(data, seconds_in_15m) for data in reversed(klines_15m)]
        self.candles_15m.extend(new_candles_15m)

        # Смотрим 4-часовые свечки
        seconds_in_4h = 4 * 60 * 60
        klines_4h = session.get_kline(symbol=self.symbol, interval='4h')["result"]["list"]
        new_candles_4h = [Candle(data, seconds_in_4h) for data in reversed(klines_4h)]
        self.candles_4h.extend(new_candles_4h)

        # Определяем текущую цену маркета
        self.mark_price = self.candles_15m[-1].close_price if self.candles_15m else 0.0

    def get_recent_candles(self, timeframe: str, count: int) -> List[Candle]:
        if timeframe == '15m':
            return list(self.candles_15m)[-count:]
        elif timeframe == '4h':
            return list(self.candles_4h)[-count:]
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

    def is_price_in_extreme_range(self, timeframe: str, threshold: float = 0.05) -> str:
        """
        Проверяет, находится ли текущая цена в верхнем или нижнем threshold% диапазона цен.
        
        :param timeframe: '15m' или '4h'
        :param threshold: процент диапазона для проверки (по умолчанию 5%)
        :return: 'high' если цена в верхнем диапазоне, 'low' если в нижнем, 'normal' в противном случае
        """
        candles = self.get_recent_candles(timeframe, self.max_candles)
        if not candles:
            return 'normal'  # Если нет свечей, считаем ситуацию нормальной

        high = max(candle.high_price for candle in candles)
        low = min(candle.low_price for candle in candles)
        price_range = high - low

        if price_range == 0:
            return 'normal'  # Избегаем деления на ноль

        lower_threshold = low + price_range * threshold
        upper_threshold = high - price_range * threshold

        if self.mark_price <= lower_threshold:
            return 'low'
        elif self.mark_price >= upper_threshold:
            return 'high'
        else:
            return 'normal'
