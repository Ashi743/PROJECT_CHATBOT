# Frontend Redesign — Production-Ready Streamlit UI

**Goal:** Clean, professional, easy-to-read Streamlit interface with smart organization and better UX.

**Scope:** Redesign `frontend.py` ONLY. Do NOT touch backend, tools, monitoring, or subgraphs. All existing functionality must work exactly as before — just reorganized for clarity.

**Branch:** Create `feat/frontend-redesign` off `main` (or `feat/production-fixes` if merged).

---

## Design Principles

1. **Clarity over cleverness** — simple layout, obvious controls
2. **Group related things** — data upload section, monitor section, etc.
3. **7 recent chats visible** — older chats in scrollable dropdown
4. **One unified data section** — SQL + CSV together, not scattered
5. **Small subtle labels** — file type + name in corner, not intrusive
6. **Everything still works** — HITL flows, streaming, tools, monitoring

---

## Current Problems

❌ **Chat history cluttered** — all threads shown, gets messy after 20 chats
❌ **Data upload scattered** — SQL and CSV in different places
❌ **No visual hierarchy** — everything same size/weight
❌ **Hard to scan** — unclear what's a button vs status vs info
❌ **900+ lines, one file** — difficult to maintain

---

## New Layout (Top to Bottom)

```
╔══════════════════════════════════════════════════════════╗
║  SIDEBAR                                                 ║
╟──────────────────────────────────────────────────────────╢
║  [App Title + Icon]                                      ║
║                                                          ║
║  ┌─ Chat History ────────────────────────────────────┐  ║
║  │ • Recent 7 chats (always visible)                 │  ║
║  │ • "More chats..." (expander with scroll)          │  ║
║  │ • [+ New Chat] button                             │  ║
║  └───────────────────────────────────────────────────┘  ║
║                                                          ║
║  ┌─ Data & Databases ────────────────────────────────┐  ║
║  │ [Upload SQL/CSV/Excel] (unified dropzone)         │  ║
║  │                                                    │  ║
║  │ Available Data:                                   │  ║
║  │  └─ sales.csv        (CSV, 234KB)                 │  ║
║  │  └─ analytics.db     (SQL, 1.2MB)                 │  ║
║  │  └─ inventory.xlsx   (Excel, 456KB)               │  ║
║  └───────────────────────────────────────────────────┘  ║
║                                                          ║
║  ┌─ Pipeline Monitor ─────────────────────────────────┐ ║
║  │ [Select Monitors] multiselect                      │ ║
║  │ [Interval] dropdown                                │ ║
║  │ [Start] [Stop] buttons                             │ ║
║  │ Status: RUNNING / STOPPED                          │ ║
║  └───────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════╗
║  MAIN CHAT AREA                                          ║
╟──────────────────────────────────────────────────────────╢
║  [Current file context: sales.csv]      ← small, corner ║
║                                                          ║
║  User:  What's the average by region?                   ║
║  Bot:   Analyzing sales.csv...                          ║
║         Region | Avg Sales                              ║
║         North  | $1,234                                 ║
║         ...                                             ║
║                                                          ║
║  [HITL approval UI shown inline when needed]            ║
║                                                          ║
║  ┌───────────────────────────────────────────────────┐  ║
║  │ 💬 Your message...                    [Send]      │  ║
║  └───────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════╝
```

---

## Detailed Requirements

### 1. Chat History (Sidebar)

**7 Recent Chats — Always Visible**
```python
recent_threads = get_last_n_threads(7)  # newest first
for thread in recent_threads:
    if st.button(f"{thread.title[:30]}...", key=f"recent_{thread.id}"):
        switch_to_thread(thread.id)
```

**Older Chats — Scrollable Expander**
```python
older_threads = get_threads_older_than(recent_threads[-1])
if older_threads:
    with st.expander(f"More chats ({len(older_threads)})"):
        for thread in older_threads:
            if st.button(thread.title, key=f"old_{thread.id}"):
                switch_to_thread(thread.id)
```

**New Chat Button**
```python
if st.button("+ New Chat", use_container_width=True, type="primary"):
    create_new_thread()
```

---

### 2. Data & Databases (Sidebar) — UNIFIED SECTION

