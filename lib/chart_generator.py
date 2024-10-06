from .chart import Chart


class ChartGenerator:
    def __init__(self):
        pass

    def generate_candlestick_chart(self, candles, title: str) -> Chart:
        return Chart(candles, title)
