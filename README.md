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

## 🚀 Running the Application

### Startup Operations (3 services required)

```bash
# Terminal 1: Start Redis (memory + cache backend)
redis-server
# Or with Docker:
docker run -d -p 6379:6379 --name redis-chatbot redis:latest

# Terminal 2: Start ChromaDB (episodic memory + RAG vector store)
chroma run --host localhost --port 8000

# Terminal 3: Start the Streamlit app
streamlit run frontend.py
```

### Service Dependencies
- **Redis** (port 6379) — Required for memory + caching
- **ChromaDB** (port 8000) — Required for RAG + episodic memory
- **Streamlit** (port 8501) — App UI

**Graceful Degradation:** App works without Redis/ChromaDB (memory/cache disabled, but chat still functions).

## 🏗️ Architecture

### Tech Stack
- **LangGraph** — Agentic chatbot with SqliteSaver state management
- **Streamlit** — Interactive web UI with real-time streaming
- **ChromaDB** — Vector database for semantic search + episodic memory
- **SQLite** — Chat history + data analysis database
- **Redis** — User memory + response caching + token tracking
- **OpenAI** — LLM backend (gpt-4o-mini for chat, gpt-4o for analysis)
- **Pandas** — Data analysis

### Storage Layer Breakdown

| Storage | Data | TTL | Lookup | Purpose |
|---------|------|-----|--------|---------|
| **SQLite (chat_memory.db)** | Chat messages, thread metadata | Forever | O(n) | Persistent chat history, conversation recovery |
| **SQLite (data/*.db)** | Uploaded CSV/Excel data | Forever | O(1) SELECT | Data analysis queries, historical records |
| **Redis** | Semantic profile (facts), procedural profile (prefs), session state | 2h / Forever | O(1) hash | Fast user context, working memory, no LLM latency |
| **ChromaDB** | Episodic memory (conversations), RAG chunks (documents) | Forever | 200-500ms | Semantic search context, document retrieval |
| **Redis Cache Layer** | Response cache, semantic cache, tool results, node outputs, token usage | 24h / 1h | O(1) hash | Speed optimization (50-100x faster), API tracking |
| **Filesystem** | Chroma index files, plots/visualizations, uploaded files | Until deleted | File I/O | Vector index persistence, generated charts, user uploads |

### Data Flow: How Memory + Cache Works

```
User Query
    ↓
[1] Check Response Cache (24h, exact match)
    → HIT: Return cached response (50-100x faster) ✅
    → MISS: Continue
    ↓
[2] Load Long-Term Memory
    ├─ Semantic Profile (Redis O(1)) — facts, interests
    ├─ Procedural Profile (Redis O(1)) — preferences
    └─ Episodic Context (ChromaDB 200-500ms) — recent conversations
    ↓
[3] Build <memory> Block (400 token limit max)
    ↓
[4] Inject into System Prompt → LLM Call
    ↓
[5] Track Tokens (extract from response metadata)
    → Store input + output tokens in Redis
    ↓
[6] Cache Response (24h TTL)
    ↓
Response to User
```

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

## 🎯 Latest Implementation: Memory System + Caching + Token Tracking (This Session - April 25, 2026)

### Memory System Features (April 25, 2026)
- ✅ **Semantic Memory** — Persistent user facts (name, age, interests) in Redis
- ✅ **Procedural Memory** — Communication preferences (tone, format, language) in Redis
- ✅ **Episodic Memory** — Conversation context and events in ChromaDB with semantic search
- ✅ **Session State** — Working context with 2-hour TTL in Redis
- ✅ **Memory Injection** — Automatic context loading into LLM prompts
- ✅ **Monitor-to-Memory Bridge** — Monitor events auto-update memory
- ✅ **Sidebar Profile Display** — User profile facts and preferences in real-time

### Optional Caching Layer (50-100x Speed Improvement)
- ✅ **Response Cache (24h)** — Exact LLM responses (50-100x faster on hit)
- ✅ **Semantic Cache (24h)** — Similar question matching (15-30x faster)
- ✅ **Tool Cache (1h)** — Stock/commodity API results (avoid redundant calls)
- ✅ **RAG Cache (1h)** — Document chunks (faster retrieval)
- ✅ **Node Cache (1h)** — LangGraph node results (skip recomputation)
- ✅ **Cache Monitoring** — Real-time cache stats in sidebar
- ✅ **Graceful Degradation** — Chat works fine if Redis/ChromaDB unavailable

### API Token Usage Tracking
- ✅ **Per-Session Token Tracking** — Input + output tokens stored in Redis (24h TTL)
- ✅ **Automatic Extraction** — Parses tokens from LLM response metadata
- ✅ **Sidebar Display** — Shows cumulative input/output tokens in Memory & Cache Status
- ✅ **Session-Scoped** — Resets after 24 hours, separate tracking per session
- **Use Case:** Monitor API costs, identify token-heavy queries, optimize prompt efficiency

### RAG Improvements
- ✅ **Fast Document Deletion** — Batch delete (100x faster, no slow indexing)
- ✅ **Clean Index Removal** — Proper ChromaDB cleanup
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

## 💾 Backup & Data Persistence

### Automatic Persistence
All data is automatically saved:
- **Redis** — Auto-saves to `dump.rdb` on shutdown (RDB snapshots)
- **ChromaDB** — Auto-persists vectors to `data/chroma_db/` on every write
- **SQLite** — Auto-commits to `chat_memory.db` after operations

### Manual Backups

**Backup Redis Data**
```bash
# Trigger background save
redis-cli BGSAVE

# Backup dump.rdb with timestamp
cp dump.rdb dump.rdb.$(date +%Y%m%d_%H%M%S)

# Verify last save time
redis-cli LASTSAVE
```

**Backup ChromaDB Data**
```bash
# Stop ChromaDB first (Ctrl+C) to ensure flush
# Then backup the entire directory
cp -r data/chroma_db data/chroma_db.$(date +%Y%m%d_%H%M%S)
```

**Complete Backup Script**
```bash
#!/bin/bash
# backup.sh - Backup all data
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "[INFO] Backing up Redis..."
redis-cli BGSAVE && sleep 2
cp dump.rdb $BACKUP_DIR/dump.rdb

echo "[INFO] Backing up ChromaDB..."
cp -r data/chroma_db $BACKUP_DIR/chroma_db

echo "[INFO] Backing up chat history..."
cp chat_memory.db $BACKUP_DIR/chat_memory.db

echo "[OK] Backup complete: $BACKUP_DIR"
```

### Restore from Backup

**Restore Redis**
```bash
redis-cli shutdown          # Stop Redis
cp dump.rdb.backup dump.rdb # Restore backup
redis-server                # Restart
```

**Restore ChromaDB**
```bash
# Ctrl+C to stop ChromaDB
rm -rf data/chroma_db
cp -r chroma_db.backup data/chroma_db
# Restart ChromaDB
chroma run --host localhost --port 8000
```

### Storage Locations

| Data | Location | Size | Type |
|------|----------|------|------|
| Chat history | `chat_memory.db` | ~10-100 MB | SQLite |
| User memory | Redis `dump.rdb` | ~1-5 MB | RDB snapshot |
| RAG documents | `data/chroma_db/` | ~50-500 MB | Vector index |
| Visualizations | `data/plots/` | ~10-50 MB | PNG/SVG files |
| Uploaded files | `data/uploaded_files/` | Variable | User uploads |

### Graceful Shutdown

Stop all services cleanly (in this order):
```bash
# Terminal 3: Stop Streamlit
# Press Ctrl+C

# Terminal 2: Stop ChromaDB
# Press Ctrl+C

# Terminal 1: Stop Redis
redis-cli shutdown
# Or Docker: docker stop redis-chatbot
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
