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

### Data Management & RAG
- **Unified Data Section** — Upload CSV, Excel, SQL, PDF, Word files in one location
- **CSV/Excel Analysis** — Pandas-powered data analysis with visualizations
- **SQL Databases** — Upload .sql files, run SELECT queries
- **Document Upload** — Index PDF, Word, CSV, Excel for semantic search
- **C-RAG + Self-RAG** — Dual-layer quality control with 4 grading prompts
  - Document relevance verification (C-RAG)
  - Hallucination detection (Self-RAG)
  - Answer usefulness validation (Self-RAG)
  - Web search fallback (DuckDuckGo)
  - Max 3 retrieval/generation loops with metrics
- **ChromaDB Vector DB** — Semantic search with proper indexing

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

## 🎯 Latest Implementation: Memory System (This Session)

### Memory System Features (April 24, 2026)
- ✅ **Semantic Memory** — Persistent user facts (name, age, interests, goals) in Redis
- ✅ **Procedural Memory** — Communication preferences (tone, format, language) in Redis
- ✅ **Episodic Memory** — Conversation context and events in ChromaDB with semantic search
- ✅ **Session State** — Working context with 2-hour TTL in Redis
- ✅ **Memory Injection** — Automatic context loading and injection into LLM prompts
- ✅ **Monitor-to-Memory Bridge** — Monitor events (commodity alerts, API issues) auto-update memory
- ✅ **Sidebar Profile Display** — Show user profile facts and preferences
- ✅ **Graceful Degradation** — Chat works fine if Redis/ChromaDB unavailable
- ✅ **Complete Specs** — 15 detailed spec files in `.claude/specs/memory/`

### Architecture
```
User Message → Load LongTermMemory
├─ Semantic Profile (Redis) [O(1)]
├─ Procedural Profile (Redis) [O(1)]
└─ Episodic Context (ChromaDB) [200-500ms]
    ↓
Build <memory> Block (400 token limit)
    ↓
Inject into System Prompt → LLM (personalized response)
```

### Testing
- ✅ Memory system tests passing (models, context builder)
- ✅ Backend integration verified (memory injection in chat_node)
- ✅ Frontend integration verified (session management, sidebar display)
- ✅ Monitor bridge ready (commodity alerts → semantic.interests)

---

## 🎯 Previous Implementation: C-RAG + Self-RAG

### Major Features Implemented (April 24, 2026)
- ✅ **C-RAG + Self-RAG System** — Dual-layer quality control for RAG queries
  - Document relevance grading (Prompt 1 - IsRel)
  - Answer generation from context (Prompt 2)
  - Hallucination detection (Prompt 3 - IsSup)
  - Usefulness validation (Prompt 4 - IsUse)
  - Loop control: max 3 retrieval/generation iterations
  - 30-second timeout with metrics tracking
  
- ✅ **Document Upload UI** — Accept PDF, Word, CSV, Excel files for RAG indexing
  - ChromaDB vector storage with OpenAI embeddings
  - Document metadata and preview
  - Organized sidebar with collapsed sections

- ✅ **Document Management** — Rename and delete uploaded documents with HITL
  - Indexed documents display with count
  - Per-document rename/delete buttons
  - Deletion confirmation warning
  - Full HITL workflow

- ✅ **Web Search Fallback** — DuckDuckGo integration when all docs irrelevant
  - Automatic fallback to web results
  - Metrics tracking for fallback usage

- ✅ **Sidebar Reorganization**
  - 📤 UPLOADS (RAG Documents, CSV/Excel, SQL Files)
  - 📚 DOCUMENTS (Indexed Documents with management)
  - 📊 DATASETS (Available Datasets)
  - 🗄️ DATABASES (Available Databases)
  - ⚙️ MONITORING (Monitor controls)

- ✅ **Code Quality Improvements**
  - Proper environment variable loading (.env)
  - Response content parsing fixes
  - Indentation corrections
  - Comprehensive dependency management

### Previous Sessions
- ✅ Minimal modular refactoring (frontend/utils.py)
- ✅ 7 recent chats + scrollable older chats expander
- ✅ Table-based monitor reports
- ✅ HITL email approval workflows
- ✅ Multi-channel alert system

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
