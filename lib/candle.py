import pandas as pd
from typing import Optional
from .fvg import FVG


class Candle:
    def __init__(self, data: pd.Series):
        self.data = data
        self.open = float(data['open'])
        self.high = float(data['high'])
        self.low = float(data['low'])
        self.close = float(data['close'])
        self.timestamp = data.name
        self.prev: Optional['Candle'] = None
        self.next: Optional['Candle'] = None

    def is_bullish(self) -> bool:
        return self.close >= self.open

    def get_fvg(self) -> Optional[FVG]:
        if not (self.prev and self.next):
            return None

        if self.is_bullish():
            fvg_size = self.prev.high - self.next.low
            if fvg_size > 0:
                return FVG(fvg_size, self.next.low, self.prev.high, self)
        else:
            fvg_size = self.next.high - self.prev.low
            if fvg_size > 0:
                return FVG(fvg_size, self.prev.low, self.next.high, self)

        return None
