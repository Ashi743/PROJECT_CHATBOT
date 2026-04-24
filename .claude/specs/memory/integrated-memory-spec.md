# SPEC: Spendly Chatbot with Memory System & Monitoring Integration
# Version: 3.0 | OpenAI-only | Streamlit + LangGraph + Redis + ChromaDB
# Integrates memory management into existing backend.py + frontend.py + monitoring

---

## OVERVIEW

Your existing chatbot (backend.py, frontend.py) gets three new capabilities:

1. **Memory Layer** — Persistent user facts, conversation history, preferences
2. **Monitor-to-Memory Bridge** — When monitors detect events, they auto-update user memory
3. **Synchronized Session State** — Memory is loaded at session start, saved at session end

**No breaking changes.** The chatbot works exactly as before. Memory is additive.

---

## FILE STRUCTURE

```
spendly/
├── backend.py                    (MODIFIED)
│   ├── Import memory manager
│   ├── Add memory-aware LLM routing
│   └── Add memory cleanup on session end
│
├── frontend.py                   (MODIFIED)
│   ├── Load user memory on session start
│   ├── Display memory in sidebar (optional)
│   └── Update memory on chat end
│
├── memory/
│   ├── __init__.py
│   ├── config.py                 # All memory constants
│   ├── models.py                 # Pydantic models
│   ├── store.py                  # MemoryStore (Redis + Chroma abstraction)
│   ├── short_term.py             # Session + 5 cache layers
│   ├── long_term.py              # Episodic/semantic/procedural
│   ├── loader.py                 # load_long_term_memory()
│   ├── summariser.py             # Session-end summarisation
│   └── sync_wrapper.py           # Sync wrappers for Streamlit
│
├── monitoring/runner.py          (MODIFIED)
│   └── Add memory update callbacks to monitoring checks
│
└── monitoring/memory_bridge.py   (NEW)
    └── Connect monitor results → user memory updates
```

---

## 1. MEMORY CONFIG (`memory/config.py`)

```python
import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI ────────────────────────────────────────────────────────────────
OPENAI_API_KEY        = os.environ["OPENAI_API_KEY"]
CHAT_MODEL            = "gpt-4o"
SUMMARISER_MODEL      = "gpt-4o-mini"
EMBEDDING_MODEL       = "text-embedding-3-small"
EMBEDDING_DIM         = 1536

# ── Redis ─────────────────────────────────────────────────────────────────
REDIS_URL             = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# TTLs (seconds)
TTL_SESSION           = 7_200    # 2 h  — working context
TTL_RESP_CACHE        = 86_400   # 24 h — exact response cache
TTL_SEM_CACHE         = 86_400   # 24 h — semantic cache
TTL_RAG_CACHE         = 3_600    # 1 h  — RAG chunk cache
TTL_TOOL_CACHE        = 3_600    # 1 h  — tool/API result cache
TTL_NODE_CACHE        = 3_600    # 1 h  — pipeline node cache

# Key prefixes
PFX_SESSION           = "session"
PFX_RESP              = "cache:resp"
PFX_SEM               = "cache:sem"
PFX_RAG               = "cache:rag"
PFX_TOOL              = "cache:tool"
PFX_NODE              = "cache:node"
PFX_MEM_SEMANTIC      = "memory:semantic"
PFX_MEM_PROCEDURAL    = "memory:procedural"

# Session
MAX_TURNS             = 12
SUMMARISE_AFTER_TURNS = 10

# Similarity threshold
SEM_CACHE_THRESHOLD   = 0.85
EPISODIC_MIN_IMP      = 0.3
EPISODIC_TOP_K        = 5
MEMORY_BLOCK_MAX_TOKENS = 400

# ChromaDB
CHROMA_HOST           = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT           = int(os.getenv("CHROMA_PORT", 8000))

COL_EPISODIC          = "episodic_{user_id}"
COL_SEMANTIC          = "semantic_{user_id}"

# ── Monitoring Memory Bridge ──────────────────────────────────────────────
# When monitors detect events, store them as episodic memory with this importance
MONITOR_EVENT_IMPORTANCE = 0.7   # Higher = more likely to be retrieved
MONITOR_MEMORY_ENABLED = True    # Set to False to disable monitor → memory updates
```

---

## 2. MEMORY MODELS (`memory/models.py`)

