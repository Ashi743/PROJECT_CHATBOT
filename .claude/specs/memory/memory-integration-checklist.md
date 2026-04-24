# Memory System Integration Checklist & Setup

## Dependencies

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

## File Structure

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
│   ├── context_builder.py         # Build prompt context
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

## Implementation Checklist

### Phase 1: Foundation (Memory Modules)

- [ ] Create `/memory` folder
- [ ] Create `memory/__init__.py`
- [ ] Create `memory/config.py` with constants
- [ ] Create `memory/models.py` with Pydantic models
- [ ] Create `memory/store.py` with MemoryStore abstraction
- [ ] Create `memory/short_term.py` (session + cache layers)
- [ ] Create `memory/long_term.py` (episodic/semantic/procedural)
- [ ] Create `memory/loader.py` (load_long_term_memory())
- [ ] Create `memory/context_builder.py` (build_messages())
- [ ] Create `memory/summariser.py` (session-end summarization)
- [ ] Create `memory/sync_wrapper.py` (Streamlit sync wrappers)

### Phase 2: Monitor Integration

- [ ] Create `monitoring/memory_bridge.py` (NEW)
- [ ] Modify `monitoring/runner.py` — add memory update callbacks

### Phase 3: Backend Integration

- [ ] Modify `backend.py` — add memory injection to chat_node
- [ ] Test memory context appears in LLM prompts
- [ ] Test cache layers work (exact/semantic)

### Phase 4: Frontend Integration

- [ ] Modify `frontend.py` — add memory session start/end
- [ ] Add memory profile display in sidebar
- [ ] Test memory loads on session start
- [ ] Test memory updates after each turn

### Phase 5: Dependencies & Configuration

- [ ] Update `requirements.txt` with Redis + ChromaDB + Pydantic
- [ ] Update `.env` with Redis + Chroma + memory settings
- [ ] Start Redis server (`redis-server`)
- [ ] Start ChromaDB server (`chroma run --host localhost --port 8000`)

### Phase 6: Integration Testing

- [ ] Start Streamlit app
- [ ] Test: Send chat message → verify memory context injected in logs
- [ ] Test: Load memory profile in sidebar
- [ ] Test: Monitor runs → verify commodity interest stored in semantic memory
- [ ] Test: Session end → verify summariser creates episodic entry
- [ ] Test: Next session → verify memory loads and influences response

### Phase 7: Monitor Event Flow

- [ ] Test commodity monitor detects alert
- [ ] Test event stored in episodic memory
- [ ] Test semantic.commodity_interests updated
- [ ] Test next chat retrieves updated memory

---

## Pre-Flight Checklist

Before starting integration:

- [ ] Read `memory-architecture.md` for overall design
- [ ] Read each tool spec (`memory-config.md`, `memory-models.md`, etc.)
- [ ] Read integration specs (`backend-memory.md`, `frontend-memory.md`, etc.)
- [ ] Set up Redis and ChromaDB locally
- [ ] Verify current chatbot works without memory changes
- [ ] Create a git branch for memory work (e.g., `feat/memory-system`)

---

## Rollback Plan

If issues arise during integration:

1. Stop the Streamlit app
2. Stop Redis and ChromaDB servers
3. Revert `backend.py` and `frontend.py` to HEAD
4. `git checkout -- memory/ monitoring/memory_bridge.py`
5. Restart app with `streamlit run frontend.py`

Memory is fully backward-compatible; removing imports restores original behavior.

---

## Monitoring & Debugging

### Enable debug logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Redis connection

```bash
redis-cli ping  # Should return PONG
```

### Check ChromaDB connection

```bash
curl http://localhost:8000/api/v1/heartbeat
```

### View memory for a user

```python
from memory.sync_wrapper import sync_load_semantic, sync_load_procedural
sem = sync_load_semantic("user123")
proc = sync_load_procedural("user123")
print(sem, proc)
```

### Clear memory for testing

```python
from memory.store import MemoryStore
store = MemoryStore()
store.redis.flushdb()  # WARNING: Clears all data
```

---

## Performance Notes

- Semantic memory loads in <50ms (Redis hash lookup)
- Episodic retrieval is ~200-500ms (ChromaDB similarity search)
- Summariser runs asynchronously, not on critical path
- <memory> block (~400 tokens) adds ~0.5s to LLM latency
- Monitor-to-memory updates are non-blocking
