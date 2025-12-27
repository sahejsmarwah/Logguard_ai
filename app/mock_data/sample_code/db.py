import os
import psycopg2

def connect():
    db_url = os.getenv("DB_URL")
    # BUG: No validation or retry
    return psycopg2.connect(db_url)
