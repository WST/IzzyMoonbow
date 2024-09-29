import logging
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from io import BytesIO

class ChartGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_candlestick_chart(self, df: pd.DataFrame, symbol: str, timeframe: str, time_range: str):
        # Select only the OHLC data
        df = df[['open', 'high', 'low', 'close']]
        
        # Create custom style
        mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
        s = mpf.make_mpf_style(marketcolors=mc)

        # Create the candlestick chart
        timeframe_label = "15м" if timeframe == "15m" else "4ч"
        fig, axes = mpf.plot(df, type='candle', style=s,
                             title=f'{symbol} - График {timeframe_label}\nВременной диапазон: {time_range}',
                             ylabel='Цена (USDT)',
                             volume=False,
                             figsize=(10, 5),
                             returnfig=True)

        # Remove the top and right spines
        axes[0].spines['top'].set_visible(False)
        axes[0].spines['right'].set_visible(False)

        # Save the chart to a bytes buffer
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)

        return buf
