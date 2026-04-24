# Memory System Specification

Complete specification for the LangGraph chatbot memory system with semantic, procedural, and episodic storage.

## Index

### Architecture & Design
- **[memory-architecture.md](memory-architecture.md)** — Overview, data flow, lifecycle, key decisions
- **[memory-integration-checklist.md](memory-integration-checklist.md)** — Setup guide, dependencies, implementation checklist
- **[integrated-memory-spec.md](integrated-memory-spec.md)** — Complete integrated spec (reference document)

### Core Tools & Components
- **[memory-config.md](memory-config.md)** — Configuration constants (Redis URLs, TTLs, thresholds)
- **[memory-models.md](memory-models.md)** — Pydantic models (SemanticProfile, ProceduralProfile, EpisodicDoc, MonitorEvent)
- **[memory-store.md](memory-store.md)** — MemoryStore abstraction (Redis + ChromaDB operations)
- **[memory-short-term.md](memory-short-term.md)** — Session + cache layers (response, semantic, RAG, tool caches)
- **[memory-long-term.md](memory-long-term.md)** — Episodic/semantic/procedural storage and retrieval
- **[memory-loader.md](memory-loader.md)** — Load assembled long-term memory for chat
- **[memory-context-builder.md](memory-context-builder.md)** — Format memory into `<memory>` block for prompts
- **[memory-summariser.md](memory-summariser.md)** — Session-end summarization and memory updates
- **[memory-sync-wrapper.md](memory-sync-wrapper.md)** — Sync wrappers for Streamlit compatibility

### Integration
- **[backend-memory.md](backend-memory.md)** — Integrate memory into backend.py chat_node
- **[memory-monitor-bridge.md](memory-monitor-bridge.md)** — Connect monitoring system to memory updates

---

## Quick Start

### 1. Read First
- Start with **memory-architecture.md** for overview
- Then **memory-integration-checklist.md** for setup steps

### 2. Understand Components
- **memory-config.md** — What gets configured
- **memory-models.md** — What data structures exist
- **memory-store.md** — How data is persisted

### 3. Implement Flow
- **memory-loader.py** — Entry point for loading memory
- **memory-context-builder.py** — Format for LLM injection
- **backend-memory.md** — How to inject into chat

### 4. Extend (Optional)
- **memory-short-term.md** — Add caching layers
- **memory-summariser.md** — Enhance with LLM extraction
- **memory-monitor-bridge.md** — Connect to monitors

---

## Memory Types at a Glance

| Type | Storage | TTL | Use |
|------|---------|-----|-----|
| **Semantic** | Redis | None | User facts, interests, goals |
| **Procedural** | Redis | None | Communication preferences |
| **Episodic** | ChromaDB | None | Conversations, events, context |
| **Session** | Redis | 2h | Working context |
| **Cache** | Redis | 1h-24h | Response/semantic/tool caching |

---

## Implementation Status

✅ **Complete & Tested**
- Core memory modules (store, loader, context_builder)
- Backend integration (chat_node memory injection)
- Frontend integration (session management + UI)
- Monitor-to-memory bridge ready
- Graceful error handling

🔄 **Optional Enhancements**
- Short-term caching (response, semantic, tool caches)
- LLM-powered summariser (structured extraction)
- PostgreSQL migration (designed but not implemented)

---

## Setup Checklist

```bash
# 1. Start Redis
redis-server

# 2. Start ChromaDB
chroma run --host localhost --port 8000

# 3. Install deps
pip install -r requirements.txt

# 4. Run chatbot
streamlit run frontend.py
```

---

## Key Files in Codebase

```
memory/                 — Core implementation (8 modules)
├── config.py          
├── models.py          
├── store.py           
├── loader.py          
├── context_builder.py 
├── sync_wrapper.py    
├── summariser.py      
└── test_memory.py     

monitoring/
└── memory_bridge.py   — Monitor → Memory integration

backend.py            — Modified for memory injection
frontend.py           — Modified for session management
```

---

## Questions?

- **How does memory work?** → Read memory-architecture.md
- **How do I set it up?** → Read memory-integration-checklist.md
- **What's in each module?** → Read individual spec files
- **How's it implemented?** → Check memory/ directory
