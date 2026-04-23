# Production Fixes — Claude Code Prompt

**Scope:** Fix all CRITICAL, HIGH, and MEDIUM production-readiness issues **before** starting C-RAG, Memory, Frontend redesign, or Dockerization.

**Branch strategy:** Do NOT stay on `feat/nlp-monitoring`. Create a new branch `feat/production-fixes` off `main` so these fixes are isolated, reviewable, and independent of the nlp-monitoring work.

---

## How to use this prompt

Paste this entire document into Claude Code. Work through fixes in order. Each fix has:
- **Files** to touch
- **Change** description
- **Test** command
- **Commit** message (Conventional Commits)

Rules from `CLAUDE.md` apply throughout:
- No emojis anywhere (Windows cp1252)
- Use `[OK]`, `[ALERT]`, `[DOWN]`, `[WARN]`, `[ERROR]`, `[STALE]`
- Test each file independently before committing
- One logical fix per commit
- Never commit broken code

Read `.claude/specs/INDEX.md` before starting. Read any tool-specific spec before touching that tool.

---

## Phase 0: Branch Setup

```bash
git checkout main
git pull origin main
git checkout -b feat/production-fixes
```

Confirm you're on `feat/production-fixes` before any changes.

---

## Phase 1: CRITICAL Fixes (deploy blockers)

### Fix 1.1 — Remove broken langchain.messages import (BACKEND + ALL TESTS)

**Files:**
- `backend.py` (line 1)
- `tool_testing/test_all_tools.py`
- `tool_testing/test_backend_debug.py`
- `tool_testing/test_backend_integration.py`
- `tool_testing/test_calculator_backend.py`
- `tool_testing/test_new_tools.py`
- `tool_testing/test_web_search_backend.py`

**Change:**
Replace every occurrence of:
```python
from langchain.messages import HumanMessage
```
with:
```python
from langchain_core.messages import HumanMessage
```

In `backend.py` specifically, remove the duplicate import on line 1 entirely if line 3 already has the correct `langchain_core.messages` import.

**Test:**
```bash
python -c "from backend import chatbot; print('[OK] backend imports')"
python tool_testing/test_all_tools.py
```

**Commit:**
```
fix: replace deprecated langchain.messages with langchain_core.messages
```

---

### Fix 1.2 — Remove hardcoded email from Gmail alert

**File:** `monitoring/alerts/gmail_alert.py`

**Change:**
Replace the hardcoded `"ashishdangwal97@gmail.com"` with environment variable:

```python
import os
GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT")

def send_gmail_report(results: dict, subject: str = None):
    if not GMAIL_RECIPIENT:
        return {"status": "error", "message": "GMAIL_RECIPIENT not set in .env"}

    result = send_email.invoke({
        "to": GMAIL_RECIPIENT,
        ...
    })
```

Add `GMAIL_RECIPIENT=your_email@gmail.com` to `.env.example` (create if missing).

**Test:**
```bash
python -c "from monitoring.alerts.gmail_alert import send_gmail_report; print('[OK] import')"
```

**Commit:**
```
fix(monitoring): load gmail recipient from env, remove hardcoded address
```

---

### Fix 1.3 — Add HITL to monitor_tool

**File:** `tools/monitor_tool.py`

**Change:**
`start_monitoring` must not spawn a background thread without user confirmation. Modify the tool to return a pending-approval payload on first call, then actually start on approved second call. Use session-state keyed pattern consistent with `subgraphs/csv_analyst_subgraph.py`.

Minimal approach — add `confirm: bool = False` parameter:
```python
@tool
def start_monitoring(commodity: str, interval_minutes: int = 30, confirm: bool = False) -> str:
    """
    Start monitoring a commodity in background thread.
    First call returns confirmation request; set confirm=True to actually start.
    """
    if not confirm:
        return (
            f"[CONFIRM] Ready to start monitoring {commodity} every {interval_minutes} min. "
            f"This will spawn a background thread. "
            f"Call again with confirm=True to proceed."
        )
    # ... existing start logic ...
```

