import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError


def wait_for_db(db_url, max_retries=30, retry_interval=2):
    retries = 0
    while retries < max_retries:
        try:
            engine = create_engine(db_url)
            engine.connect()
            print("Successfully connected to the database")
            return engine
        except OperationalError:
            retries += 1
            print(
                f"Unable to connect to the database. Retrying in {retry_interval} seconds... (Attempt {retries}/{max_retries})")
            time.sleep(retry_interval)

    raise Exception("Max retries reached. Unable to connect to the database.")
