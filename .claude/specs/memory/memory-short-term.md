# TOOL SPEC: Short-Term Memory (`memory/short_term.py`)

## Purpose
Session state + 5 cache layers: working context (2h), response cache (24h), semantic cache (24h), RAG cache (1h), tool cache (1h).

---

## Implementation Notes

Reference `STREAMLIT_MEMORY_SPEC.md` section 6 for complete short-term memory implementation.

## Module Should Include

### Session Management
```python
async def create_session(session_id: str, user_id: str) -> SessionState:
    """Create new session with empty working context"""

async def load_session(session_id: str) -> Optional[SessionState]:
    """Retrieve session from Redis"""

async def append_turn(session: SessionState, role: str, content: str) -> SessionState:
    """Add turn to working_context, return updated session"""

async def delete_session(session_id: str) -> None:
    """Clean up session (called on logout or after TTL)"""
```

### Cache Layers (all Redis-based)

1. **Response Cache** (24h TTL)
   ```python
   async def cache_exact_response(query: str, response: str) -> None
   async def get_exact_response(query: str) -> Optional[str]
   ```
   - Stores exact question → answer pairs
   - Reuse if same question asked again

2. **Semantic Cache** (24h TTL)
   ```python
   async def cache_semantic(query_embedding, response: str, score: float) -> None
   async def get_similar_response(query: str, threshold: float = 0.85) -> Optional[str]
   ```
   - Stores embeddings of questions
   - Reuse if similar question (>85% match) asked

3. **RAG Cache** (1h TTL)
   ```python
   async def cache_rag_chunk(doc_id: str, chunk: str, embedding) -> None
   async def get_rag_chunk(doc_id: str) -> Optional[str]
   ```
   - Caches retrieved document chunks
   - Speeds up multi-turn RAG queries

4. **Tool Cache** (1h TTL)
   ```python
   async def cache_tool_result(tool_name: str, args: dict, result: dict) -> None
   async def get_tool_result(tool_name: str, args: dict) -> Optional[dict]
   ```
   - Stores API/tool results (stock prices, weather, etc.)
   - Avoids duplicate external calls

5. **Node Cache** (1h TTL)
   ```python
   async def cache_node_result(node_name: str, inputs: dict, output: dict) -> None
   async def get_node_result(node_name: str, inputs: dict) -> Optional[dict]
   ```
   - Caches LangGraph node results
   - Skips re-execution if inputs unchanged

---

## Cache Key Strategy

Each cache layer uses unique Redis key prefixes (from config):

```
Response Cache: cache:resp:<hash(query)>
Semantic Cache: cache:sem:<hash(query_embedding)>
RAG Cache:      cache:rag:<doc_id>:<chunk_id>
Tool Cache:     cache:tool:<tool_name>:<hash(args)>
Node Cache:     cache:node:<node_name>:<hash(inputs)>
```

TTL enforcement via Redis EXPIRE:
- Response: 86400s (24h)
- Semantic: 86400s (24h)
- RAG: 3600s (1h)
- Tool: 3600s (1h)
- Node: 3600s (1h)

---

## Integration with LangGraph

Cache lookups happen in:

1. **chat_node** (before LLM call)
   - Check response cache (exact match)
   - Check semantic cache (similarity match)
   - If hit, return cached response

2. **retrieval_node** (after RAG search)
   - Cache retrieved chunks with TTL_RAG_CACHE

3. **tool nodes** (after tool execution)
   - Cache tool results with TTL_TOOL_CACHE

4. **Each node** (save output)
   - Cache node output with TTL_NODE_CACHE

---

## Usage Example

```python
from memory.short_term import (
    create_session, append_turn,
    get_exact_response, cache_exact_response,
    get_similar_response, cache_semantic
)
from memory.models import SessionState, Turn

# Create new session
session = await create_session("sess_123", "user_456")

# Add turns as conversation progresses
session = await append_turn(session, "user", "What's my savings goal?")
session = await append_turn(session, "assistant", "Your goal is ₹5L by 2025")

# Use cache in chat_node
cached_response = await get_exact_response("What's my savings goal?")
if cached_response:
    return cached_response  # Skip LLM
else:
    response = await llm.agenerate(...)
    await cache_exact_response("What's my savings goal?", response)
    return response
```

---

## Cache Invalidation

**Manual invalidation:**
```python
async def invalidate_response_cache(query: str):
    """Clear exact response for specific query"""
    
async def invalidate_all_caches():
    """Clear all cache layers (e.g., on model update)"""
```

**Automatic invalidation:**
- Redis TTL handles expiration
- Semantic cache clears on procedural profile update
- Tool/node cache clears after 1 hour

---

## Performance Notes

- Response cache hit: <10ms
- Semantic search: ~100-200ms
- RAG cache hit: ~50ms
- All cache misses fall back to normal processing (no errors)
- Cache is optional; system works fine without it (just slower)

---

## Notes

- Exact implementation should be referenced from STREAMLIT_MEMORY_SPEC.md section 6
- Ensures working context + 5 cache layers integrate smoothly
- Cache hits reduce LLM calls and improve latency
