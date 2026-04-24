# Monitoring System Spec

## Overview
Comprehensive background monitoring system for commodity prices, APIs, files, databases, ChromaDB, and application health. Runs independently with scheduled checks and automated Slack alerts. No HITL for background monitoring.

## Directory Structure
```
monitoring/
├── __init__.py
├── runner.py              Main scheduler orchestrator
├── checks/
│   ├── __init__.py
│   ├── commodity_check.py  Commodity price monitoring (wheat, soy, corn, sugar)
│   ├── file_check.py       File system health (data/ directory)
│   ├── api_check.py        External API availability (DuckDuckGo, yfinance, etc)
│   ├── database_check.py   SQLite database health
│   ├── chromadb_check.py   ChromaDB vector store health
│   └── app_check.py        Application resource usage
├── alerts/
│   ├── __init__.py
│   ├── slack_alert.py      Send alerts to Slack (automated, no HITL)
│   └── gmail_alert.py      Send reports to Gmail (HITL only, manual trigger)
└── reports/
    ├── __init__.py
    ├── formatter.py        Format check results into readable messages
    └── daily_report.py     (optional) Generate daily summary
```

## Check Functions

### commodity_check.py :: check_commodities()
Monitors 4 commodities using yfinance futures data.

**Symbols:**
- wheat: ZW=F
- soy: ZS=F
- corn: ZC=F
- sugar: SB=F

**Per commodity:**
- Fetch latest price via yfinance (1-5 day history)
- Calculate % change vs previous close
- Status assignment:
  - `change < -1.5%` → `[ALERT]`
  - `change > +1.5%` → `[SURGE]`
  - else → `[OK]`

**Returns:**
```python
{
  "wheat": {
    "price": 543.20,
    "change": -0.8,
    "status": "[OK]",
    "volume": 12400,
    "updated": "22 Apr 2026 14:30"
  },
  ...
}
```

**Error handling:** Per-commodity try/except. Never crashes whole monitor.

---

### file_check.py :: check_files()
Scans `data/` directory recursively for file health.

**Per file:**
- size_kb: File size in kilobytes
- age_hours: Hours since last modified
- readable: Try opening file (check integrity)
- Status assignment:
  - Unreadable → `[ERROR]`
  - age > 48hrs → `[STALE]`
  - size < 1KB → `[WARN]`
  - else → `[OK]`
- New files (not in last state) → `[NEW]`
- Missing files (in last state, not now) → `[MISSING]`

**State tracking:**
- File: `data/monitoring_state.json`
- Tracks which files were seen last check
- Updated after each check

**Returns:**
```python
{
  "chroma_db/data.db": {
    "size_kb": 234.5,
    "age_hours": 12.3,
    "status": "[OK]",
    "readable": true,
    "modified": "22 Apr 2026 14:30"
  },
  ...
}
```

---

### api_check.py :: check_apis()
Tests external API connectivity with retry logic.

**APIs tested:**
1. **DuckDuckGo**: Calls `DuckDuckGoSearchRun("test")`
2. **yfinance**: Calls `yf.Ticker("AAPL").history(period="1d")`
3. **Calendarific**: HTTP GET with API key
4. **Gmail SMTP**: SMTP_SSL connect (no auth, no email send)
5. **Slack webhook**: HTTP POST to webhook URL

**Retry logic:**
- Max retries: 3
- Delay between retries: 1 second
- Tracks attempts and response_ms

**Returns:**
```python
{
  "DuckDuckGo": {
    "status": "[OK]",
    "response_ms": 234,
    "attempts": 1
  },
  "Calendarific": {
    "status": "[DOWN]",
    "response_ms": null,
    "attempts": 3,
    "error": "timeout"
  }
}
```

---

### database_check.py :: check_databases()
Scans `data/databases/` for `.db` files + root `chat_memory.db`.

