import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

STATE_FILE = Path("data/monitoring_state.json")


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load state file: {e}")
    return {"last_files": {}}


def _save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save state file: {e}")


def check_files() -> dict:
    results = {}
    current_state = _load_state()
    last_files = current_state.get("last_files", {})
    current_files = {}

    data_dir = Path("data")
    if not data_dir.exists():
        return {"status": "[WARN]", "message": "data/ directory not found"}

    now = datetime.now()

    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            file_key = str(file_path.relative_to(data_dir))
            current_files[file_key] = True

            try:
                stat = file_path.stat()
                size_kb = stat.st_size / 1024
                modified_time = datetime.fromtimestamp(stat.st_mtime)
                age_hours = (now - modified_time).total_seconds() / 3600

                readable = True
                try:
                    with open(file_path, "rb") as f:
                        f.read(1)
                except Exception:
                    readable = False

                if not readable:
                    status = "[ERROR]"
                elif age_hours > 48:
                    status = "[STALE]"
                elif size_kb < 1:
                    status = "[WARN]"
                else:
                    status = "[OK]"

                was_seen = file_key in last_files
                file_status = "[NEW]" if not was_seen else status

                results[file_key] = {
                    "size_kb": round(size_kb, 2),
                    "age_hours": round(age_hours, 2),
                    "status": file_status,
                    "readable": readable,
                    "modified": modified_time.strftime("%d %b %Y %H:%M")
                }

            except Exception as e:
                logger.error(f"Error checking file {file_path}: {e}")
                results[file_key] = {
                    "status": "[ERROR]",
                    "error": str(e)
                }

    for file_key in last_files:
        if file_key not in current_files:
            results[file_key] = {
                "status": "[MISSING]"
            }

    current_state["last_files"] = current_files
    _save_state(current_state)

    return results


if __name__ == "__main__":
    import json
    result = check_files()
    print(json.dumps(result, indent=2))
