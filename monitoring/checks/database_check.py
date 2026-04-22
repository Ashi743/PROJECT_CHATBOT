import sqlite3
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def check_databases() -> dict:
    results = {}

    data_dir = Path("data/databases")
    if data_dir.exists():
        for db_file in data_dir.glob("*.db"):
            results.update(_check_database_file(db_file))

    root_db = Path("chat_memory.db")
    if root_db.exists():
        results.update(_check_database_file(root_db))

    return results


def _check_database_file(db_path: Path) -> dict:
    key = db_path.name
    results = {}

    try:
        stat = db_path.stat()
        size_mb = stat.st_size / (1024 * 1024)
        modified_time = datetime.fromtimestamp(stat.st_mtime)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_count = len(tables)

        total_rows = 0
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows += cursor.fetchone()[0]

        conn.close()

        if size_mb > 500:
            status = "[WARN]"
        elif total_rows == 0 and table_count > 0:
            status = "[WARN]"
        else:
            status = "[OK]"

        results[key] = {
            "size_mb": round(size_mb, 2),
            "tables": table_count,
            "rows": total_rows,
            "status": status,
            "modified": modified_time.strftime("%d %b %Y %H:%M")
        }

    except sqlite3.DatabaseError:
        logger.error(f"Database corrupted: {db_path}")
        results[key] = {
            "status": "[ERROR]",
            "error": "Database corrupted"
        }
    except Exception as e:
        logger.error(f"Error checking database {db_path}: {e}")
        results[key] = {
            "status": "[ERROR]",
            "error": str(e)
        }

    return results


if __name__ == "__main__":
    import json
    result = check_databases()
    print(json.dumps(result, indent=2))
