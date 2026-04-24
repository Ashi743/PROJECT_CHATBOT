# TOOL SPEC: Memory Loader (`memory/loader.py`)

## Purpose
Load assembled long-term memory context for injection into LLM prompt. Called by `context_builder.py` during chat.

---

## Implementation Notes

Reference `STREAMLIT_MEMORY_SPEC.md` section 8 for complete memory loader implementation.

## Module Should Include

### Main Function
```python
async def load_long_term_memory(
    user_id: str,
    query: str,
    top_k: int = 5
) -> LongTermMemory:
    """
    Load complete long-term memory for user.
    
    Args:
        user_id: User identifier
        query: Current chat query (used for episodic retrieval)
        top_k: Number of episodic chunks to retrieve
    
    Returns:
        LongTermMemory object ready for prompt injection
    """
```

### Internal Steps
1. **Load Semantic Profile**
   ```python
   semantic = await long_term.load_semantic(user_id)
   ```
   - Fast: O(1) Redis lookup
   - Returns facts: name, age, goals, interests, etc.

2. **Load Procedural Profile**
   ```python
   procedural = await long_term.load_procedural(user_id)
   ```
   - Fast: O(1) Redis lookup
   - Returns preferences: tone, format, language, etc.

3. **Search Episodic Memory**
   ```python
   episodic_docs = await long_term.search_episodic(
       user_id, query, limit=top_k, min_importance=EPISODIC_MIN_IMP
   )
   ```
   - Slower: ~200-500ms ChromaDB similarity search
   - Returns top-K matching documents
   - Filtered by importance threshold

4. **Assemble LongTermMemory**
   ```python
   ltm = LongTermMemory(
       semantic=semantic,
       procedural=procedural,
       episodic_chunks=[doc.document for doc in episodic_docs]
   )
   return ltm
   ```

---

## Performance Characteristics

- **Semantic load**: ~10-50ms (Redis)
- **Procedural load**: ~10-50ms (Redis)
- **Episodic search**: ~200-500ms (ChromaDB)
- **Total**: ~250-600ms per call

For better UX, episodic search can run in background while using semantic/procedural immediately.

---

## Fallback Behavior

If stores unavailable:
```python
async def load_long_term_memory(user_id: str, query: str) -> LongTermMemory:
    try:
        semantic = await load_semantic(user_id)
    except Exception:
        semantic = SemanticProfile()  # Empty profile
    
    try:
        procedural = await load_procedural(user_id)
    except Exception:
        procedural = ProceduralProfile()  # Defaults
    
    try:
        episodic_docs = await search_episodic(user_id, query)
        episodic_chunks = [doc.document for doc in episodic_docs]
    except Exception:
        episodic_chunks = []  # No context
    
    return LongTermMemory(
        semantic=semantic,
        procedural=procedural,
        episodic_chunks=episodic_chunks
    )
```

This ensures graceful degradation; chat continues even if memory unavailable.

---

## Usage Example

```python
from memory.loader import load_long_term_memory

# In chat_node, load memory for current query
user_id = st.session_state["user_id"]
user_message = "How much should I save for retirement?"

ltm = await load_long_term_memory(
    user_id=user_id,
    query=user_message,
    top_k=5  # Get 5 relevant episodic memories
)

# Memory is now ready for injection
print(ltm.semantic.name)  # User's name
print(ltm.procedural.tone)  # How to speak
print(ltm.episodic_chunks)  # Top-K relevant contexts
```

---

## Optimizations

### Parallel Loading
Semantic + Procedural can load in parallel (independent Redis calls):
```python
sem, proc = await asyncio.gather(
    long_term.load_semantic(user_id),
    long_term.load_procedural(user_id)
)
```

### Episodic Search in Background
Start episodic search early while building prompt with semantic/procedural:
```python
# Fire episodic search but don't wait
episodic_task = asyncio.create_task(
    long_term.search_episodic(user_id, query, limit=5)
)

# Build memory block with semantic/procedural immediately
memory_block = build_memory_block(sem, proc, [])

# Wait for episodic results if ready
try:
    episodic_docs = await asyncio.wait_for(episodic_task, timeout=0.5)
    episodic_chunks = [doc.document for doc in episodic_docs]
except asyncio.TimeoutError:
    episodic_chunks = []  # Proceed without episodic
```

---

## Error Handling

Catch and log errors; never throw exceptions that interrupt chat:
```python
try:
    semantic = await load_semantic(user_id)
except RedisError as e:
    logger.error(f"Failed to load semantic: {e}")
    semantic = SemanticProfile()

try:
    episodic_docs = await search_episodic(user_id, query)
except ChromaError as e:
    logger.error(f"Failed to search episodic: {e}")
    episodic_docs = []
```

---

## Notes

- Complete implementation should reference STREAMLIT_MEMORY_SPEC.md section 8
- Provides single entry point for loading all memory types
- Handles fallbacks gracefully
- Performance target: <1s total latency (including episodic search)
