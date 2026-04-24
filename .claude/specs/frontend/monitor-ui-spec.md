# Frontend Monitor UI Spec

## Overview
Streamlit sidebar monitor control panel with HITL (Human-In-The-Loop) approval flows for email and Slack alerts. Allows users to start/stop monitoring, configure intervals, and manually trigger or schedule reports.

## Current State
- **monitoring/** directory: Comprehensive check functions (commodities, files, APIs, databases, chromadb, app)
- **monitoring/runner.py**: Orchestrates checks and scheduling
- **monitoring/reports/formatter.py**: Formats results for display
- **monitoring/alerts/slack_alert.py**: Sends Slack messages (automated, no HITL)
- **monitoring/alerts/gmail_alert.py**: Sends Gmail reports (HITL only)
- **tools/monitor_tool.py**: Legacy tool (for chat commands, sentiment-based commodity monitoring)
- **tools/slack_alert_tool.py**: Slack webhook integration
- **tools/gmail.py**: Gmail wrapper

## Frontend Architecture

### Part 1: Sidebar Monitor Panel

**Location:** streamlit sidebar (after existing chat history section)

**Layout:**
```
st.divider()
st.subheader("Pipeline Monitor")

[Monitor Selection Multiselect]
[Interval Dropdown]
[Start/Stop Buttons]
[Status Indicator]
[Report Action Buttons] (conditional)
```

#### 1.1 Monitor Selection Multiselect
```python
monitor_selection = st.multiselect(
  "Select monitors:",
  options=[
    "Commodity Prices",
    "Data Files",
    "API Health",
    "Database Health",
    "ChromaDB",
    "App Health",
    "All"
  ],
  default=[]
)
```

**Behavior:**
- If "All" selected, expands to all 6 individual monitors
- Multiple selections allowed
- Default empty (user must select)

#### 1.2 Interval Dropdown
```python
interval = st.selectbox(
  "Check interval:",
  options=[
    "Every 15 minutes",
    "Every 30 minutes",
    "Every hour",
    "Every 6 hours"
  ],
  index=1  # default 30 min
)
```

**Interval Map:**
- "Every 15 minutes" → 15 min
- "Every 30 minutes" → 30 min
- "Every hour" → 60 min
- "Every 6 hours" → 360 min

#### 1.3 Start/Stop Buttons
```python
col1, col2 = st.columns(2)
with col1:
  start_btn = st.button(
    "Start Monitor",
    use_container_width=True,
    type="primary"
  )
with col2:
  stop_btn = st.button(
    "Stop Monitor",
    use_container_width=True,
    type="secondary"
  )
```

#### 1.4 Status Indicator
```python
if st.session_state.get("monitor_running"):
  st.success("Monitor: RUNNING")
  st.caption(f"Checking: {', '.join(st.session_state['monitor_selections'])}")
  st.caption(f"Interval: {st.session_state['monitor_interval']} min")
else:
  st.info("Monitor: STOPPED")
```

#### 1.5 Report Action Buttons (Conditional)
Only shown when monitor is running:

```python
if st.session_state.get("monitor_running"):
  st.divider()
  st.caption("Report Actions:")
  
  report_col1, report_col2 = st.columns(2)
  with report_col1:
    gmail_now_btn = st.button(
      "Email Report Now",
      use_container_width=True
    )
  with report_col2:
    slack_now_btn = st.button(
      "Slack Report Now",
      use_container_width=True
    )
  
  schedule_btn = st.button(
    "Schedule Reports",
    use_container_width=True
  )
  
  stop_reports_btn = st.button(
    "Pause Reports",
    use_container_width=True
  )
```

**Button Behavior:**
- **Email Report Now**: Triggers Gmail HITL flow
- **Slack Report Now**: Sends immediately (no HITL needed)
- **Schedule Reports**: Opens time picker for daily scheduled sends
- **Pause Reports**: Stops scheduled sends, monitor keeps running

---

### Part 2: Session State Management

Initialize in frontend.py early in script:

```python
if "monitor_running" not in st.session_state:
    st.session_state["monitor_running"] = False
if "monitor_selections" not in st.session_state:
    st.session_state["monitor_selections"] = []
if "monitor_interval" not in st.session_state:
    st.session_state["monitor_interval"] = 30
if "monitor_thread" not in st.session_state:
    st.session_state["monitor_thread"] = None
if "last_check_results" not in st.session_state:
    st.session_state["last_check_results"] = None
if "report_scheduled" not in st.session_state:
    st.session_state["report_scheduled"] = False
if "report_paused" not in st.session_state:
    st.session_state["report_paused"] = False
if "scheduled_time" not in st.session_state:
    st.session_state["scheduled_time"] = None
if "awaiting_hitl" not in st.session_state:
    st.session_state["awaiting_hitl"] = False
if "hitl_context" not in st.session_state:
    st.session_state["hitl_context"] = None
```

**Key state variables:**
| Variable | Type | Purpose |
|----------|------|---------|
| `monitor_running` | bool | Monitor daemon thread active |
| `monitor_selections` | list[str] | Selected monitors to run |
| `monitor_interval` | int | Check interval in minutes |
| `monitor_thread` | Thread | Daemon thread reference |
| `last_check_results` | dict | Latest check results (for preview) |
| `report_scheduled` | bool | Daily report scheduled |
| `report_paused` | bool | Scheduled reports paused (but monitor running) |
| `scheduled_time` | str | Time for daily report (HH:MM format) |
| `awaiting_hitl` | bool | Waiting for user action |
| `hitl_context` | str | Which HITL flow active |

---

### Part 3: Button Handlers

#### 3.1 START MONITOR Handler

```python
if start_btn:
  if not monitor_selection:
    st.warning("Select at least one monitor.")
  else:
    # Map interval string to minutes
    interval_map = {
      "Every 15 minutes": 15,
      "Every 30 minutes": 30,
      "Every hour": 60,
      "Every 6 hours": 360
    }
    interval_minutes = interval_map[interval]
    
    # Expand "All" selection
    selections = monitor_selection
    if "All" in selections:
      selections = [
        "Commodity Prices",
        "Data Files",
        "API Health",
        "Database Health",
        "ChromaDB",
        "App Health"
      ]
    
    # Start background monitoring thread
    from monitoring.runner import start_background
    thread = start_background(selections, interval_minutes)
    
    # Update session state
    st.session_state["monitor_running"] = True
    st.session_state["monitor_selections"] = selections
    st.session_state["monitor_interval"] = interval_minutes
    st.session_state["monitor_thread"] = thread
    
    # Run immediate check
    from monitoring.runner import run_selected_checks
    results = run_selected_checks(selections)
    st.session_state["last_check_results"] = results
    
    # Format and display results in chat
    from monitoring.reports.formatter import format_daily_report
    report = format_daily_report(results)
    
    st.session_state["message_history"].append({
      "role": "assistant",
      "content": f"Monitor started.\n\nInitial check:\n{report}"
    })
    
    # Set HITL for user decision
    st.session_state["awaiting_hitl"] = True
    st.session_state["hitl_context"] = "monitor_started"
    st.rerun()
```

#### 3.2 STOP MONITOR Handler

```python
if stop_btn:
  st.session_state["monitor_running"] = False
  st.session_state["monitor_selections"] = []
  st.session_state["monitor_thread"] = None
  st.session_state["report_scheduled"] = False
  st.session_state["report_paused"] = False
  st.session_state["scheduled_time"] = None
  
  st.session_state["message_history"].append({
    "role": "assistant",
    "content": "Monitor stopped. All scheduled reports cancelled."
  })
  st.rerun()
```

#### 3.3 EMAIL REPORT NOW Handler

```python
if st.session_state.get("monitor_running") and gmail_now_btn:
  results = st.session_state.get("last_check_results")
  if results:
    st.session_state["awaiting_hitl"] = True
    st.session_state["hitl_context"] = "gmail_now"
    st.rerun()
  else:
    st.warning("No check results yet. Wait for first check to complete.")
```

#### 3.4 SLACK REPORT NOW Handler

```python
if st.session_state.get("monitor_running") and slack_now_btn:
  results = st.session_state.get("last_check_results")
  if results:
    from monitoring.alerts.slack_alert import alert_daily
    alert_daily(results)
    
    st.session_state["message_history"].append({
      "role": "assistant",
      "content": "Report sent to Slack."
    })
    st.rerun()
  else:
    st.warning("No check results yet.")
```

#### 3.5 SCHEDULE REPORTS Handler

```python
if st.session_state.get("monitor_running") and schedule_btn:
  st.session_state["awaiting_hitl"] = True
  st.session_state["hitl_context"] = "schedule_report"
  st.rerun()
```

#### 3.6 PAUSE REPORTS Handler

```python
if st.session_state.get("monitor_running") and stop_reports_btn:
  st.session_state["report_paused"] = True
  
  st.session_state["message_history"].append({
    "role": "assistant",
    "content": (
      "Reports paused. Monitor continues running.\n"
      "Click 'Email Report Now' or 'Slack Report Now' to send manually.\n"
      "Click 'Schedule Reports' to resume."
    )
  })
  st.rerun()
```

---

### Part 4: HITL Flows in Chat Area

Displayed **after chat messages**, **before chat input**.

#### 4.1 Monitor Started HITL

**Context:** `monitor_started`

```python
if context == "monitor_started":
  st.divider()
  st.warning("Monitor started. What would you like to do with the report?")
  
  h_col1, h_col2, h_col3, h_col4 = st.columns(4)
  
  with h_col1:
    if st.button("Email Now", key="h_email_now"):
      st.session_state["awaiting_hitl"] = True
      st.session_state["hitl_context"] = "gmail_now"
      st.rerun()
  
  with h_col2:
    if st.button("Slack Now", key="h_slack_now"):
      results = st.session_state["last_check_results"]
      from monitoring.alerts.slack_alert import alert_daily
      alert_daily(results)
      
      st.session_state["message_history"].append({
        "role": "assistant",
        "content": "Report sent to Slack."
      })
      st.session_state["awaiting_hitl"] = False
      st.rerun()
  
  with h_col3:
    if st.button("Schedule", key="h_schedule"):
      st.session_state["awaiting_hitl"] = True
      st.session_state["hitl_context"] = "schedule_report"
      st.rerun()
  
  with h_col4:
    if st.button("Skip", key="h_skip"):
      st.session_state["awaiting_hitl"] = False
      st.session_state["hitl_context"] = None
      st.rerun()
```

#### 4.2 Gmail Now HITL

**Context:** `gmail_now`

Shows report preview + confirmation buttons.

```python
elif context == "gmail_now":
  results = st.session_state.get("last_check_results", {})
  from monitoring.reports.formatter import format_daily_report
  report = format_daily_report(results)
  
  st.divider()
  st.warning("Email Report Preview:")
  st.text_area(
    "Report content:",
    value=report[:500] + "..." if len(report) > 500 else report,
    height=200,
    disabled=True
  )
  
  g_col1, g_col2 = st.columns(2)
  with g_col1:
    if st.button("Send Email", key="h_send_email", type="primary"):
      from monitoring.alerts.gmail_alert import send_gmail_report
      send_gmail_report(results)
      
      st.session_state["message_history"].append({
        "role": "assistant",
        "content": "Report sent to your Gmail inbox."
      })
      st.session_state["awaiting_hitl"] = False
      st.session_state["hitl_context"] = None
      st.rerun()
  
  with g_col2:
    if st.button("Cancel", key="h_cancel_email"):
      st.session_state["awaiting_hitl"] = False
      st.session_state["hitl_context"] = None
      st.rerun()
```

#### 4.3 Schedule Report HITL

**Context:** `schedule_report`

Time picker + channel selector.

```python
elif context == "schedule_report":
  st.divider()
  st.warning("Schedule recurring reports:")
  
  s_channel = st.radio(
    "Send to:",
    options=["Slack", "Gmail", "Both"],
    horizontal=True,
    key="schedule_channel"
  )
  
  s_time = st.time_input(
    "Daily report time:",
    value=None,
    key="schedule_time"
  )
  
  s_col1, s_col2 = st.columns(2)
  with s_col1:
    if st.button("Confirm Schedule", key="h_confirm_schedule", type="primary"):
      import schedule
      from monitoring.runner import run_all_checks
      from monitoring.reports.formatter import format_daily_report
      
      time_str = s_time.strftime("%H:%M") if s_time else "09:00"
      channel = s_channel
      
      def scheduled_job():
        if not st.session_state.get("report_paused"):
          results = run_all_checks()
          st.session_state["last_check_results"] = results
          report = format_daily_report(results)
          
          if channel in ["Slack", "Both"]:
            from monitoring.alerts.slack_alert import alert_daily
            alert_daily(results)
          
          if channel in ["Gmail", "Both"]:
            from monitoring.alerts.gmail_alert import send_gmail_report
            send_gmail_report(results)
      
      schedule.every().day.at(time_str).do(scheduled_job)
      
      st.session_state["report_scheduled"] = True
      st.session_state["scheduled_time"] = time_str
      st.session_state["report_paused"] = False
      
      st.session_state["message_history"].append({
        "role": "assistant",
        "content": (
          f"Daily report scheduled at {time_str}.\n"
          f"Channel: {channel}\n"
          f"Click 'Pause Reports' to stop temporarily.\n"
          f"Click 'Stop Monitor' to cancel everything."
        )
      })
      st.session_state["awaiting_hitl"] = False
      st.session_state["hitl_context"] = None
      st.rerun()
  
  with s_col2:
    if st.button("Cancel", key="h_cancel_schedule"):
      st.session_state["awaiting_hitl"] = False
      st.session_state["hitl_context"] = None
      st.rerun()
```

---

### Part 5: Chat Command Integration

Monitor can be controlled via chat commands.

**Commands:**
| Command | Action |
|---------|--------|
| "stop monitoring" | Trigger `stop_btn` logic |
| "pause reports" | Trigger `stop_reports_btn` logic |
| "send report now" | Trigger `gmail_now_btn` logic |
| "send to slack" | Trigger `slack_now_btn` logic |
| "show monitor status" | Display status message |
| "schedule report" | Trigger `schedule_btn` logic |

**Implementation:**

```python
def handle_monitor_command(action: str):
  if action == "stop_monitor":
    # Run stop_btn logic
    st.session_state["monitor_running"] = False
    st.session_state["monitor_selections"] = []
    st.session_state["monitor_thread"] = None
    st.session_state["report_scheduled"] = False
    st.session_state["report_paused"] = False
    
    st.session_state["message_history"].append({
      "role": "assistant",
      "content": "Monitor stopped. All scheduled reports cancelled."
    })
  
  elif action == "pause_reports":
    st.session_state["report_paused"] = True
    st.session_state["message_history"].append({
      "role": "assistant",
      "content": (
        "Reports paused. Monitor continues running.\n"
        "Type 'schedule report' to resume."
      )
    })
  
  elif action == "gmail_now":
    if st.session_state.get("monitor_running"):
      st.session_state["awaiting_hitl"] = True
      st.session_state["hitl_context"] = "gmail_now"
  
  elif action == "slack_now":
    if st.session_state.get("monitor_running"):
      results = st.session_state.get("last_check_results")
      if results:
        from monitoring.alerts.slack_alert import alert_daily
        alert_daily(results)
        st.session_state["message_history"].append({
          "role": "assistant",
          "content": "Report sent to Slack."
        })
  
  elif action == "monitor_status":
    st.session_state["message_history"].append({
      "role": "assistant",
      "content": get_monitor_status()
    })
  
  elif action == "schedule_report":
    if st.session_state.get("monitor_running"):
      st.session_state["awaiting_hitl"] = True
      st.session_state["hitl_context"] = "schedule_report"

# In chat input handler:
monitor_commands = {
  "stop monitoring": "stop_monitor",
  "pause reports": "pause_reports",
  "send report now": "gmail_now",
  "send to slack": "slack_now",
  "show monitor status": "monitor_status",
  "schedule report": "schedule_report"
}

for phrase, action in monitor_commands.items():
  if phrase in user_input.lower():
    handle_monitor_command(action)
    st.rerun()
    break
```

---

### Part 6: Monitor Status Message

```python
def get_monitor_status() -> str:
  if not st.session_state.get("monitor_running"):
    return "Monitor is not running. Click 'Start Monitor' in sidebar."
  
  lines = [
    "Monitor Status: RUNNING",
    f"Checking: {', '.join(st.session_state['monitor_selections'])}",
    f"Interval: every {st.session_state['monitor_interval']} minutes",
  ]
  
  if st.session_state.get("report_scheduled"):
    lines.append(
      f"Scheduled report: daily at {st.session_state['scheduled_time']}"
    )
  
  if st.session_state.get("report_paused"):
    lines.append("Reports: PAUSED")
  
  results = st.session_state.get("last_check_results")
  if results:
    from monitoring.reports.formatter import has_issues, format_issue_alert
    if has_issues(results):
      lines.append("\nCurrent Issues:")
      lines.append(format_issue_alert(results))
    else:
      lines.append("\nAll systems: [OK]")
  
  return "\n".join(lines)
```

---

## Part 7: monitoring/runner.py Updates

Add these functions to support frontend integration:

### run_selected_checks()

```python
def run_selected_checks(selections: list) -> dict:
  """
  Run only selected checks (not all).
  
  Args:
    selections: List of monitor names
    
  Returns:
    Dict with results for each selected monitor
  """
  results = {}
  check_map = {
    "Commodity Prices": check_commodities,
    "Data Files": check_files,
    "API Health": check_apis,
    "Database Health": check_databases,
    "ChromaDB": check_chromadb,
    "App Health": check_app
  }
  
  for selection in selections:
    if selection in check_map:
      try:
        results[selection] = check_map[selection]()
      except Exception as e:
        logger.error(f"Error running {selection}: {e}")
        results[selection] = {"status": "[ERROR]", "error": str(e)}
  
  return results
```

### start_background()

```python
import threading

def start_background(selections: list, interval_minutes: int) -> threading.Thread:
  """
  Start background monitoring in daemon thread.
  
  Args:
    selections: List of monitor names
    interval_minutes: Check interval
    
  Returns:
    Thread reference (for tracking)
  """
  def job():
    results = run_selected_checks(selections)
    from monitoring.reports.formatter import has_issues
    from monitoring.alerts.slack_alert import alert_issues
    
    if has_issues(results):
      alert_issues(results)
  
  schedule.every(interval_minutes).minutes.do(job)
  
  thread = threading.Thread(
    target=lambda: [
      schedule.run_pending() or time.sleep(60)
      for _ in iter(int, 1)
    ],
    daemon=True
  )
  thread.start()
  return thread
```

---

## Key Design Decisions

### 1. No Emojis
- Windows cp1252 encoding constraint
- Use `[OK]`, `[ALERT]`, `[DOWN]`, `[WARN]`, `[ERROR]` status codes

### 2. HITL Rules
| Action | HITL Required | Reason |
|--------|---------------|--------|
| Slack auto-alert | No | Background, fully automated |
| Slack manual send | No | User explicitly clicked button |
| Gmail send | Yes | Email is more sensitive, needs confirmation |
| Schedule creation | Yes | Creates recurring job, review required |
| Monitor start | Yes | Initial report shown, user chooses action |

### 3. Pause vs Stop
- **Pause**: Monitor keeps checking, reports stop sending
- **Stop**: Everything stops, thread terminated

### 4. Session State
- Always use `.get()` with defaults
- Never assume state variables exist
- Initialize all at startup

### 5. Thread Safety
- Daemon threads (auto-kill on app exit)
- Schedule library handles concurrent checks
- No explicit locking needed (Streamlit is single-threaded per session)

---

## Testing Checklist

1. **Start Monitor**
   - [ ] Select "Commodity Prices", "API Health"
   - [ ] Set "Every 15 minutes"
   - [ ] Click "Start Monitor"
   - [ ] Results appear in chat
   - [ ] HITL buttons appear

2. **HITL Email**
   - [ ] Click "Email Now" in sidebar
   - [ ] Preview shown
   - [ ] Click "Send Email"
   - [ ] Check Gmail inbox

3. **HITL Slack**
   - [ ] Click "Slack Now"
   - [ ] Message sent immediately
   - [ ] Check Slack #alerts

4. **Schedule Reports**
   - [ ] Click "Schedule Reports"
   - [ ] Select "Both", time "09:00"
   - [ ] Confirm
   - [ ] Verify status shows "Scheduled"

5. **Pause/Resume**
   - [ ] Click "Pause Reports"
   - [ ] Monitor still running (sidebar shows RUNNING)
   - [ ] No scheduled sends
   - [ ] Click "Schedule Reports" again to resume

6. **Stop Monitor**
   - [ ] Click "Stop Monitor"
   - [ ] Everything stops
   - [ ] Sidebar shows STOPPED

7. **Chat Commands**
   - [ ] Type "show monitor status"
   - [ ] Type "send to slack"
   - [ ] Type "stop monitoring"

---

## File Changes Summary

| File | Changes |
|------|---------|
| `frontend.py` | Add sidebar monitor panel + HITL flows + chat commands |
| `monitoring/runner.py` | Add `run_selected_checks()` and `start_background()` |

---

## Implementation Order (Commits)

1. **Sidebar UI**: Monitor selection, interval, start/stop buttons, status
2. **HITL Flows**: Email preview, Slack confirm, schedule picker
3. **Chat Commands**: Monitor control via chat messages
4. **Runner Updates**: Backend functions for frontend integration
