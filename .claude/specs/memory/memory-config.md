# TOOL SPEC: Memory Configuration (`memory/config.py`)

## Purpose
Central configuration for all memory system constants, including Redis/ChromaDB connection details, TTLs, key prefixes, and thresholds.

---

## Implementation

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

## Configuration Reference

### Redis Connection
- Default: `redis://localhost:6379/0`
- Override via `REDIS_URL` environment variable
- Used for: semantic, procedural, session state, all cache layers

### ChromaDB Connection
- Default host: `localhost`
- Default port: `8000`
- Override via `CHROMA_HOST` and `CHROMA_PORT`
- Used for: episodic memory, monitor events, semantic search

### TTL Values (seconds)
- **Session**: 2 hours — working context persists across page reloads
- **Response cache**: 24 hours — exact answer reuse
- **Semantic cache**: 24 hours — similar question matching
- **RAG cache**: 1 hour — document chunk reuse
- **Tool cache**: 1 hour — API/tool result reuse
- **Node cache**: 1 hour — LangGraph node result cache

### Session Limits
- **MAX_TURNS**: 12 — max conversation turns before forced summarize
- **SUMMARISE_AFTER_TURNS**: 10 — auto-summarize at 10 turns (before max)

### Similarity & Retrieval
- **SEM_CACHE_THRESHOLD**: 0.85 — similarity score needed to reuse cached response
- **EPISODIC_MIN_IMP**: 0.3 — minimum importance to retrieve from episodic memory
- **EPISODIC_TOP_K**: 5 — number of episodic chunks to retrieve per query
- **MEMORY_BLOCK_MAX_TOKENS**: 400 — max token budget for <memory> block in prompt

### Models
- **CHAT_MODEL**: "gpt-4o" — primary LLM for all chat responses
- **SUMMARISER_MODEL**: "gpt-4o-mini" — cheaper model for session summarization
- **EMBEDDING_MODEL**: "text-embedding-3-small" — embeddings for ChromaDB
- **EMBEDDING_DIM**: 1536 — vector dimension for "text-embedding-3-small"

### Monitoring Integration
- **MONITOR_EVENT_IMPORTANCE**: 0.7 — episodic importance for monitor-detected events
- **MONITOR_MEMORY_ENABLED**: true — enable/disable monitor → memory updates globally

---

## Environment Variables (.env)

Required to override defaults:

```
REDIS_URL=redis://localhost:6379/0
CHROMA_HOST=localhost
CHROMA_PORT=8000
MONITOR_MEMORY_ENABLED=true
```

---

## Usage in Other Modules

```python
from memory.config import (
    REDIS_URL,
    CHROMA_HOST,
    CHROMA_PORT,
    TTL_SESSION,
    EPISODIC_TOP_K,
    MAX_TURNS,
    SUMMARISER_MODEL,
)

# Example: Initialize Redis with TTL
import redis
r = redis.from_url(REDIS_URL)
r.setex("key", TTL_SESSION, "value")
```

---

## Notes

- All TTL and threshold values are tunable for different use cases
- For local testing, defaults connect to `localhost` on standard ports
- For production, update `REDIS_URL` and `CHROMA_*` via environment
- Never hardcode API keys; always load from environment
