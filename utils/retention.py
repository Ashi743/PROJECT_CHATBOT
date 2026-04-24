"""File retention utilities."""
import time
from pathlib import Path


def cleanup_old_files(directory: Path, max_age_days: int = 7) -> int:
    if not directory.exists():
        return 0
    cutoff = time.time() - (max_age_days * 86400)
    removed = 0
    for f in directory.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            try:
                f.unlink()
                removed += 1
            except Exception:
                pass
    return removed
