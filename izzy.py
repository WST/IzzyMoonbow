#!/usr/bin/env python3

import settings
from lib.izzybot import IzzyBot
from lib.db_utils import wait_for_db

if __name__ == "__main__":
    db_url = f"mysql+pymysql://{settings.DB_CONFIG['user']}:{settings.DB_CONFIG['password']}@{settings.DB_CONFIG['host']}/{settings.DB_CONFIG['database']}"
    engine = wait_for_db(db_url)
    izzy = IzzyBot(settings, engine)
    izzy.run()