**One Upload Widget for All Types**
```python
st.subheader("Data & Databases")

uploaded_file = st.file_uploader(
    "Upload data file",
    type=["csv", "xlsx", "xls", "sql", "db"],
    help="SQL databases, CSV, or Excel files"
)

if uploaded_file:
    file_type = detect_file_type(uploaded_file.name)
    
    if file_type == "sql":
        handle_sql_upload(uploaded_file)
    elif file_type in ["csv", "xlsx", "xls"]:
        handle_data_upload(uploaded_file)
```

**Available Data — Single List with Type Labels**
```python
st.caption("Available Data:")

all_data = get_all_data_files()  # combines SQL + CSV + Excel

for item in all_data:
    # Small font, shows: filename (type, size)
    label = f"{item.name}  ({item.type}, {item.size})"
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.caption(label)
    with col2:
        if st.button("🗑", key=f"del_{item.id}", help="Delete"):
            delete_file_with_hitl(item)
```

**Function to get all data:**
```python
def get_all_data_files():
    """Returns unified list: SQL databases + CSV/Excel datasets"""
    files = []
    
    # SQL databases from data/databases/
    for db in list_sql_databases():
        files.append({
            "name": db.name,
            "type": "SQL",
            "size": format_size(db.size),
            "id": f"sql_{db.name}",
            "path": db.path
        })
    
    # CSV/Excel from data/uploads/
    for dataset in list_datasets():
        files.append({
            "name": dataset.name,
            "type": dataset.type,  # CSV/Excel
            "size": format_size(dataset.size),
            "id": f"data_{dataset.name}",
            "path": dataset.path
        })
    
    return sorted(files, key=lambda x: x["name"])
```

---

### 3. Current File Context (Main Area — Top Right Corner)

**Small, subtle label showing active dataset**
```python
# Top right of chat area
if st.session_state.get("active_dataset"):
    dataset = st.session_state["active_dataset"]
    st.caption(f"📊 Active: {dataset['name']} ({dataset['type']})")
```

**Auto-set when user uploads or references a file:**
```python
def set_active_dataset(name, file_type):
    st.session_state["active_dataset"] = {
        "name": name,
        "type": file_type
    }
```

**Clear on new chat:**
```python
def create_new_thread():
    st.session_state["active_dataset"] = None
    # ... rest of new thread logic
```

---

### 4. Pipeline Monitor (Sidebar) — Keep Same, Just Cleaner

**No changes to logic**, just visual polish:
- Use `st.status()` widget for running state
- Color-coded status: green=running, gray=stopped
- Compact button layout (2 columns)

```python
st.subheader("Pipeline Monitor")

# Monitor selection
monitors = st.multiselect(
    "Select monitors",
    options=["Commodity Prices", "Data Files", "API Health", 
             "Database Health", "ChromaDB", "App Health"],
    key="monitor_selection"
)

# Interval + buttons in 2 columns
col1, col2 = st.columns(2)
with col1:
    interval = st.selectbox("Interval", 
                           ["15 min", "30 min", "1 hour", "6 hours"])
with col2:
    if st.button("Start", type="primary", use_container_width=True):
        start_monitor()
    if st.button("Stop", use_container_width=True):
        stop_monitor()

# Status indicator
if st.session_state.get("monitor_running"):
    st.success("Status: RUNNING")
else:
    st.info("Status: STOPPED")
```

---

### 5. Main Chat Area — Keep Streaming, Add Polish

**No changes to streaming logic**, just layout:

```python
# Chat container
chat_container = st.container()

with chat_container:
    # Show message history
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # HITL UI (if active)
    if st.session_state.get("awaiting_hitl"):
        show_hitl_ui()

# Input at bottom
user_input = st.chat_input("Your message...")
if user_input:
    handle_user_message(user_input)
```

**HITL flows stay inline** (already good, just keep them).

---

## File Structure — Split frontend.py

**Current:** 900+ lines in one file 😱

**New structure:**
```
frontend/
├── __init__.py
├── main.py              # Entry point, session init, layout
├── sidebar.py           # All sidebar widgets
├── chat_area.py         # Chat display + input
├── data_section.py      # Unified data upload + list
├── monitor_section.py   # Monitor controls
├── hitl_flows.py        # HITL UI components
└── utils.py             # Helper functions
```

