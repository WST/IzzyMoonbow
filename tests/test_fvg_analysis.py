import pandas as pd
import pytest
from lib.candle import Candle
from lib.fvg import FVG

def test_candle_creation():
    data = pd.Series({'open': 100, 'high': 110, 'low': 90, 'close': 105}, name=pd.Timestamp('2023-01-01'))
    candle = Candle(data)
    assert candle.open == 100
    assert candle.high == 110
    assert candle.low == 90
    assert candle.close == 105
    assert candle.timestamp == pd.Timestamp('2023-01-01')
    assert candle.is_bullish() == True

def test_fvg_detection():
    candle1 = Candle(pd.Series({'open': 100, 'high': 110, 'low': 90, 'close': 105}, name=pd.Timestamp('2023-01-01')))
    candle2 = Candle(pd.Series({'open': 106, 'high': 115, 'low': 102, 'close': 112}, name=pd.Timestamp('2023-01-02')))
    candle3 = Candle(pd.Series({'open': 114, 'high': 120, 'low': 108, 'close': 118}, name=pd.Timestamp('2023-01-03')))

    candle1.next = candle2
    candle2.prev = candle1
    candle2.next = candle3
    candle3.prev = candle2

    fvg = candle2.get_fvg()
    assert fvg is not None
    assert fvg.size == 2  # 110 - 108
    assert fvg.start_price == 108
    assert fvg.end_price == 110
    assert fvg.is_bullish == True

def test_fvg_coverage():
    candle1 = Candle(pd.Series({'open': 100, 'high': 110, 'low': 90, 'close': 105}, name=pd.Timestamp('2023-01-01')))
    candle2 = Candle(pd.Series({'open': 106, 'high': 115, 'low': 102, 'close': 112}, name=pd.Timestamp('2023-01-02')))
    candle3 = Candle(pd.Series({'open': 114, 'high': 120, 'low': 108, 'close': 118}, name=pd.Timestamp('2023-01-03')))
    candle4 = Candle(pd.Series({'open': 117, 'high': 122, 'low': 109, 'close': 120}, name=pd.Timestamp('2023-01-04')))

    candle1.next = candle2
    candle2.prev = candle1
    candle2.next = candle3
    candle3.prev = candle2
    candle3.next = candle4
    candle4.prev = candle3

    fvg = candle2.get_fvg()
    print(f"FVG: start_price={fvg.start_price}, end_price={fvg.end_price}, is_bullish={fvg.is_bullish}")
    print(f"Candle1: high={candle1.high}, low={candle1.low}")
    print(f"Candle2: high={candle2.high}, low={candle2.low}")
    print(f"Candle3: high={candle3.high}, low={candle3.low}")
    print(f"Candle4: high={candle4.high}, low={candle4.low}")
    print(f"Is covered: {fvg.is_covered()}")
    assert fvg.is_covered() == False

    candle5 = Candle(pd.Series({'open': 115, 'high': 118, 'low': 105, 'close': 110}, name=pd.Timestamp('2023-01-05')))
    candle4.next = candle5
    candle5.prev = candle4

    print(f"After adding candle5 (high={candle5.high}, low={candle5.low})")
    print(f"Is covered: {fvg.is_covered()}")
    assert fvg.is_covered() == True