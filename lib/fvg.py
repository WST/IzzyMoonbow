from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .candle import Candle

class FVG:
    def __init__(self, size: float, start_price: float, end_price: float, parent_candle: 'Candle'):
        self.size = size
        self.start_price = start_price
        self.end_price = end_price
        self.parent_candle = parent_candle
        self.is_bullish = parent_candle.is_bullish()

    def is_covered(self) -> bool:
        current_candle = self.parent_candle.next.next  # Start from the candle after the FVG
        while current_candle:
            if self.is_bullish:
                if current_candle.low <= self.start_price:
                    return True
            else:
                if current_candle.high >= self.end_price:
                    return True
            current_candle = current_candle.next
        return False
