class Candle:
    def __init__(self, data, timeframe: int):
        self.start_time = int(data[0]) / 1000
        self.open_price = float(data[1])
        self.high_price = float(data[2])
        self.low_price = float(data[3])
        self.close_price = float(data[4])
        self.volume = float(data[5])
        self.turnover = float(data[6])
        self.timeframe = timeframe

        if self.close_price >= self.open_price:
            self.direction = "bull"
        else:
            self.direction = "bear"

    def is_bullish_crossover(self, candle):
        return self.close_price > candle.close_price and candle.close_price < self.open_price