Update `tools/monitor-spec.md` and `.claude/specs/tools/monitor-spec.md` to document the HITL requirement.

**Test:**
```bash
python -c "
from tools.monitor_tool import start_monitoring
print(start_monitoring.invoke({'commodity': 'wheat'}))
print(start_monitoring.invoke({'commodity': 'wheat', 'confirm': True}))
"
```

**Commit:**
```
feat(monitor): require confirm=True before spawning monitor thread
```

---

### Fix 1.4 — Move report_paused flag out of session_state

**Files:**
- `frontend.py` (scheduled_job closure)
- New: `utils/runtime_state.py`

**Change:**
`st.session_state` is per-session and unreachable from background threads. Scheduled jobs silently fail once the browser tab closes.

Create `utils/runtime_state.py`:
```python
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
```

In `frontend.py`, update `scheduled_job()` to use `get_flag("report_paused", False)` instead of `st.session_state.get("report_paused")`. The pause button writes via `set_flag("report_paused", True)`. Initialization still populates session_state for UI reads, but the scheduled job never touches session_state.

**Test:**
```bash
python -c "
from utils.runtime_state import set_flag, get_flag
set_flag('report_paused', True)
assert get_flag('report_paused') is True
set_flag('report_paused', False)
assert get_flag('report_paused') is False
print('[OK] runtime_state')
"
```

**Commit:**
```
fix(frontend): move report_paused flag to file-backed runtime state
```

---

### Fix 1.5 — Load CSV once in csv_analyst_subgraph

**File:** `subgraphs/csv_analyst_subgraph.py`

**Change:**
Current code re-reads `pd.read_csv(state["file_path"])` inside each node (4x). Load once in `load_node` and pass the DataFrame through state.

Add a `dataframe` field to the state TypedDict:
```python
from typing import TypedDict, Optional
import pandas as pd

class CSVAnalystState(TypedDict):
    file_path: str
    dataset_name: str
    dataframe: Optional[pd.DataFrame]  # NEW
    operation: str
    result: str
    ...
```

In `load_node`:
```python
def load_node(state: CSVAnalystState) -> CSVAnalystState:
    df = pd.read_csv(state["file_path"])
    state["dataframe"] = df
    return state
```

All downstream nodes read `state["dataframe"]` instead of re-reading the file.

**Test:**
```bash
python subgraphs/csv_analyst_subgraph.py
```

**Commit:**
```
perf(csv_analyst): load dataframe once in load_node, share via state
```

---

### Fix 1.6 — Thread cleanup on Streamlit reruns

**File:** `frontend.py`

**Change:**
Streamlit reruns the script on every interaction. Every "Start Monitor" click spawns a new thread; old threads leak until process exit.

Before starting a new thread, stop the previous one:
```python
if start_btn:
    # Stop previous thread if exists
    prev_thread = st.session_state.get("monitor_thread")
    if prev_thread is not None and prev_thread.is_alive():
        # Signal stop via runtime flag
        from utils.runtime_state import set_flag
        set_flag("monitor_stop_requested", True)
        prev_thread.join(timeout=5)
        set_flag("monitor_stop_requested", False)

    # ... existing start logic ...
```

Inside the scheduler loop in `monitoring/runner.py` `start_background()`, check the flag periodically:
```python
from utils.runtime_state import get_flag

def thread_loop():
    while not get_flag("monitor_stop_requested", False):
        schedule.run_pending()
        time.sleep(60)
```

**Test:** Manual — start monitor twice, confirm only one thread is alive via `threading.enumerate()`.

**Commit:**
```
fix(frontend): stop previous monitor thread before spawning new one
```

---

### Fix 1.7 — Graceful shutdown for SqliteSaver

**File:** `backend.py`

**Change:**
SqliteSaver's connection never closes. SIGTERM during write = corrupt DB. Register an atexit handler and a SIGTERM handler.

