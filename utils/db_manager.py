import os
import sqlite3
from contextlib import contextmanager

import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "database.db")


def database_exists():
    return os.path.exists(DB_PATH)


@contextmanager
def connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_daily_records(order="DESC"):
    if not database_exists():
        return pd.DataFrame()
    with connection() as conn:
        return pd.read_sql(f"SELECT * FROM daily_records ORDER BY date {order}", conn)


def load_farm_settings():
    if not database_exists():
        return {}
    with connection() as conn:
        settings = pd.read_sql("SELECT * FROM farm_settings", conn)
    return settings.iloc[0].to_dict() if not settings.empty else {}


def load_latest_record():
    if not database_exists():
        return None
    with connection() as conn:
        latest = pd.read_sql(
            "SELECT * FROM daily_records ORDER BY rowid DESC LIMIT 1", conn
        )
    return latest.iloc[0] if not latest.empty else None


def ensure_credit_sales_table():
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS credit_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                buyer_name TEXT,
                trays_sold INTEGER,
                price_per_tray REAL,
                total_amount REAL,
                status TEXT
            )
            """
        )


def load_credit_sales():
    ensure_credit_sales_table()
    with connection() as conn:
        return pd.read_sql("SELECT * FROM credit_sales ORDER BY date DESC", conn)


def append_daily_record(record):
    with connection() as conn:
        pd.DataFrame([record]).to_sql(
            "daily_records", conn, if_exists="append", index=False
        )


def append_credit_sale(record):
    ensure_credit_sales_table()
    with connection() as conn:
        pd.DataFrame([record]).to_sql(
            "credit_sales", conn, if_exists="append", index=False
        )
