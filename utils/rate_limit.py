"""Simple token-bucket rate limiter, per tool name."""
import time
import threading
from collections import defaultdict

_last_call: dict = defaultdict(float)
_lock = threading.Lock()


def rate_limit(key: str, min_interval_seconds: float) -> None:
    """Block until min_interval_seconds has passed since last call with this key."""
    with _lock:
        now = time.time()
        wait = (_last_call[key] + min_interval_seconds) - now
        if wait > 0:
            time.sleep(wait)
        _last_call[key] = time.time()
