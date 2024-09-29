import logging
from pybit.unified_trading import HTTP
from .market import Market

class Exchange:
    def __init__(self, symbol_manager, api_key: str, api_secret: str):
        self.symbol_manager = symbol_manager
        self.session = HTTP(api_key=api_key, api_secret=api_secret, testnet=False)
        self.markets = {}
        self.logger = logging.getLogger(__name__)
        self.update_markets()
        self.logger.info(f"Exchange initialized with {len(self.markets)} markets")

    def update_markets(self):
        symbols = self.symbol_manager.get_symbols()
        for symbol in symbols:
            if symbol not in self.markets:
                self.markets[symbol] = Market(self, symbol)
            self.markets[symbol].update(self.session)
        
        # Remove markets for symbols that no longer exist
        self.markets = {symbol: market for symbol, market in self.markets.items() if symbol in symbols}

    def get_market(self, symbol: str) -> Market:
        return self.markets.get(symbol)

    def get_mark_price(self, symbol: str) -> float:
        market = self.get_market(symbol)
        if market:
            return market.get_mark_price()
        return None

    def get_kline(self, symbol: str, interval: str, limit: int):
        try:
            response = self.session.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            return response['result']['list']
        except Exception as e:
            self.logger.error(f"Error fetching kline data for {symbol}: {str(e)}")
            return []