**Responsibilities:**

**main.py** (100 lines):
- Page config
- Session state init
- Layout (2 columns: sidebar + main)
- Route to sidebar/chat_area

**sidebar.py** (200 lines):
- Chat history (recent + older)
- New chat button
- Import data_section, monitor_section
- Render both sections

**chat_area.py** (150 lines):
- Display messages
- Streaming handler
- Chat input widget
- Active dataset label

**data_section.py** (100 lines):
- Unified file uploader
- get_all_data_files()
- Available data list with delete
- HITL for delete

**monitor_section.py** (100 lines):
- Monitor multiselect
- Interval + buttons
- Status display
- Start/Stop handlers

**hitl_flows.py** (150 lines):
- All HITL UI modals
- Approval buttons
- Preview displays

**utils.py** (100 lines):
- format_size()
- detect_file_type()
- Thread management helpers
- State management

**Total: ~900 lines split across 8 files** = easier to read and maintain.

---

## Visual Design Polish

### Typography Hierarchy
```python
# Titles
st.title("🤖 AI Assistant")           # Large, bold

# Section headers
st.subheader("Data & Databases")      # Medium, bold

# Labels
st.write("Available Data:")           # Normal

# Small info
st.caption("sales.csv (CSV, 234KB)")  # Small, gray
```

### Color Coding
```python
# Success states
st.success("Monitor: RUNNING")

# Info states
st.info("Monitor: STOPPED")

# Warnings
st.warning("APPROVAL REQUIRED")

# Errors
st.error("[ERROR] Failed to load")
```

### Spacing
```python
# Between sections
st.divider()  # Clean horizontal line

# Within sections
st.write("")  # Small vertical space
```

---

## Implementation Steps

**Step 1: Create frontend/ directory structure**
```bash
mkdir frontend
touch frontend/__init__.py
touch frontend/main.py
touch frontend/sidebar.py
touch frontend/chat_area.py
touch frontend/data_section.py
touch frontend/monitor_section.py
touch frontend/hitl_flows.py
touch frontend/utils.py
```

**Step 2: Extract functions from frontend.py → new modules**
- Move sidebar widgets → `sidebar.py`
- Move chat display → `chat_area.py`
- Move data upload → `data_section.py`
- Move monitor controls → `monitor_section.py`
- Move HITL UI → `hitl_flows.py`
- Move helpers → `utils.py`

**Step 3: Wire up main.py**
```python
# frontend/main.py
import streamlit as st
from frontend.sidebar import render_sidebar
from frontend.chat_area import render_chat_area

st.set_page_config(page_title="AI Assistant", layout="wide")

# Init session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
# ... all other state inits

# Layout
sidebar_col, main_col = st.columns([1, 3])

with sidebar_col:
    render_sidebar()

with main_col:
    render_chat_area()
```

