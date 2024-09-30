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
        """
        Determines if the FVG (Fair Value Gap) is fully covered by subsequent price action.

        This method checks if any candle after the FVG formation has crossed the FVG's price range:
        - For a bullish FVG: checks if any subsequent candle's low price is less than or equal to the FVG's start price.
        - For a bearish FVG: checks if any subsequent candle's high price is greater than or equal to the FVG's end price.

        Current limitations:
        1. This method only detects full coverage of the FVG.
        2. Partial coverage is not considered.

        Future improvements:
        1. Implement partial coverage detection.
        2. Add a get_covered_size method to calculate the exact size of the covered part.
        3. Redefine is_covered to use get_covered_size, considering an FVG as covered if, for example, 
           more than 90% of its size is filled.

        Returns:
        bool: True if the FVG is fully covered, False otherwise.
        """
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