```python
from __future__ import annotations
from typing import Any, Literal, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class Turn(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class SessionState(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime
    last_active: datetime
    turn_count: int = 0
    working_context: list[Turn] = []
    active_topic: str = ""
    pending_tasks: list[str] = []


class SemanticProfile(BaseModel):
    """User facts — all optional, filled incrementally by monitors + summariser"""
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    income_monthly: Optional[float] = None        # ₹
    income_source: Optional[str] = None
    dependents: Optional[int] = None
    risk_tolerance: Optional[Literal["low","medium","high"]] = None
    financial_goals: list[str] = []
    current_savings: Optional[float] = None
    monthly_expenses: Optional[float] = None
    debt_emi: Optional[float] = None
    investment_style: Optional[str] = None
    preferred_banks: list[str] = []
    tax_bracket: Optional[str] = None
    
    # Monitor-detected facts (stored but not manually edited)
    commodity_interests: list[str] = []          # From monitor: "User follows wheat, corn"
    api_health_checks: bool = False              # From monitor: "User enabled API monitoring"
    last_monitor_alert: Optional[datetime] = None
    
    updated_at: Optional[datetime] = None


class ProceduralProfile(BaseModel):
    """How to behave with this user"""
    preferred_language: str = "English"
    response_format: Literal["concise","detailed","bullet_points","narrative"] = "concise"
    preferred_currency_fmt: str = "₹"
    greeting_style: str = ""
    topics_to_avoid: list[str] = []
    known_triggers: list[str] = []
    recurring_queries: list[str] = []
    last_completed_workflows: list[str] = []
    feedback_signals: dict[str, list[str]] = {"positive": [], "negative": []}
    tone: Literal["formal","friendly","neutral"] = "friendly"
    updated_at: Optional[datetime] = None


class EpisodicDoc(BaseModel):
    """Single document in ChromaDB episodic collection"""
    doc_id: str
    document: str
    user_id: str
    type: Literal[
        "session_summary","raw_turn","user_note","event","emotional_signal","monitor_event"
    ]
    session_id: str
    created_at: datetime
    importance: float = Field(ge=0.0, le=1.0)
    tags: list[str] = []


class MonitorEvent(BaseModel):
    """Event detected by monitoring system"""
    event_type: str           # "commodity_alert", "api_down", "storage_issue"
    severity: Literal["info","warning","alert","error"]
    message: str
    timestamp: datetime
    commodities: Optional[list[str]] = None    # For commodity events
    affected_components: Optional[list[str]] = None  # For system events
    
    def to_episodic_doc(self, user_id: str, session_id: str) -> EpisodicDoc:
        """Convert monitor event to episodic memory"""
        doc_text = f"[{self.severity.upper()}] {self.event_type}: {self.message}"
        return EpisodicDoc(
            doc_id=f"mon_{user_id}_{self.timestamp.timestamp()}",
            document=doc_text,
            user_id=user_id,
            type="monitor_event",
            session_id=session_id,
            created_at=self.timestamp,
            importance=0.7,  # From config
            tags=[self.event_type, self.severity]
        )


class LongTermMemory(BaseModel):
    """Assembled context injected into each prompt"""
    semantic: SemanticProfile
    procedural: ProceduralProfile
    episodic_chunks: list[str] = []


class SummariserOutput(BaseModel):
    """Structured output from gpt-4o-mini summariser"""
    session_summary: str
    events: list[str] = []
    emotional_signal: Optional[str] = None
    importance: float = Field(ge=0.0, le=1.0, default=0.5)
    semantic_updates: dict[str, Any] = {}
    procedural_updates: dict[str, Any] = {}
```

---

## 3. MEMORY STORE ABSTRACTION (`memory/store.py`)

(Copy from STREAMLIT_MEMORY_SPEC.md section 5 — same MemoryStore class)

---

## 4. SHORT-TERM MEMORY (`memory/short_term.py`)

(Copy from STREAMLIT_MEMORY_SPEC.md section 6 — same session + cache layers)

---

## 5. LONG-TERM MEMORY (`memory/long_term.py`)

(Copy from STREAMLIT_MEMORY_SPEC.md section 7 — same episodic/semantic/procedural)

---

## 6. MEMORY LOADER (`memory/loader.py`)

(Copy from STREAMLIT_MEMORY_SPEC.md section 8)

---

## 7. CONTEXT BUILDER (`memory/context_builder.py`)

(Copy from STREAMLIT_MEMORY_SPEC.md section 9)

