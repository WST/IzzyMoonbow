from pybit.unified_trading import HTTP
from sqlalchemy.orm import sessionmaker
from .models import Symbol
from .market import Market

class Exchange:
    def __init__(self, izzy, api_key: str, api_secret: str):
        self.izzy = izzy
        self.session = HTTP(api_key=api_key, api_secret=api_secret, testnet=False)
        self.markets = {}
        self.initialize_markets()
        self.db_session = sessionmaker(bind=self.izzy.engine)()

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
                if mark_price is not None:
                    self.update_symbol_price(symbol, mark_price)

    def update_symbol_price(self, symbol: str, price: float):
        db_symbol = self.db_session.query(Symbol).get(symbol)
        if db_symbol:
            db_symbol.last_mark_price = price
            self.db_session.commit()
        else:
            print(f"Symbol {symbol} not found in database")

    def __del__(self):
        self.db_session.close()