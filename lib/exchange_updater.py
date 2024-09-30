import threading
import queue
import time
import logging

class ExchangeUpdater(threading.Thread):
    def __init__(self, exchange, update_interval=60):
        super().__init__()
        self.exchange = exchange
        self.update_interval = update_interval
        self.stop_event = threading.Event()
        self.data_queue = queue.Queue()
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("ExchangeUpdater thread started")
        while not self.stop_event.is_set():
            try:
                new_data = self.exchange.fetch_all_market_data()
                self.data_queue.put(new_data)
                time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"Error updating markets: {e}")
                time.sleep(5)  # Wait a bit before retrying

    def stop(self):
        self.logger.info("Stopping ExchangeUpdater thread")
        self.stop_event.set()