---

## 8. SESSION-END SUMMARISER (`memory/summariser.py`)

(Copy from STREAMLIT_MEMORY_SPEC.md section 10)

---

## 9. SYNC WRAPPERS (`memory/sync_wrapper.py`)

(Copy from STREAMLIT_MEMORY_SPEC.md section 11)

---

## 10. MONITOR-TO-MEMORY BRIDGE (`monitoring/memory_bridge.py`)

**NEW FILE** — Connects monitoring events to memory updates.

```python
"""
Monitor-to-Memory Bridge

When monitoring detects events (commodity alerts, API issues, etc.),
this module auto-updates user memory so the chatbot knows about them.
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional
import logging

from memory.models import MonitorEvent, EpisodicDoc
from memory.long_term import save_episodic, update_semantic_memory
from memory.sync_wrapper import sync_load_semantic

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def store_monitor_event(
    user_id: str,
    session_id: str,
    event: MonitorEvent
) -> dict:
    """
    Store a monitoring event as episodic memory.
    Called when monitor detects a noteworthy event.

    Args:
        user_id: User whose memory to update
        session_id: Current session ID
        event: MonitorEvent from monitoring system

    Returns:
        {status: "ok", doc_id: "..."}
    """
    try:
        # Convert event to episodic document
        doc = event.to_episodic_doc(user_id, session_id)

        # Save to Chroma
        await save_episodic(doc)

        # Also update semantic memory if commodity event
        if event.event_type == "commodity_alert" and event.commodities:
            sem = await sync_load_semantic(user_id)
            
            # Add to user's commodity interests
            existing = set(sem.commodity_interests or [])
            for comm in event.commodities:
                existing.add(comm)
            
            updates = {
                "commodity_interests": list(existing),
                "last_monitor_alert": datetime.now(timezone.utc).isoformat()
            }
            await update_semantic_memory(user_id, updates)

        logger.info(f"Monitor event stored for {user_id}: {event.event_type}")
        return {"status": "ok", "doc_id": doc.doc_id}

    except Exception as e:
        logger.error(f"Failed to store monitor event: {e}")
        return {"status": "error", "message": str(e)}


def sync_store_monitor_event(
    user_id: str,
    session_id: str,
    event: MonitorEvent
) -> dict:
    """Sync wrapper for Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(
        store_monitor_event(user_id, session_id, event)
    )
```

---

## 11. MODIFIED BACKEND (`backend.py` — changes only)

```python
# Add at top
from memory.sync_wrapper import sync_load_long_term_memory
from llm.context_builder import build_messages
from memory.models import SessionState
import uuid

# Modify chat_node to inject memory
def chat_node(state: chatState):
    messages = state["messages"]
    
    # Extract user_id and session_id from Streamlit session state (see frontend changes)
    user_id = st.session_state.get("user_id", "default")
    session_id = st.session_state.get("current_thread_id", str(uuid.uuid4()))
    
    # Load long-term memory
    if messages:
        user_msg = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        ltm = sync_load_long_term_memory(user_id, user_msg)
        
        # Rebuild messages with memory context
        memory_block = _build_memory_block(ltm)
        system_prompt = (
            f"You are Spendly, a personal finance AI assistant.\n"
            f"You help with budgeting, expense tracking, goal setting, and planning.\n\n"
            f"{memory_block}\n\n"
            f"Always refer to user context above before responding."
        )
        
        # Prepend memory-aware system message
        from langchain_core.messages import SystemMessage
        messages = [SystemMessage(content=system_prompt)] + messages
    
    # Route to appropriate LLM based on analysis keywords or recent results
    if _requires_analysis_llm(messages):
        analysis_llm_with_tools = analysis_llm.bind_tools(tools)
        response = analysis_llm_with_tools.invoke(messages)
    else:
        response = llm_with_tools.invoke(messages)
    
    return {'messages': [response]}


def _build_memory_block(ltm) -> str:
    """Build <memory> block for context injection"""
    sem = ltm.semantic
    proc = ltm.procedural
    
    facts_parts = []
    if sem.name:              facts_parts.append(f"Name: {sem.name}")
    if sem.income_monthly:    facts_parts.append(f"Income: ₹{sem.income_monthly:,.0f}/mo")
    if sem.financial_goals:   facts_parts.append(f"Goals: {', '.join(sem.financial_goals)}")
    if sem.commodity_interests:
        facts_parts.append(f"Monitors: {', '.join(sem.commodity_interests)}")
    
    pref_parts = [
        f"Format: {proc.response_format}",
        f"Tone: {proc.tone}",
    ]
    
    lines = ["<memory>"]
    if facts_parts:
        lines.append("[facts] " + " | ".join(facts_parts))
    lines.append("[prefs]  " + " | ".join(pref_parts))
    if ltm.episodic_chunks:
        lines.append("[recent] " + " → ".join(ltm.episodic_chunks[:2]))
    lines.append("</memory>")
    
    return "\n".join(lines)
```

