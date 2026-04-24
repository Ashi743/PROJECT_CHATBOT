"""Simple per-database SQLite connection pool."""
import sqlite3
import threading
from pathlib import Path

_connections: dict = {}
_lock = threading.Lock()


def get_connection(db_path: str) -> sqlite3.Connection:
    with _lock:
        if db_path not in _connections:
            conn = sqlite3.connect(
                db_path,
                check_same_thread=False,
                timeout=10.0,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            _connections[db_path] = conn
        return _connections[db_path]


def close_all():
    with _lock:
        for conn in _connections.values():
            try:
                conn.close()
            except Exception:
                pass
        _connections.clear()

if __name__ == "__main__":
    c1 = get_connection("data/databases/analytics.db")
    c2 = get_connection("data/databases/analytics.db")
    assert c1 is c2
    close_all()
    print("[OK] pool")