```python
import atexit
import signal
import sqlite3

# After creating checkpointer:
def _graceful_shutdown(*args):
    try:
        if hasattr(checkpointer, "conn") and checkpointer.conn is not None:
            checkpointer.conn.commit()
            checkpointer.conn.close()
    except Exception as e:
        print(f"[ERROR] Shutdown error: {e}")

atexit.register(_graceful_shutdown)
signal.signal(signal.SIGTERM, _graceful_shutdown)
# SIGINT on Windows is handled by atexit
```

**Test:**
```bash
python -c "
import backend
import signal, os
# Simulate shutdown
backend._graceful_shutdown()
print('[OK] graceful shutdown')
"
```

**Commit:**
```
fix(backend): register atexit + SIGTERM handlers for SqliteSaver cleanup
```

---

## Phase 2: HIGH Priority Fixes

### Fix 2.1 — SQLite connection pooling

**File:** `tools/sql_analysis_tool.py`, `monitoring/checks/database_check.py`

**Change:**
Create `utils/db_pool.py`:
```python
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
```

Replace all `sqlite3.connect(...)` calls in `sql_analysis_tool.py` and `database_check.py` with `get_connection(...)`. Register `close_all()` in the atexit handler from Fix 1.7.

**Test:**
```bash
python -c "
from utils.db_pool import get_connection, close_all
c1 = get_connection('data/databases/analytics.db')
c2 = get_connection('data/databases/analytics.db')
assert c1 is c2
close_all()
print('[OK] pool')
"
```

**Commit:**
```
refactor: centralize sqlite connections through utils.db_pool
```

---

### Fix 2.2 — ChromaDB path inconsistency

**Files:**
- `tools/csv_ingest_tool.py`
- `monitoring/checks/chromadb_check.py`

**Change:**
Pick one canonical path and use it everywhere. Per specs, it should be `data/chroma_db/`.

Create `utils/paths.py`:
```python
"""Central path constants."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
DATABASES_DIR = DATA_DIR / "databases"
CHROMA_DIR = DATA_DIR / "chroma_db"
PLOTS_DIR = DATA_DIR / "plots"

for d in (UPLOADS_DIR, DATABASES_DIR, CHROMA_DIR, PLOTS_DIR):
    d.mkdir(parents=True, exist_ok=True)
```

Refactor all modules to import paths from `utils.paths`. No more ad-hoc `Path(...)` constructions for these directories.

**Test:**
```bash
python -c "
from utils.paths import CHROMA_DIR, PLOTS_DIR, UPLOADS_DIR
print(f'[OK] CHROMA_DIR={CHROMA_DIR}')
assert CHROMA_DIR.name == 'chroma_db'
assert CHROMA_DIR.parent.name == 'data'
"
```

**Commit:**
```
refactor: centralize data paths in utils.paths, fix chromadb location
```

---

### Fix 2.3 — ChromaDB client as lazy singleton

**File:** `tools/csv_ingest_tool.py` (and anywhere else with module-level `chromadb.PersistentClient`)

**Change:**
Remove module-level client creation. Create `utils/chroma.py`:
```python
"""Lazy ChromaDB client."""
import threading
import chromadb
from utils.paths import CHROMA_DIR

_client = None
_lock = threading.Lock()


def get_client():
    global _client
    with _lock:
        if _client is None:
            _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        return _client
```

Refactor callers to `from utils.chroma import get_client` and call `get_client()` where needed.

**Commit:**
```
refactor: lazy-init chromadb client in utils.chroma
```

---

### Fix 2.4 — Plots retention policy

**File:** New: `utils/retention.py`, called from `monitoring/runner.py`

**Change:**
`data/plots/` grows forever. Add a cleanup that runs daily and deletes plots older than 7 days.

```python
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
```

In `monitoring/runner.py` `start()`:
```python
from utils.retention import cleanup_old_files
from utils.paths import PLOTS_DIR

def daily_cleanup_job():
    removed = cleanup_old_files(PLOTS_DIR, max_age_days=7)
    logger.info(f"[OK] Cleaned up {removed} old plots")

schedule.every().day.at("03:00").do(daily_cleanup_job)
```