---

## 12. MODIFIED FRONTEND (`frontend.py` — key changes)

```python
# Add at top (after imports)
from memory.sync_wrapper import (
    sync_load_session, sync_create_session, sync_append_turn,
    sync_load_long_term_memory, sync_summarise_session
)
from uuid import uuid4

# ── Modified session initialization ──

if "current_thread_id" not in st.session_state:
    st.session_state["current_thread_id"] = str(uuid4())

if "user_id" not in st.session_state:
    st.session_state["user_id"] = "default_user"  # Can prompt user to login

if "memory_session" not in st.session_state:
    st.session_state["memory_session"] = None

if "user_memory" not in st.session_state:
    st.session_state["user_memory"] = None

# ── In sidebar, show memory profile ──

with st.sidebar:
    st.divider()
    st.subheader("👤 Your Profile (Memory)")
    
    # Load and display memory
    user_id = st.session_state.get("user_id", "default_user")
    try:
        from memory.sync_wrapper import sync_load_semantic, sync_load_procedural
        sem = sync_load_semantic(user_id)
        proc = sync_load_procedural(user_id)
        
        st.session_state["user_memory"] = {"semantic": sem, "procedural": proc}
        
        if sem.name:
            st.caption(f"👋 **{sem.name}**")
        if sem.income_monthly:
            st.caption(f"💰 ₹{sem.income_monthly:,.0f}/month")
        if sem.commodity_interests:
            st.caption(f"📊 Monitoring: {', '.join(sem.commodity_interests[:3])}")
        if sem.financial_goals:
            st.caption(f"🎯 Goals: {sem.financial_goals[0] if sem.financial_goals else 'None'}")
    except Exception as e:
        st.caption(f"[Memory loading disabled]")


# ── At chat start, load memory session ──

if st.session_state["chat_started"] and user_input:
    session_id = st.session_state["current_thread_id"]
    user_id = st.session_state["user_id"]
    
    # Load memory session at start of chat
    if st.session_state["memory_session"] is None:
        mem_sess = sync_load_session(session_id)
        if not mem_sess:
            mem_sess = sync_create_session(session_id, user_id)
        st.session_state["memory_session"] = mem_sess

    # After LLM response, update memory session
    # (after the chatbot.stream() loop completes)
    st.session_state["memory_session"] = sync_append_turn(
        st.session_state["memory_session"],
        user_input,
        display_response
    )


# ── At session end (when user stops chat), summarise ──

# Add button in sidebar or end of chat
if st.session_state["chat_started"]:
    if st.button("💾 Save Session to Memory", key="save_session_btn"):
        session_id = st.session_state["current_thread_id"]
        user_id = st.session_state["user_id"]
        sync_summarise_session(session_id, user_id)
        st.success("Session saved to long-term memory!")
        st.info("Your facts, goals, and preferences are now remembered for future chats.")
```

---

## 13. MODIFIED MONITORING (`monitoring/runner.py` — memory integration)

