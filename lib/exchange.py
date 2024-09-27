from pybit.unified_trading import HTTP

from .market import Market


class Exchange:
    def __init__(self, izzy, api_key: str, api_secret: str):
        self.izzy = izzy
        self.session = HTTP(api_key=api_key, api_secret=api_secret, testnet=False)
        self.markets = {}
        self.initialize_markets()

    def initialize_markets(self):
        symbols = self.izzy.get_symbols()
        for symbol in symbols:
            market = Market(self, symbol)
            self.markets[symbol] = market

    def update_markets(self):
        symbols = self.izzy.get_symbols()
        for symbol in symbols:
            market = self.markets.get(symbol)
            if market:
                market.update(self.session)
                mark_price = market.get_mark_price()
                self.izzy.logger.info(f"Updated mark price for {symbol}: {mark_price}")