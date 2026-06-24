"""SQLite helpers for the watchlist feature with connection pooling and race condition fixes."""
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from config import config

DB_PATH = Path(config.BASE_DIR) / 'watchlist.db'
_local = threading.local()


@contextmanager
def get_conn():
    """Thread-local connection with row factory."""
    if not hasattr(_local, 'conn') or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute('PRAGMA journal_mode=WAL')
        _local.conn.execute('PRAGMA busy_timeout=5000')
    try:
        yield _local.conn
    except Exception:
        _local.conn.rollback()
        raise


def init_db():
    """Initialize database schema."""
    with get_conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS watchlist (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   ticker TEXT UNIQUE NOT NULL,
                   added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_watchlist_ticker 
               ON watchlist(ticker)"""
        )
        conn.commit()


def add_to_watchlist(ticker: str) -> bool:
    """Add ticker to watchlist. Returns True if added, False if already exists."""
    ticker = ticker.upper().strip()
    if not ticker:
        return False
    with get_conn() as conn:
        try:
            conn.execute(
                'INSERT INTO watchlist (ticker) VALUES (?)', 
                (ticker,)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def remove_from_watchlist(ticker: str) -> bool:
    """Remove ticker from watchlist. Returns True if removed."""
    ticker = ticker.upper().strip()
    with get_conn() as conn:
        cursor = conn.execute(
            'DELETE FROM watchlist WHERE ticker = ?', 
            (ticker,)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_watchlist() -> list[str]:
    """Get all tickers in watchlist."""
    with get_conn() as conn:
        rows = conn.execute('SELECT ticker FROM watchlist ORDER BY ticker').fetchall()
        return [r['ticker'] for r in rows]


def is_in_watchlist(ticker: str) -> bool:
    """Check if ticker is in watchlist."""
    ticker = ticker.upper().strip()
    with get_conn() as conn:
        row = conn.execute(
            'SELECT 1 FROM watchlist WHERE ticker = ?', 
            (ticker,)
        ).fetchone()
        return row is not None


def get_watchlist_count() -> int:
    """Get count of watchlist items."""
    with get_conn() as conn:
        row = conn.execute('SELECT COUNT(*) as cnt FROM watchlist').fetchone()
        return row['cnt'] if row else 0


def close_connections():
    """Close thread-local connections."""
    if hasattr(_local, 'conn') and _local.conn:
        _local.conn.close()
        _local.conn = None