```python
# Add at top
from monitoring.memory_bridge import sync_store_monitor_event
from memory.models import MonitorEvent
from config import MONITOR_MEMORY_ENABLED
from datetime import datetime, timezone

# Modify run_selected_checks to include memory callbacks
def run_selected_checks(selections: list, user_id: str = "default_user", session_id: str = None) -> dict:
    """
    Run only selected checks and auto-update user memory with events.

    Args:
        selections: List of monitor names from sidebar
        user_id: User whose memory to update
        session_id: Current session ID (optional)

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
                
                # ── NEW: Store monitor events in memory ──
                if MONITOR_MEMORY_ENABLED:
                    _process_results_to_memory(
                        selection, results[selection], user_id, session_id
                    )
            except Exception as e:
                logger.error(f"Error running {selection}: {e}")
                results[selection] = {"status": "[ERROR]", "error": str(e)}

    return results


def _process_results_to_memory(
    check_name: str,
    results: dict,
    user_id: str,
    session_id: str
):
    """Convert check results to monitor events and store in memory"""
    if not session_id:
        session_id = f"monitor_{datetime.now().timestamp()}"
    
    # Example: Commodity alerts
    if check_name == "Commodity Prices" and isinstance(results, dict):
        for commodity, data in results.items():
            if isinstance(data, dict):
                status = data.get("status", "[OK]")
                if status in ["[ALERT]", "[SURGE]"]:
                    event = MonitorEvent(
                        event_type="commodity_alert",
                        severity="alert" if status == "[ALERT]" else "warning",
                        message=f"{commodity.upper()} {status}: {data.get('change', 0):.2f}% change",
                        timestamp=datetime.now(timezone.utc),
                        commodities=[commodity]
                    )
                    sync_store_monitor_event(user_id, session_id, event)
    
    # Example: API health
    elif check_name == "API Health" and isinstance(results, dict):
        for api, data in results.items():
            if isinstance(data, dict):
                status = data.get("status", "[OK]")
                if status == "[DOWN]":
                    event = MonitorEvent(
                        event_type="api_down",
                        severity="error",
                        message=f"{api} is down",
                        timestamp=datetime.now(timezone.utc),
                        affected_components=[api]
                    )
                    sync_store_monitor_event(user_id, session_id, event)
    
    # Example: Database/ChromaDB health
    elif check_name == "Database Health" and isinstance(results, dict):
        for db, data in results.items():
            if isinstance(data, dict):
                status = data.get("status", "[OK]")
                if status in ["[ERROR]", "[WARN]"]:
                    event = MonitorEvent(
                        event_type="storage_issue",
                        severity="warning",
                        message=f"Database {db}: {status}",
                        timestamp=datetime.now(timezone.utc),
                        affected_components=[db]
                    )
                    sync_store_monitor_event(user_id, session_id, event)


# Modify start_background to pass user_id
def start_background(
    selections: list,
    interval_minutes: int,
    user_id: str = "default_user",
    session_id: str = None
) -> threading.Thread:
    """
    Start background monitoring in daemon thread (for frontend).

    Args:
        selections: List of monitor names
        interval_minutes: Check interval in minutes
        user_id: User whose memory to update
        session_id: Current session ID
    """
    def job():
        results = run_selected_checks(selections, user_id, session_id)
        if has_issues(results):
            alert_issues(results)

    schedule.every(interval_minutes).minutes.do(job)

    def thread_loop():
        from utils.runtime_state import get_flag
        while not get_flag("monitor_stop_requested", False):
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=thread_loop, daemon=True)
    thread.start()
    return thread
```

---

## 14. FRONTEND MONITORING BUTTON UPDATE

In `frontend.py`, modify the monitor start button:

```python
if start_btn and not st.session_state.get("monitor_running"):
    # ... existing code ...
    
    from monitoring.runner import start_background, run_selected_checks
    
    # Get current user/session for memory updates
    user_id = st.session_state.get("user_id", "default_user")
    session_id = st.session_state.get("current_thread_id")
    
    thread = start_background(
        selections,
        interval_minutes,
        user_id=user_id,          # ← NEW: Pass user_id
        session_id=session_id       # ← NEW: Pass session_id
    )
    
    st.session_state["monitor_running"] = True
    # ... rest of existing code ...
    
    # Initial check also updates memory
    results = run_selected_checks(
        selections,
        user_id=user_id,
        session_id=session_id
    )
```

---

## 15. SETUP & DEPENDENCIES

### New `requirements.txt` entries

```
redis[asyncio]>=5.0.1
chromadb>=0.5.0
pydantic>=2.7.0
python-ulid>=2.2.0
numpy>=1.26.0
```

(Keep existing dependencies: langchain, streamlit, yfinance, etc.)

### New `.env` entries

```
REDIS_URL=redis://localhost:6379/0
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Monitoring memory integration
MONITOR_MEMORY_ENABLED=true
```

---

## 16. INITIALIZATION CHECKLIST

