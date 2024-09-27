from .candle import Candle


class Market:
    def __init__(self, exchange, symbol: str):
        self.exchange = exchange
        self.symbol = symbol
        self.mark_price = 0.0
        self.candles = []

    def get_mark_price(self) -> float:
        return self.mark_price

    def update(self, session):
        # Смотрим открытый интерес

        # Смотрим 15-минутные свечки
        seconds_in_15m = 15 * 60
        klines_15m = session.get_kline(symbol=self.symbol, interval='15')["result"]["list"]
        self.candles_15m = [Candle(data, seconds_in_15m) for data in reversed(klines_15m)]

        # Далее смотрим 4-часовые свечки
        seconds_in_4h = 4 * 60 * 60
        klines_4h = session.get_kline(symbol=self.symbol, interval='4h')["result"]["list"]
        self.candles_4h = [Candle(data, seconds_in_4h) for data in reversed(klines_4h)]

        # Определяем текущую цену маркета
        self.mark_price = self.candles_15m[-1].close_price