**Commit:**
```
feat(monitoring): add daily plots retention cleanup (7 day)
```

---

### Fix 2.5 — Fix dual-LLM cost optimization

**File:** `backend.py`

**Change:**
`_is_analysis_result()` currently only triggers on ToolMessage. User questions about analysis get `gpt-4o-mini` which gives worse interpretations.

Two options — pick one:

**Option A (simpler):** Drop dual-LLM entirely. Use one model.

**Option B (correct):** Also route to `gpt-4o` when the user's last message contains analysis keywords:
```python
ANALYSIS_KEYWORDS = {
    "analyze", "interpret", "explain", "why", "insight",
    "trend", "correlate", "compare", "anomaly", "outlier"
}

def _requires_analysis_llm(messages) -> bool:
    last = messages[-1]
    if isinstance(last, ToolMessage):
        return _is_analysis_result(last)
    if isinstance(last, HumanMessage):
        text = (last.content or "").lower()
        return any(kw in text for kw in ANALYSIS_KEYWORDS)
    return False
```

Pick Option A unless you need the cost optimization. Document the choice.

**Commit:**
```
fix(backend): correct dual-llm routing logic (or simplify to single model)
```

---

### Fix 2.6 — Remove os.chdir from gmail_toolkit

**File:** `gmail_toolkit/gmail.py`

**Change:**
`os.chdir()` is a process-global side effect; racy with monitor threads.

Replace the `os.chdir` dance with environment variables that the Google library respects, or pass credentials path explicitly to `GmailToolkit(credentials_path=...)` if the API supports it. If not, use a context manager and a lock:

```python
import threading
from contextlib import contextmanager

_cwd_lock = threading.Lock()

@contextmanager
def _chdir(path):
    with _cwd_lock:
        prev = os.getcwd()
        try:
            os.chdir(path)
            yield
        finally:
            os.chdir(prev)
```

Wrap the toolkit init:
```python
with _chdir(GMAIL_TOOLKIT_DIR):
    toolkit = GmailToolkit()
    gmail_tools = toolkit.get_tools()
```

Also remove the dead fallback path logic (`fallback_path = os.path.join(os.path.dirname(GMAIL_TOOLKIT_DIR), "gmail_toolkit", "credentials.json")` — this resolves to the same directory).

Replace `print()` error reporting with `logging`.

**Test:**
```bash
python gmail_toolkit/gmail.py
```

**Commit:**
```
fix(gmail): lock-guard chdir, remove dead fallback path, use logging
```

---

### Fix 2.7 — Rate limiting on external tools

**File:** New: `utils/rate_limit.py`, applied to `web_search`, `stock`, `commodity`, `calendarific`

**Change:**
```python
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
```

Apply in tools:
```python
# tools/web_search_tool.py
from utils.rate_limit import rate_limit

@tool
def web_search(query: str, num_results: int = 5) -> str:
    rate_limit("web_search", 2.0)  # max 1 call / 2 sec
    ...
```

Suggested intervals:
- `web_search`: 2.0s
- `stock`: 1.0s
- `commodity`: 1.0s
- `calendarific`: 1.0s

**Commit:**
```
feat(tools): add rate limiting to web_search, stock, commodity, calendarific
```

---

### Fix 2.8 — Replace silent except:pass with logging

**Files:** grep for `except Exception:\n *pass` and `except:\n *pass` across the project

**Change:**
Set up central logging config in `utils/logging_config.py`:
```python
"""Central logging setup."""
import logging
import sys
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "logs" / "app.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
```

Call `setup_logging()` once in `frontend.py` and `monitor.py` at startup.

Replace every silent except:
```python
# BEFORE
except Exception:
    pass

# AFTER
import logging
logger = logging.getLogger(__name__)
...
except Exception as e:
    logger.warning(f"Non-fatal error in {context}: {e}")
```

Add `logs/` to `.gitignore`.

**Commit:**
```
chore: replace silent exceptions with logging throughout
```

---

