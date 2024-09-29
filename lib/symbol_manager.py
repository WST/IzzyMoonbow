import logging
from lib.models import Symbol

class SymbolManager:
    def __init__(self, session_maker):
        self.Session = session_maker
        self.logger = logging.getLogger(__name__)

    def get_symbols(self) -> list:
        with self.Session() as session:
            symbols = session.query(Symbol.symbol).all()
            return [symbol[0] for symbol in symbols]

    def add_symbol(self, symbol: str, icon_class: str):
        with self.Session() as session:
            existing_symbol = session.query(Symbol).filter_by(symbol=symbol).first()
            if not existing_symbol:
                new_symbol = Symbol(symbol=symbol, icon_class=icon_class)
                session.add(new_symbol)
                session.commit()

    def remove_symbol(self, symbol: str):
        with self.Session() as session:
            existing_symbol = session.query(Symbol).filter_by(symbol=symbol).first()
            if existing_symbol:
                session.delete(existing_symbol)
                session.commit()