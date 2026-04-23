"""
Thread-safe runtime flags backed by a JSON file.
Readable from background scheduler threads where st.session_state is unavailable.
"""
import json
import threading
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent / "data" / "runtime_state.json"
_lock = threading.Lock()


def _load() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def set_flag(name: str, value) -> None:
    with _lock:
        state = _load()
        state[name] = value
        _save(state)


def get_flag(name: str, default=None):
    with _lock:
        return _load().get(name, default)


if __name__ == "__main__":
    set_flag("report_paused", True)
    assert get_flag("report_paused") is True
    set_flag("report_paused", False)
    assert get_flag("report_paused") is False
    print("[OK] runtime_state")