## Phase 3: MEDIUM Priority Fixes

### Fix 3.1 — SQL injection protection

**File:** `tools/sql_analysis_tool.py`

**Change:**
`analyze_sql` uses f-string with LLM-provided `table_name`. Whitelist against `sqlite_master`:

```python
def _validate_table_name(conn, table_name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cur.fetchone() is not None


# In count/describe/sample operations:
if not _validate_table_name(conn, table_name):
    return f"[ERROR] Unknown table: {table_name}"

# Now safe to use in f-string since we verified it exists
cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
```

Same for `describe`, `sample`, and any other table-name-in-f-string spot.

**Commit:**
```
fix(sql): whitelist table names against sqlite_master before interpolation
```

---

### Fix 3.2 — Move sample data out of code

**Files:**
- New: `data/sample_init.sql`
- `tools/sql_analysis_tool.py`

**Change:**
Extract the hardcoded sample-data INSERTs from `_initialize_sample_database()` into `data/sample_init.sql`. Load it:

```python
from utils.paths import DATA_DIR

def _initialize_sample_database(conn):
    sql_file = DATA_DIR / "sample_init.sql"
    if sql_file.exists():
        conn.executescript(sql_file.read_text(encoding="utf-8"))
```

**Commit:**
```
refactor(sql): move sample seed data to data/sample_init.sql
```

---

### Fix 3.3 — Dispatch pattern for analyze_data

**File:** `tools/csv_analysis_tool.py`

**Change:**
Replace the giant if/elif chain with a dispatcher dict. Split each operation into its own `_op_*` function:

```python
def _op_head(df, params): ...
def _op_describe(df, params): ...
def _op_groupby_sum(df, params): ...
# ...

OPERATIONS = {
    "head": _op_head,
    "describe": _op_describe,
    "groupby_sum": _op_groupby_sum,
    # ...
}

@tool
def analyze_data(dataset_name: str, operation: str, params: str = "") -> str:
    df = _load_dataframe(dataset_name)
    if operation not in OPERATIONS:
        return f"[ERROR] Unknown operation: {operation}. Valid: {list(OPERATIONS)}"
    return OPERATIONS[operation](df, params)
```

**Commit:**
```
refactor(csv_analyst): dispatcher pattern for analyze_data operations
```

---

### Fix 3.4 — Standardize error format

**All tool files**

**Change:**
Search for every error return across tools and normalize to `[ERROR] message`. Banned strings:
- `"Error: "`
- `"Failed: "`
- `f"Error executing {name}: "`

Replace with:
- `"[ERROR] "` prefix

Also use `[OK]`, `[WARN]`, `[ALERT]` consistently per CLAUDE.md status codes.

**Commit:**
```
chore: standardize tool error messages to [ERROR]/[WARN]/[OK] format
```

---

### Fix 3.5 — Fix subgraphs/__init__.py None imports

**File:** `subgraphs/__init__.py`

**Change:**
Stop exporting late-bound objects that are `None` at import time. Either:

**Option A:** Make each subgraph self-contained (no late binding).

**Option B:** Export builder functions instead of built graphs:
```python
# subgraphs/__init__.py
from .rag_ingestion_subgraph import build_rag_ingestion_graph
from .csv_analyst_subgraph import build_csv_analyst_graph
from .sql_analyst_subgraph import build_sql_analyst_graph

__all__ = [
    "build_rag_ingestion_graph",
    "build_csv_analyst_graph",
    "build_sql_analyst_graph",
]
```

Callers do `build_rag_ingestion_graph()` when they need it.

**Commit:**
```
refactor(subgraphs): export builders instead of late-bound None objects
```

---

### Fix 3.6 — Remove dead conditional in sql_analyst_subgraph

**File:** `subgraphs/sql_analyst_subgraph.py`

**Change:**
`should_continue` always returns `"end"`. The `"continue" → execute` edge is unreachable. Remove the dead conditional edge, or implement actual retry logic.

