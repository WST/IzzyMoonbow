import os
import logging

class Config:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Config")
        self.TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.BYBIT_API_KEY = os.environ.get('BYBIT_API_KEY')
        self.BYBIT_API_SECRET = os.environ.get('BYBIT_API_SECRET')
        
        # Database configuration
        self.DB_HOST = os.environ.get('DB_HOST', 'localhost')
        self.DB_USER = os.environ.get('DB_USER', 'root')
        self.DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
        self.DB_NAME = os.environ.get('DB_NAME', 'izzy_db')
        
        self.logger.info("Config initialized successfully")

    def get_db_url(self):
        url = f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"
        self.logger.debug(f"Generated database URL: {url}")
        return url

    def validate(self):
        self.logger.info("Validating config")
        required_vars = ['TELEGRAM_BOT_TOKEN', 'BYBIT_API_KEY', 'BYBIT_API_SECRET']
        missing_vars = [var for var in required_vars if getattr(self, var) is None]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        self.logger.info("Config validation completed")
