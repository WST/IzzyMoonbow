import logging
import queue
import threading

import numpy as np
import pandas as pd
from pybit.unified_trading import HTTP

from .exchange_updater import ExchangeUpdater
from .market import Market


class Exchange:
    def __init__(self, symbol_manager, api_key: str, api_secret: str):
        self.symbol_manager = symbol_manager
        self.session = HTTP(api_key=api_key, api_secret=api_secret, testnet=False)
        self.markets = {}
        self.logger = logging.getLogger(__name__)
        self.market_data_lock = threading.Lock()
        self.updater = ExchangeUpdater(self)
        self.updater.start()
        self.logger.info(f"Exchange initialized with {len(self.markets)} markets")
        self.logger.info("ExchangeUpdater thread started")

    def update_markets(self):
        try:
            new_data = self.updater.data_queue.get_nowait()
            with self.market_data_lock:
                self.process_new_market_data(new_data)
            self.logger.info("Markets updated with new data")
        except queue.Empty:
            self.logger.debug("No new market data available")

    def process_new_market_data(self, new_data):
        symbols = self.symbol_manager.get_symbols()
        for symbol, data in new_data.items():
            if symbol in symbols:
                if symbol not in self.markets:
                    self.markets[symbol] = Market(self, symbol)
                self.markets[symbol].update_from_data(data)

        self.markets = {symbol: market for symbol, market in self.markets.items() if symbol in symbols}

    def get_market(self, symbol: str) -> Market:
        with self.market_data_lock:
            return self.markets.get(symbol)

    def fetch_all_market_data(self):
        symbols = self.symbol_manager.get_symbols()
        market_data = {}
        for symbol in symbols:
            try:
                kline_15m = self.get_kline(symbol, interval="15", limit=100)
                kline_4h = self.get_kline(symbol, interval="240", limit=100)
                market_data[symbol] = {
                    '15m': kline_15m,
                    '4h': kline_4h
                }
            except Exception as e:
                self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return market_data

    def get_kline(self, symbol: str, interval: str, limit: int):
        try:
            klines = self.session.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            kline_data = klines['result']['list']

            oiIntervalTime = '15min' if interval == '15' else '4h'
            response = self.session.get_open_interest(
                category="linear",
                symbol=symbol,
                intervalTime=oiIntervalTime,
                limit=limit
            )
            oi_data = response['result']['list']

            df = pd.DataFrame(kline_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(np.int64), unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.astype(float)
            df = df.sort_index()

            for item in oi_data:
                # {'openInterest': '4144631.00000000', 'timestamp': '1726617600000'}
                timestamp = pd.to_datetime(float(item['timestamp']), unit='ms')
                open_interest = float(item['openInterest'])
                df.loc[timestamp, 'open_interest'] = open_interest

            return df
        except Exception as e:
            self.logger.error(f"Error fetching kline data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def stop(self):
        self.logger.info("Stopping ExchangeUpdater thread")
        self.updater.stop()
        self.updater.join()
        self.logger.info("ExchangeUpdater thread stopped")