If unclear which, default to removing:
```python
# Remove this:
graph.add_conditional_edges("result", should_continue, {"continue": "execute", "end": END})
# Use this:
graph.add_edge("result", END)
```

**Commit:**
```
fix(sql_analyst): remove unreachable conditional edge in subgraph
```

---

### Fix 3.7 — Pin requirements.txt

**File:** `requirements.txt`

**Change:**
Replace every `>=` with `~=` (compatible-release) for major libraries:
```
langgraph~=1.0
langchain-core~=0.3
langchain-openai~=0.2
streamlit~=1.40
chromadb~=0.5
yfinance~=0.2
python-dotenv~=1.0
```

Keep the current resolved versions for non-critical deps. Run `pip freeze > requirements-lock.txt` and commit both.

**Commit:**
```
chore: pin direct deps with ~= and add requirements-lock.txt
```

---

### Fix 3.8 — Smoke test skeleton

**Files:** new `tests/` directory

**Change:**
```
tests/
├── __init__.py
├── test_tools_smoke.py       # each tool returns string, no crash
├── test_monitor_smoke.py     # each check function returns dict
└── conftest.py               # pytest fixtures
```

Example `tests/test_tools_smoke.py`:
```python
"""Smoke tests — tools return strings, do not crash."""
from tools.calculator_tool import calculator
from tools.india_time_tool import get_india_time
from tools.commodity_tool import get_commodity_price


def test_calculator_basic():
    result = calculator.invoke({"expression": "2+2"})
    assert isinstance(result, str)
    assert "4" in result


def test_india_time():
    result = get_india_time.invoke({})
    assert isinstance(result, str)
    assert "IST" in result or "India" in result


def test_commodity_wheat():
    result = get_commodity_price.invoke({"commodity": "wheat"})
    assert isinstance(result, str)
```

Add `pytest~=8.0` to requirements.txt.

**Test:**
```bash
pytest tests/ -v
```

**Commit:**
```
test: add smoke test suite for tools and monitor checks
```

---

## Phase 4: Documentation Consistency

### Fix 4.1 — Fix CLAUDE.md / README.md inconsistencies

**Files:**
- `CLAUDE.md`
- `README.md`
- `tool_testing/README.md`

**Change:**

`CLAUDE.md`:
- Line "MySQL (data analysis)" → "SQLite (data analysis)"

`README.md`:
- Architecture diagram: `InMemorySaver` → `SqliteSaver`
- Prerequisites: `Python 3.9+` → `Python 3.11+` (Docker will use 3.11-slim)
- Roadmap: mark `SQLite persistence` as done, `HITL` as done
- Add section on monitoring, Gmail, Slack