- [ ] Create `/memory` folder with all modules
- [ ] Create `memory/config.py` with constants
- [ ] Create `memory/models.py` with Pydantic models
- [ ] Create `memory/store.py` with MemoryStore (copy from STREAMLIT_MEMORY_SPEC.md)
- [ ] Create `memory/short_term.py` (copy from STREAMLIT_MEMORY_SPEC.md)
- [ ] Create `memory/long_term.py` (copy from STREAMLIT_MEMORY_SPEC.md)
- [ ] Create `memory/loader.py` (copy from STREAMLIT_MEMORY_SPEC.md)
- [ ] Create `memory/context_builder.py` (copy from STREAMLIT_MEMORY_SPEC.md)
- [ ] Create `memory/summariser.py` (copy from STREAMLIT_MEMORY_SPEC.md)
- [ ] Create `memory/sync_wrapper.py` (copy from STREAMLIT_MEMORY_SPEC.md)
- [ ] Create `monitoring/memory_bridge.py` (NEW)
- [ ] Modify `backend.py` — add memory injection to chat_node
- [ ] Modify `frontend.py` — add memory session start/end + sidebar display
- [ ] Modify `monitoring/runner.py` — add memory update callbacks
- [ ] Update `requirements.txt` with Redis + ChromaDB + Pydantic
- [ ] Update `.env` with Redis + Chroma + memory settings
- [ ] Test: Start Redis + Chroma + Streamlit app
- [ ] Test: Send chat message → verify memory context injected
- [ ] Test: Monitor runs → verify commodity interest stored in semantic memory
- [ ] Test: Session end → verify summariser creates episodic entry

---

## 17. DATA FLOW DIAGRAM

```
User Chat Message
       ↓
┌──────────────────────────────────────────┐
│ FRONTEND - Load Memory                   │
│ 1. Load SemanticProfile (facts)          │
│ 2. Load ProceduralProfile (prefs)        │
│ 3. Retrieve EpisodicMemory (context)     │
│ 4. Build <memory> block (400 tokens max) │
└──────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│ BACKEND - Inject & Chat                  │
│ 1. Prepend memory to system prompt       │
│ 2. Check cache layers (exact/semantic)   │
│ 3. Call LLM with memory context          │
│ 4. Return response                       │
└──────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│ FRONTEND - Store & Update                │
│ 1. Append turn to working_context (12 max)
│ 2. Check if summarise_after_turns reached
│ 3. On session end: trigger summariser    │
└──────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────┐
│ MONITORING - Detect & Bridge             │
│ 1. Monitor detects commodity alert       │
│ 2. Create MonitorEvent                   │
│ 3. Convert to EpisodicDoc                │
│ 4. Store in Chroma + update Semantic     │
│ 5. Next chat loads updated memory        │
└──────────────────────────────────────────┘
```

---

## 18. MEMORY LIFECYCLE

```
Session Start
  ↓
Load Semantic + Procedural from Redis (1 call)
Load Episodic from ChromaDB matching current query (similarity search)
Build <memory> block, inject into system prompt
  ↓
Chat Loop (turns accumulate in working_context)
  ↓
Every N turns OR session end:
  ↓
Summariser (gpt-4o-mini) extracts:
  - session_summary → Chroma (episodic)
  - semantic_updates (facts) → Redis (semantic hash)
  - procedural_updates (prefs) → Redis (procedural hash)
  ↓
Monitor runs independently:
  - Detects commodity alert
  - Stores as MonitorEvent → EpisodicDoc
  - Updates semantic.commodity_interests
  ↓
Next session start:
  - Loads updated memory automatically
  - Chatbot aware of monitor events
```

---

## 19. KEY DESIGN DECISIONS

| Decision | Rationale |
|----------|-----------|
| Redis for semantic/procedural | Fast reads, permanent storage, no TTL |
| ChromaDB for episodic/monitor events | Semantic search, embeds events in context |
| GPT-4o-mini for summariser only | Cheaper than gpt-4o, only called at session end |
| Monitor-to-memory bridge | Monitors inform memory without interrupting chat flow |
| <memory> block max 400 tokens | Balances context richness with token budget |
| Sync wrappers for Streamlit | Streamlit is sync-only, wraps async memory code |
| Abstraction layer (MemoryStore) | Allows future PostgreSQL migration without code changes |

---

## 20. NEXT PHASES (Future)

- Phase 2: Token counting + cost tracking in monitoring
- Phase 3: PostgreSQL + pgvector migration (MemoryStore swap only)
- Phase 4: Multi-user support with auth system
- Phase 5: Conversation memory (multi-turn RAG across sessions)
- Phase 6: Redis caching for monitoring results (shared across users)