**Per database:**
- Connect via sqlite3
- List tables and count total rows
- Check size_mb and last modified timestamp
- Status assignment:
  - Corrupted (can't connect) → `[ERROR]`
  - size_mb > 500 → `[WARN]`
  - row count = 0 (but has tables) → `[WARN]`
  - else → `[OK]`

**Returns:**
```python
{
  "chat_memory.db": {
    "size_mb": 45.2,
    "tables": 3,
    "rows": 1523,
    "status": "[OK]",
    "modified": "22 Apr 2026 14:30"
  },
  ...
}
```

---

### chromadb_check.py :: check_chromadb()
Tests ChromaDB vector store at `data/chroma_db/`.

**Steps:**
1. Check directory exists
2. Connect via `Chroma(persist_directory=..., embedding_function=OpenAIEmbeddings())`
3. Get document count from collection
4. Run test similarity search ("test" query)
5. Check disk usage

**Status assignment:**
- Not found → `[NOT_FOUND]`
- doc_count = 0 → `[EMPTY]`
- Test search fails → `[ERROR]`
- disk_mb > 1024 → `[WARN]`
- else → `[OK]`

**Returns:**
```python
{
  "chromadb": {
    "status": "[OK]",
    "documents": 47,
    "disk_mb": 234.5,
    "test_query": "[OK]"
  }
}
```

---

### app_check.py :: check_app()
Monitors application resource usage via psutil.

**Metrics:**
- memory_pct: Process memory usage %
- cpu_pct: Process CPU usage % (interval=1sec)
- threads: Active thread count
- disk_pct: System disk usage %
- chat_db_size_mb: Size of chat_memory.db

**Status assignment:**
- memory_pct > 80% → `[WARN]`
- cpu_pct > 90% → `[WARN]`
- disk_pct > 85% → `[WARN]`
- else → `[OK]`

**Returns:**
```python
{
  "app_health": {
    "memory_pct": 45.2,
    "cpu_pct": 12.3,
    "threads": 8,
    "disk_pct": 34.1,
    "chat_db_size_mb": 45.2,
    "status": "[OK]"
  }
}
```

---

## Alert System

### formatter.py
Formats check results into human-readable messages. No emojis (Windows cp1252 encoding).

**has_issues(results: dict) -> bool**
- Returns True if any result has status in `[ALERT]`, `[DOWN]`, `[WARN]`, `[ERROR]`
- Used to decide whether to send alerts

**format_issue_alert(results: dict) -> str**
- Extracts only problematic items
- Short message format
- Includes timestamp
- Footer: "Check chatbot for full report"
- Max 4000 chars (Slack limit)

**format_daily_report(results: dict) -> str**
- Formats ALL results regardless of status
- Sections: Commodities, APIs, Files, Databases, ChromaDB, App Health
- Issues highlighted at top
- Timestamp at top
- Max 4000 chars, truncates if longer

**format_all_clear() -> str**
- One-line message: "All systems [OK] - {timestamp}"

**Status codes (no emojis):**
- `[OK]` - Nominal
- `[ALERT]` - Critical issue (commodity volatile)
- `[DOWN]` - API unreachable
- `[WARN]` - Warning (resource threshold, stale data)
- `[ERROR]` - Corrupted/unreadable
- `[STALE]` - Data not updated in 48hrs
- `[EMPTY]` - No data
- `[NEW]` - File/resource newly detected
- `[MISSING]` - Resource disappeared
- `[NOT_FOUND]` - Expected resource not present
- `[SURGE]` - Commodity up > 1.5%

---

### slack_alert.py
Sends alerts to Slack webhook (fully automated, no HITL).

**alert_issues(results: dict)**
- Checks `has_issues(results)`
- If True, sends formatted issue alert via `send_slack_alert()`
- No user interaction

**alert_daily(results: dict)**
- Sends full daily report via `send_slack_alert()`
- Called daily at 09:00

**alert_all_clear()**
- Sends all-clear message
- Optional: called when no issues detected on startup

---

### gmail_alert.py
Sends reports via Gmail (HITL only - manual trigger, never automatic).

**send_gmail_report(results: dict, subject: str = None)**
- Formats full daily report
- Sends to `ashishdangwal97@gmail.com`
- Subject: `[Report] Pipeline Status - {datetime}` (or custom)
- Called only by explicit user action, never by scheduler

---

## Scheduler (runner.py)

### run_all_checks() -> dict
Runs all check functions, returns dict with keys:
- `commodities`
- `files`
- `apis`
- `databases`
- `chromadb`
- `app`

### run_quick_checks() -> dict
Lightweight checks (commodities + APIs only), for frequent monitoring.

### monitor_job()
Called every 30 minutes:
1. `run_quick_checks()`
2. If `has_issues()`, send Slack alert

### daily_report_job()
Called daily at 09:00:
1. `run_all_checks()`
2. Send full Slack report

### start()
Main entry point. Prints startup banner and schedules:
- Every 30 min: `monitor_job()` (commodities + APIs)
- Every 1 hour: `check_files()`, `check_databases()`
- Every 6 hours: `check_chromadb()`, `check_app()`
- Daily at 09:00: `daily_report_job()`

Runs immediate full check on startup. If issues, sends alert. Otherwise prints "All systems [OK]".

Then enters infinite loop: `schedule.run_pending()` every 60 seconds.

---

## HITL Rules
- **Slack automated alerts**: No HITL, fires automatically from scheduler
- **Gmail reports**: HITL only, manual user action required
- **File state tracking**: No HITL, automatic background state management
- **All checks**: Fully automatic, no user prompts

---

## Error Handling
Each check function:
- Handles own try/except blocks
- Never crashes entire monitor
- Returns dict always (with status = `[ERROR]` on failure)
- Logs error via Python logging

---

## Configuration
- **Commodity symbols:** Hardcoded in commodity_check.py
- **Check intervals:** Hardcoded in runner.py (configurable via edit)
- **Daily report time:** 09:00 (configurable via schedule.every().day.at())
- **State file:** `data/monitoring_state.json` (auto-created)

---

## Entry Points
1. **Root monitor.py**: Simple entry point, calls `monitoring.runner.start()`
2. **Direct runner**: `python -m monitoring.runner`
3. **Individual checks:** Each check has `if __name__ == "__main__"` test block

---

## Testing Order
Test each check independently before running full monitor:

```bash
python -c "from monitoring.checks.commodity_check import check_commodities; import json; print(json.dumps(check_commodities(), indent=2))"

python -c "from monitoring.checks.api_check import check_apis; import json; print(json.dumps(check_apis(), indent=2))"

python -c "from monitoring.checks.file_check import check_files; import json; print(json.dumps(check_files(), indent=2))"

python -c "from monitoring.checks.database_check import check_databases; import json; print(json.dumps(check_databases(), indent=2))"

python -c "from monitoring.checks.chromadb_check import check_chromadb; import json; print(json.dumps(check_chromadb(), indent=2))"

python -c "from monitoring.checks.app_check import check_app; import json; print(json.dumps(check_app(), indent=2))"

python monitor.py
```

---

## Debugging
Check intervals for testing (modify runner.py temporarily):
```python
schedule.every(1).minute.do(monitor_job)  # Test every 1 min instead of 30
```

Check Slack messages in configured channel to verify alerts.

Logs printed to console (StreamHandler) + optional file if configured.

---

## Dependencies
- langchain-community (DuckDuckGoSearchRun)
- langchain-openai (OpenAIEmbeddings)
- yfinance
- requests
- psutil
- chromadb
- schedule
