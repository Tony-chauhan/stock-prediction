"""SQLite helpers for the watchlist feature."""
import sqlite3
from contextlib import closing

DB_PATH = 'watchlist.db'


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS watchlist (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   ticker TEXT UNIQUE NOT NULL
               )"""
        )
        conn.commit()


def add_to_watchlist(ticker):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        try:
            conn.execute('INSERT INTO watchlist (ticker) VALUES (?)', (ticker.upper(),))
            conn.commit()
        except sqlite3.IntegrityError:
            pass


def remove_from_watchlist(ticker):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute('DELETE FROM watchlist WHERE ticker = ?', (ticker.upper(),))
        conn.commit()


def get_watchlist():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        rows = conn.execute('SELECT ticker FROM watchlist ORDER BY ticker').fetchall()
        return [r[0] for r in rows]
