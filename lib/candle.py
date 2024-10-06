import logging

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
        self.open_interest = float(data['open_interest']) if 'open_interest' in data else None
        self.prev: Optional['Candle'] = None
        self.next: Optional['Candle'] = None

    def is_bullish(self) -> bool:
        return self.close >= self.open

    def get_fvg(self, min_gap_percent: float) -> Optional[FVG]:
        if not (self.prev and self.next):
            return None

        if self.is_bullish():
            fvg_size = self.next.low - self.prev.high
            fvg_size_in_percent = (fvg_size / self.prev.high) * 100.0
            if (fvg_size > 0) and fvg_size_in_percent > min_gap_percent:
                return FVG(self.prev.high, self.next.low, self)
        else:
            fvg_size = self.prev.low - self.next.high
            fvg_size_in_percent = (fvg_size / self.next.high) * 100.0
            if fvg_size > 0 and fvg_size_in_percent > min_gap_percent:
                return FVG(self.prev.low, self.next.high, self)

        return None
