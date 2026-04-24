# SPEC: Memory System Architecture

## Overview

The memory system adds three persistent memory capabilities to the chatbot:

1. **Memory Layer** — Persistent user facts, conversation history, preferences
2. **Monitor-to-Memory Bridge** — When monitors detect events, they auto-update user memory
3. **Synchronized Session State** — Memory is loaded at session start, saved at session end

**Design principle:** No breaking changes. The chatbot works exactly as before. Memory is additive.

---

## Memory Types

### Semantic Memory (User Facts)
- Name, age, city, income, goals, preferences
- Detected by monitors (commodity interests, API monitoring status)
- Stored in Redis for fast read/write
- Immutable except via summariser + monitor events

### Procedural Memory (Behavior Rules)
- How to respond to this user: tone, format, language
- Preferred currency, topics to avoid, triggers
- Stored in Redis
- Updated by summariser

### Episodic Memory (Events & Context)
- Session summaries, individual turns, emotional signals
- Monitor-detected events
- Stored in ChromaDB (semantic search enabled)
- Embedded and retrieved by similarity to current query

### Session State (Working Context)
- Current conversation turn count, active topic, pending tasks
- Stored in Redis with 2-hour TTL
- Accumulates turns until summariser triggers (at 10 turns)

---

## Data Flow Diagram

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

## Memory Lifecycle

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

## Storage Strategy

| Memory Type | Store | Persistence | TTL | Why |
|-------------|-------|-------------|-----|-----|
| Semantic | Redis hash | Permanent | None | Fast reads, immutable |
| Procedural | Redis hash | Permanent | None | User preferences, rarely change |
| Episodic | ChromaDB | Permanent | None | Semantic search, long history |
| Session | Redis key | 2 hours | 2h | Working context, auto-cleanup |
| Cache layers | Redis | Temporary | 1h-24h | Response/semantic/RAG caching |

---

## Key Design Decisions

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

## Integration Points

### Backend (backend.py)
- Load long-term memory at chat start
- Inject memory block into system prompt
- Route to appropriate LLM based on query

### Frontend (frontend.py)
- Load memory on session start
- Display memory profile in sidebar
- Update working_context after each turn
- Trigger summariser at session end

### Monitoring (monitoring/runner.py)
- Convert monitor events to MonitorEvent objects
- Store events in episodic memory
- Update semantic memory with new interests

---

## Next Phases (Future)

- Phase 2: Token counting + cost tracking in monitoring
- Phase 3: PostgreSQL + pgvector migration (MemoryStore swap only)
- Phase 4: Multi-user support with auth system
- Phase 5: Conversation memory (multi-turn RAG across sessions)
- Phase 6: Redis caching for monitoring results (shared across users)
