import psutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def check_app() -> dict:
    try:
        process = psutil.Process()

        memory_pct = process.memory_percent()
        cpu_pct = process.cpu_percent(interval=1)
        thread_count = process.num_threads()

        disk_usage = psutil.disk_usage("/")
        disk_pct = disk_usage.percent

        chat_db = Path("chat_memory.db")
        chat_db_size_mb = 0
        if chat_db.exists():
            chat_db_size_mb = chat_db.stat().st_size / (1024 * 1024)

        status = "[OK]"
        if memory_pct > 80:
            status = "[WARN]"
        elif cpu_pct > 90:
            status = "[WARN]"
        elif disk_pct > 85:
            status = "[WARN]"

        return {
            "app_health": {
                "memory_pct": round(memory_pct, 1),
                "cpu_pct": round(cpu_pct, 1),
                "threads": thread_count,
                "disk_pct": round(disk_pct, 1),
                "chat_db_size_mb": round(chat_db_size_mb, 2),
                "status": status
            }
        }

    except Exception as e:
        logger.error(f"Error checking app health: {e}")
        return {
            "app_health": {
                "status": "[ERROR]",
                "error": str(e)
            }
        }


if __name__ == "__main__":
    import json
    result = check_app()
    print(json.dumps(result, indent=2))
