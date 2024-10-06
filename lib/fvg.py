import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .candle import Candle


# Для простоты определим FVG как разницу между ближайшими фитилями соседних свечей
class FVG:
    def __init__(self, start_price: float, end_price: float, parent_candle: 'Candle'):
        self.size = abs(end_price - start_price)
        self.start_price = start_price
        self.end_price = end_price
        self.parent_candle = parent_candle

    def is_bullish(self) -> bool:
        return self.parent_candle.is_bullish()

    # Вернуть размер проторгованной части имбаланса
    def get_covered_size(self) -> float:
        current_candle = self.parent_candle.next.next
        covered_size = 0.0
        while current_candle:
            if self.is_bullish():
                if current_candle.low < self.end_price:
                    diff = self.end_price - current_candle.low
                    if diff > covered_size:
                        covered_size = min(diff, self.size)
            else:
                if current_candle.high > self.end_price:
                    diff = current_candle.high - self.end_price
                    if diff > covered_size:
                        covered_size = min(diff, self.size)

            current_candle = current_candle.next

        return covered_size

    # Определить сколько процентов составляет проторгованная часть имбаланса от общего размера
    def get_covered_size_percent(self) -> float:
        covered_size = self.get_covered_size()
        return (covered_size / self.size) * 100.0

    # Проверить, находится ли проторгованная часть имбаланса в заданном процентном диапазоне
    def is_covered(self, percent: int = 90) -> bool:
        return self.get_covered_size_percent() >= percent

    # Вернуть нижний предел непроторгованной части имбаланса
    def get_lower_bound(self) -> float:
        if self.is_bullish():
            return self.start_price
        else:
            covered_size = self.get_covered_size()
            return self.end_price + covered_size

    # Вернуть верхний предел непроторгованной части имбаланса
    def get_upper_bound(self) -> float:
        if self.is_bullish():
            covered_size = self.get_covered_size()
            return self.end_price - covered_size
        else:
            return self.start_price