`tool_testing/README.md` — major cleanup:
- Remove all references to Tavily (test_web_search.py uses DuckDuckGo per spec)
- Remove all references to Telegram (not in codebase per CLAUDE.md)
- Delete `test_telegram_alert.py` if present (it shouldn't be)
- Remove all emojis (✓, ✅, ✗) — replace with `[OK]`, `[PASS]`, `[FAIL]`
- Remove `test_calender.py` (legacy Nager.Date reference)

**Commit:**
```
docs: reconcile CLAUDE.md/README/test-readme with actual stack (SQLite, DuckDuckGo, no Telegram)
```

---

### Fix 4.2 — Update specs to reflect fixes

**Files:**
- `.claude/specs/tools/monitor-spec.md` — document `confirm=True` HITL requirement
- `.claude/specs/architecture/rag-spec.md` — confirm `data/chroma_db/` path
- `.claude/specs/INDEX.md` — update [WIP]/[DONE] statuses
- Add `.claude/specs/architecture/paths-spec.md` — central paths doc
- Add `.claude/specs/architecture/logging-spec.md` — logging config doc
- Add `.claude/specs/architecture/rate-limit-spec.md` — rate limit doc

**Commit:**
```
docs(specs): update for production fixes (HITL monitor, paths, logging, rate limit)
```

---

## Phase 5: Final Validation

Before merging `feat/production-fixes` to `main`:

```bash
# 1. All smoke tests pass
pytest tests/ -v

# 2. Every tool imports without error
python -c "
from tools.calculator_tool import calculator
from tools.india_time_tool import get_india_time
from tools.web_search_tool import web_search
from tools.stock_tool import get_stock_price
from tools.commodity_tool import get_commodity_price
from tools.nlp_tool import nlp_analyze
from tools.csv_analysis_tool import analyze_data
from tools.sql_analysis_tool import analyze_sql
from tools.monitor_tool import start_monitoring
from tools.slack_alert_tool import slack_notify
from tools.calendarific_tool import get_holidays
from tools.gmail import send_email
print('[OK] all tools import')
"

# 3. Backend boots
python -c "from backend import chatbot; print('[OK] backend')"

# 4. Monitor runner boots
python -c "from monitoring.runner import run_all_checks; print('[OK] runner')"

# 5. Frontend smoke (just launch, confirm no import errors, then Ctrl+C)
streamlit run frontend.py --server.headless=true &
sleep 5
kill %1

# 6. Grep for anti-patterns
grep -rn "from langchain.messages" . --include="*.py"                # should be empty
grep -rn "ashishdangwal97@gmail.com" . --include="*.py"              # should be empty
grep -rn "except.*:\\s*$" --include="*.py" .                         # review each
grep -rn "except.*:\\s*pass" --include="*.py" .                      # should be empty
grep -rn ">=" requirements.txt                                       # should be empty (all ~=)
```

If all green:

```bash
git checkout main
git merge feat/production-fixes --no-ff
git push origin main
git branch -d feat/production-fixes
```

Now you can safely start C-RAG (Phase 1 of the build roadmap) on a fresh `feat/c-rag` branch.

---

## Summary Checklist

Tick off as you go. Each line = one commit.

**Phase 1 — Critical (deploy blockers):**
- [ ] 1.1 Fix langchain.messages imports (backend + 7 test files)
- [ ] 1.2 Env-var Gmail recipient
- [ ] 1.3 HITL on start_monitoring
- [ ] 1.4 runtime_state.py for cross-thread flags
- [ ] 1.5 Load dataframe once in csv_analyst
- [ ] 1.6 Stop previous monitor thread
- [ ] 1.7 Graceful shutdown handler

**Phase 2 — High (scale / stability):**
- [ ] 2.1 SQLite connection pool
- [ ] 2.2 Central paths in utils/paths.py
- [ ] 2.3 Lazy ChromaDB client
- [ ] 2.4 Plots retention (7 day)
- [ ] 2.5 Fix dual-LLM routing
- [ ] 2.6 Remove os.chdir, dead fallback in gmail
- [ ] 2.7 Rate limiting on external tools
- [ ] 2.8 Central logging, kill silent excepts

**Phase 3 — Medium (code quality):**
- [ ] 3.1 SQL injection whitelist
- [ ] 3.2 Move sample SQL to file
- [ ] 3.3 Dispatcher pattern in analyze_data
- [ ] 3.4 Standardize error format
- [ ] 3.5 Fix subgraphs/__init__.py exports
- [ ] 3.6 Remove dead edge in sql_analyst
- [ ] 3.7 Pin requirements + lockfile
- [ ] 3.8 Smoke test skeleton

**Phase 4 — Docs:**
- [ ] 4.1 Reconcile CLAUDE.md / README / test-readme
- [ ] 4.2 Update specs for new architecture modules

**Phase 5 — Validation + merge**
- [ ] All smoke tests pass
- [ ] Anti-pattern greps empty
- [ ] Merge to main

---

## What this does NOT include

Deferred to subsequent branches per build roadmap:

- **feat/c-rag** — Corrective RAG with relevance grader + web-search fallback
- **feat/memory** — short-term / long-term / user memory system
- **feat/frontend-redesign** — split frontend.py into modules + memory panel UI
- **feat/docker** — Dockerfile, docker-compose, Redis cache backend flip

Do NOT mix these concerns into `feat/production-fixes`. One branch, one purpose.
