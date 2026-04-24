# Chat Bot — LangGraph + Streamlit

Multi-tool AI assistant with monitoring, analysis, and real-time alerts.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run frontend.py
```

## 📋 Features

### Chat Interface
- Multi-thread chat history with persistent storage
- 7 recent chats visible + older chats in scrollable expander
- Real-time message streaming with tool execution
- Support for 19+ AI tools (search, analysis, stocks, commodities, email, etc.)

### Data Management
- **Unified Data Section** — Upload CSV, Excel, SQL files in one dropdown
- **CSV/Excel Analysis** — Pandas-powered data analysis with visualizations
- **SQL Databases** — Upload .sql files, run SELECT queries
- **ChromaDB RAG** — Semantic search across uploaded datasets

### Monitoring & Alerts
- **Real-time Monitor** — Check commodity prices, API health, file integrity, database health
- **Table-Based Reports** — System status displayed as organized dataframes
- **Multi-Channel Alerts** — Send reports to Slack (automated) or Gmail (HITL approval)
- **Scheduled Reports** — Set daily report delivery times
- **Issue Detection** — Tracks WARN, ALERT, DOWN, ERROR, SURGE statuses

### HITL (Human-in-the-Loop)
- Email report approval with recipient input
- CSV upload confirmation
- Chat deletion confirmation
- Data visualization approval workflow

## 🏗️ Architecture

### Tech Stack
- **LangGraph** — Agentic chatbot with SqliteSaver state management
- **Streamlit** — Interactive web UI with real-time streaming
- **ChromaDB** — Vector database for semantic search
- **SQLite** — Local data analysis database
- **OpenAI** — LLM backend
- **Pandas** — Data analysis

## 📊 Sidebar Organization

1. **My Conversations**
   - 7 recent chats (always visible)
   - "More chats" expander for older threads
   - NEW CHAT button

2. **Available Tools**
   - 19 tools list (collapsible)
   - Quick reference for AI capabilities

3. **Data Analysis**
   - CSV/Excel upload
   - SQL upload
   - Available datasets list
   - Available databases with schema

4. **Pipeline Monitor**
   - Monitor selection (Commodity Prices, API Health, etc.)
   - Check interval setting
   - Start/Stop controls
   - Report actions (Email/Slack + scheduling)

## 🔍 Monitor System

### Checks Run
- **Commodity Prices** — Wheat, soy, corn, sugar price tracking
- **API Health** — DuckDuckGo, yfinance, Calendarific, Gmail SMTP, Slack
- **Data Files** — File integrity and age monitoring
- **Database Health** — SQLite database status and size
- **ChromaDB** — Vector DB document count and disk usage
- **App Health** — Memory, CPU, disk utilization

### Report Format
Reports display as organized tables showing:
- Issues Table (WARN, ALERT, DOWN, ERROR, SURGE)
- Commodities Table (price changes)
- APIs Table (response times)
- Files Table (problem files only)
- Databases Table (size, row counts)
- ChromaDB Table (document count, disk)
- App Health Table (resource usage)

### Status Indicators
- `[OK]` — System healthy
- `[WARN]` — Minor issue (permissions, stale data)
- `[ALERT]` — Critical alert
- `[DOWN]` — Service unavailable
- `[ERROR]` — Error state
- `[SURGE]` — Price surge detected
- `[STALE]` — Data older than 48 hours

## 💬 Chat Commands

### Monitor Commands
- `show monitor status` — Current monitoring state
- `load report` / `show report` — Display latest monitor results as tables
- `stop monitoring` — Stop all monitors
- `pause reports` — Temporarily stop scheduled reports
- `send report now` — HITL approval → send via Gmail
- `send to slack` — Send report to Slack immediately
- `schedule report` — HITL approval → set daily report time

## 🎯 Recent Implementation (This Session)

### Completed Features
- ✅ Minimal modular refactoring (frontend/utils.py)
- ✅ 7 recent chats + scrollable older chats expander
- ✅ Reorganized sidebar (Conversations → Tools → Data → Monitor)
- ✅ Table-based monitor reports (HTML email, Slack markdown, Streamlit dataframes)
- ✅ "All systems work fine" message only when truly healthy
- ✅ Fixed DuckDuckGo API check
- ✅ Load report chat commands with table display
- ✅ HITL email input for "Send report to:" confirmation
- ✅ Removed duplicate SQL uploader (fixed key collision)
- ✅ Fixed false WARN on small files (.gitkeep, JSON state files)

### Architecture Decisions Made

**Frontend Refactoring Strategy**
- Chose ultra-conservative modular approach
- Only extracted small utility functions to frontend/utils.py
- Reason: Comprehensive refactoring caused state management issues
- Preserves stability while improving code organization
- Can expand to full FRONTEND_REDESIGN_PROMPT structure in future if needed

**Table-Based Reporting**
- Implemented three report formats:
  - HTML tables for email (styled, color-coded)
  - Markdown tables for Slack (monospace code blocks)
  - Interactive Streamlit dataframes for chat display
- Reason: Different channels have different formatting capabilities

**Sidebar Organization**
- Changed order to: Conversations → Tools → Data → Monitor
- 7 recent chats visible + scrollable expander for older
- Reason: Users access conversations most frequently, then tools, then data

**File Monitoring**
- Skip .gitkeep files entirely
- Removed size < 1KB WARN threshold
- Reason: Small config files are normal and healthy
- Decision: Only warn on unreadable [ERROR] or stale [STALE] files

## 🧪 Testing

Run the app and verify:
- [x] Sidebar shows correct section order
- [x] 7 recent chats visible, older chats in expander
- [x] Chat history saves and loads
- [x] Monitor start/stop buttons work
- [x] Monitor reports display as tables
- [x] Gmail report HITL shows email input
- [x] File monitor shows no false WARN for small files
- [x] Load report command displays table format

## 📝 Configuration

Set environment variables in `.env`:

```env
OPENAI_API_KEY=sk-...
GMAIL_USER=your-email@gmail.com
GMAIL_RECIPIENT=recipient@gmail.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
CALENDARIFIC_API_KEY=...
```

## 📚 Documentation

- **FRONTEND_REDESIGN_PROMPT.md** — Updated spec showing planned vs. implemented features
- **.claude/specs/** — Detailed tool, pipeline, and monitoring specifications

## 🧠 Knowledge Graph (graphify)

A persistent knowledge graph of the codebase is maintained in `graphify-out/`:
- **graph.json** (11 MB) — 7,079 nodes, 48 communities, 24,021 edges
- **graph.graphml** — Open in Gephi for visual exploration
- **GRAPH_REPORT.md** — God nodes, surprising connections, suggested questions

### Querying the Graph (Zero Token Cost)

For codebase questions, use graphify instead of asking Claude directly:

```bash
# Show all APIs in the project
/graphify query "show me all apis"

# Trace a specific dependency
/graphify path "frontend.py" "monitor_tool"

# Explain a component
/graphify explain "check_apis"

# Find shortest connection between concepts
/graphify path "stock_tool" "slack_alert"
```

### Token Efficiency Comparison

| Approach | Token Cost | Best For | Speed |
|----------|-----------|----------|-------|
| **graphify query** | $0 (no LLM) | Codebase facts, APIs, dependencies | ~1s |
| **Claude direct** | ~500 tokens | Context, reasoning, "why" questions | Instant |

**Example:** 100 API queries via graphify = $0. Same queries to Claude = ~$0.10 (+ slower).

### When to Use Each

**Use graphify** for:
- What APIs exist?
- How does X call Y?
- Where is rate limiting implemented?
- What components talk to the monitor?

**Use Claude** for:
- Why was this architecture chosen?
- How should I implement feature X?
- Code review or optimization advice
- Multi-file refactoring
