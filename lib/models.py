from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    nickname = Column(String(50))
    is_premium = Column(Boolean)
    last_seen = Column(Integer)

class ChatGroup(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True)
    title = Column(String(100))

class Symbol(Base):
    __tablename__ = 'symbols'
    symbol = Column(String(20), primary_key=True)
    icon_class = Column(String(50), nullable=False)
    last_mark_price = Column(Float)
    monitor_oi = Column(Boolean, default=False)
    oi_threshold = Column(Float, default=0.0)
    monitor_fvg = Column(Boolean, default=False)
    fvg_threshold = Column(Float, default=0.0)

    def __repr__(self):
        return f'<Symbol {self.symbol}>'

# Add this line at the end of the file to export Base
__all__ = ['Base', 'User', 'ChatGroup', 'Symbol']