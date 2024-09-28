#!/usr/bin/env python3

from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.models import Base, Symbol
from settings import DB_CONFIG, SECRET_KEY
import click

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Configure MySQL connection
db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)

@app.route('/api/glitter.jsp', methods=['GET'])
def api_handler():
    call = request.args.get('call')
    if call == 'symbols':
        return get_symbols()
    elif call == 'symbol':
        symbol = request.args.get('symbol')
        return get_symbol(symbol)
    else:
        return jsonify({'error': 'Invalid call parameter'}), 400

def get_symbols():
    session = Session()
    try:
        symbols = session.query(Symbol).all()
        return jsonify([{
            'symbol': symbol.symbol,
            'icon_class': symbol.icon_class,
            'last_mark_price': symbol.last_mark_price
        } for symbol in symbols])
    finally:
        session.close()

def get_symbol(symbol_name):
    session = Session()
    try:
        symbol = session.get(Symbol, symbol_name)
        if symbol:
            return jsonify({
                'symbol': symbol.symbol,
                'icon_class': symbol.icon_class,
                'last_mark_price': symbol.last_mark_price
            })
        else:
            return jsonify({'error': 'Symbol not found'}), 404
    finally:
        session.close()

def insert_initial_symbols():
    session = Session()
    try:
        symbols = [
            ('BTCUSDT', 'fab fa-bitcoin'),
            ('ETHUSDT', 'fab fa-ethereum'),
            ('SOLUSDT', 'fas fa-sun'),
            ('XMRUSDT', 'fas fa-user-secret'),
            ('AVAXUSDT', 'fas fa-mountain'),
            ('POPCATUSDT', 'fas fa-cat'),
            ('SUIUSDT', 'fas fa-cube'),
            ('WIFUSDT', 'fas fa-wifi')
        ]
        
        for symbol_data in symbols:
            existing_symbol = session.get(Symbol, symbol_data[0])
            if not existing_symbol:
                new_symbol = Symbol(symbol=symbol_data[0], icon_class=symbol_data[1])
                session.add(new_symbol)
        
        session.commit()
    finally:
        session.close()

@app.cli.command("init-db")
def initialize_database():
    """Initialize the database."""
    Base.metadata.create_all(engine)
    click.echo('Initialized the database.')

@app.cli.command("insert-symbols")
def insert_symbols_command():
    """Insert initial symbols."""
    insert_initial_symbols()
    click.echo('Inserted initial symbols.')

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    insert_initial_symbols()
    app.run(debug=True, host='0.0.0.0', port=5000)