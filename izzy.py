#!/usr/bin/env python3

from lib.izzybot import IzzyBot
from lib.config import Config
from lib.db_utils import wait_for_db

if __name__ == "__main__":
    config = Config()
    config.validate()  # Check if all required environment variables are set
    engine = wait_for_db(config.get_db_url())
    izzy = IzzyBot(config, engine)
    izzy.run()
