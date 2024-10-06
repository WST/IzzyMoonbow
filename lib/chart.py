import logging

import matplotlib.pyplot as plt
import mplfinance as mpf
from io import BytesIO
from typing import List
from .fvg import FVG
import pandas as pd


class Chart:
    def __init__(self, candles, title: str):
        self.candles = candles
        self.df = pd.DataFrame([c.data for c in candles])
        self.title = title
        self._plot_candlesticks()

    def _plot_candlesticks(self):
        # Define custom style
        mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
        style = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', gridaxis='both')

        ap = mpf.make_addplot(self.df['open_interest'], panel=1, type='line', ylabel='ОИ')

        # Plot candlesticks
        self.fig, self.axes = mpf.plot(
            self.df,
            type='candle',
            style=style,
            title=self.title,
            ylabel='Цена, USDT',
            volume=False,
            figsize=(10, 6),
            returnfig=True,
            addplot=ap
        )

        # Get the main price axis
        self.ax = self.axes[0]

        # Customize grid
        self.ax.grid(True, linestyle=':', alpha=0.6)
        self.ax.set_axisbelow(True)  # Place grid behind other elements

        # Customize x-axis
        self.ax.tick_params(axis='x', rotation=0)

        # Adjust the layout
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.8, bottom=0.05)

    def draw_range(self, start_price: float, end_price: float, color: str, alpha: float = 0.3):
        self.ax.axhspan(start_price, end_price, facecolor=color, alpha=alpha)

    def draw_fvg(self, fvg: FVG):
        color = 'green' if fvg.is_bullish() else 'red'
        self.draw_range(fvg.get_lower_bound(), fvg.get_upper_bound(), color, 0.1)

    def draw_fvgs(self, fvgs: List[FVG]):
        for fvg in fvgs:
            self.draw_fvg(fvg)

    def highlight_price_ranges(self, low_threshold, high_threshold):
        if low_threshold:
            self.ax.axhspan(self.df['low'].min(), low_threshold, facecolor='lightcoral', alpha=0.3)
        if high_threshold:
            self.ax.axhspan(high_threshold, self.df['high'].max(), facecolor='lightgreen', alpha=0.3)

    def save(self) -> BytesIO:
        buf = BytesIO()
        self.fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close(self.fig)
        return buf