**Step 4: Update root frontend.py to import from frontend/**
```python
# frontend.py (root level — entry point for streamlit run)
from frontend.main import *
```

**Step 5: Test each section independently**
```bash
# Test sidebar
python -c "from frontend.sidebar import render_sidebar; print('[OK]')"

# Test chat area
python -c "from frontend.chat_area import render_chat_area; print('[OK]')"

# ... etc
```

**Step 6: Run full app**
```bash
streamlit run frontend.py
```

---

## Commit Strategy

```
feat(frontend): create frontend/ module structure

feat(frontend): extract sidebar to sidebar.py

feat(frontend): extract chat area to chat_area.py

feat(frontend): extract data section to data_section.py

feat(frontend): extract monitor section to monitor_section.py

feat(frontend): extract hitl flows to hitl_flows.py

feat(frontend): unify SQL and CSV data lists

feat(frontend): add 7 recent + scrollable older chats

feat(frontend): add active dataset context label

feat(frontend): polish typography and spacing

docs(frontend): update README with new structure
```

---

## Testing Checklist

After all changes:

**Functional tests:**
- [ ] Upload CSV → appears in data list
- [ ] Upload SQL → appears in data list
- [ ] Delete file → HITL approval shown
- [ ] Start monitor → status shows RUNNING
- [ ] Stop monitor → status shows STOPPED
- [ ] New chat → creates new thread
- [ ] Switch to old chat → loads history
- [ ] Send message → streaming works
- [ ] Tool call → executes correctly
- [ ] HITL approval → shows modal, executes on confirm

**Visual tests:**
- [ ] 7 recent chats visible without scrolling
- [ ] Older chats in expander
- [ ] Data list shows all files with type labels
- [ ] Active dataset label in corner
- [ ] Monitor status color-coded
- [ ] Typography hierarchy clear
- [ ] Spacing looks clean
- [ ] No visual regressions

**Code quality:**
- [ ] Each module under 200 lines
- [ ] No circular imports
- [ ] Each module independently importable
- [ ] Session state managed in one place
- [ ] No duplicated code

---

## Visual Mockup (ASCII)

```
┌────────────────────────────────────────────────────────────────┐
│  SIDEBAR                     │  MAIN CHAT AREA                 │
├──────────────────────────────┼─────────────────────────────────┤
│ 🤖 AI Assistant              │  📊 Active: sales.csv (CSV)     │
│                              │                                 │
│ ──── Chat History ────       │  ┌─────────────────────────┐   │
│ • Q4 Sales Analysis          │  │ User: avg by region?    │   │
│ • Wheat Price Monitoring     │  └─────────────────────────┘   │
│ • Database Migration         │                                 │
│ • Python Debugging           │  ┌─────────────────────────┐   │
│ • API Integration            │  │ Bot: Analyzing...       │   │
│ • Budget Planning            │  │                         │   │
│ • Holiday Schedule           │  │ Region | Avg           │   │
│                              │  │ ─────────────────       │   │
│ ▶ More chats (15)            │  │ North  | $1,234        │   │
│                              │  │ South  | $987          │   │
│ [+ New Chat]                 │  └─────────────────────────┘   │
│                              │                                 │
│ ──── Data & Databases ────   │                                 │
│ [📤 Upload]                  │  ┌─────────────────────────┐   │
│                              │  │ 💬 Your message...      │   │
│ Available Data:              │  └─────────────────────────┘   │
│  sales.csv (CSV, 234KB)      │         [Send]                 │
│  analytics.db (SQL, 1.2MB)   │                                 │
│  inventory.xlsx (Excel, 456KB)│                                │
│                              │                                 │
│ ──── Pipeline Monitor ────   │                                 │
│ [☑ Commodity Prices]         │                                 │
│ [☐ API Health]               │                                 │
│                              │                                 │
│ Interval: [30 min ▼]         │                                 │
│ [Start] [Stop]               │                                 │
│                              │                                 │
│ ● Status: RUNNING            │                                 │
└──────────────────────────────┴─────────────────────────────────┘
```

---

## Success Criteria

✅ **Clarity:** New user can navigate without explanation
✅ **Organization:** Related things grouped together
✅ **Scannability:** Visual hierarchy obvious at glance
✅ **Maintainability:** Each module under 200 lines
✅ **Functionality:** Everything works exactly as before
✅ **Polish:** Professional look, no amateur vibes

---

## What NOT to Change

❌ Backend logic (backend.py, tools/, subgraphs/)
❌ Monitoring system (monitoring/)
❌ Data storage paths (data/)
❌ HITL approval logic (just UI presentation)
❌ Streaming implementation (just container layout)
❌ Tool calling (just display formatting)

Only touch `frontend.py` and create the new `frontend/` module.

---

## Final Validation

Before merging:

```bash
# 1. All functional tests pass
pytest tests/test_frontend_smoke.py

# 2. No import errors
python -c "from frontend.main import *; print('[OK]')"

# 3. Visual check
streamlit run frontend.py
# Manually verify:
#  - 7 recent chats visible
#  - Data list unified
#  - Monitor section clean
#  - HITL flows work
#  - Active dataset label shows
#  - Streaming works

# 4. Code metrics
find frontend/ -name "*.py" -exec wc -l {} \;
# Each file should be < 250 lines

# 5. No regressions
# Upload CSV → analyze → monitor → all work as before
```

If all ✓, merge to main.

---

## Notes

- **Keep it simple** — don't over-engineer
- **Test incrementally** — one section at a time
- **Preserve functionality** — UI only, no logic changes
- **Document as you go** — comments in each module
- **No emojis in code** — Windows cp1252 (except in UI strings, those render in browser)


