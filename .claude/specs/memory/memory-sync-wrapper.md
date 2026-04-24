# TOOL SPEC: Sync Wrappers (`memory/sync_wrapper.py`)

## Purpose
Sync wrappers for all async memory functions. Streamlit is synchronous; these wrappers allow calling async memory code from Streamlit without blocking.

---

## Implementation Notes

Reference `STREAMLIT_MEMORY_SPEC.md` section 11 for complete sync wrapper implementation.

## Module Should Include

### Session Management Wrappers
```python
def sync_create_session(session_id: str, user_id: str) -> SessionState:
    """Sync wrapper for create_session()"""

def sync_load_session(session_id: str) -> Optional[SessionState]:
    """Sync wrapper for load_session()"""

def sync_append_turn(session: SessionState, role: str, content: str) -> SessionState:
    """Sync wrapper for append_turn()"""

def sync_delete_session(session_id: str) -> None:
    """Sync wrapper for delete_session()"""
```

### Semantic/Procedural Wrappers
```python
def sync_load_semantic(user_id: str) -> SemanticProfile:
    """Sync wrapper for load_semantic()"""

def sync_load_procedural(user_id: str) -> ProceduralProfile:
    """Sync wrapper for load_procedural()"""

def sync_save_semantic(user_id: str, profile: SemanticProfile) -> None:
    """Sync wrapper for save_semantic()"""

def sync_save_procedural(user_id: str, profile: ProceduralProfile) -> None:
    """Sync wrapper for save_procedural()"""

def sync_update_semantic(user_id: str, updates: dict) -> None:
    """Sync wrapper for update_semantic()"""

def sync_update_procedural(user_id: str, updates: dict) -> None:
    """Sync wrapper for update_procedural()"""
```

### Memory Loading Wrapper
```python
def sync_load_long_term_memory(
    user_id: str,
    query: str,
    top_k: int = 5
) -> LongTermMemory:
    """Sync wrapper for load_long_term_memory()"""
```

### Summariser Wrapper
```python
def sync_summarise_session(
    session_id: str,
    user_id: str,
    session_state: Optional[SessionState] = None
) -> SummariserOutput:
    """Sync wrapper for summarise_session()"""
```

---

## Implementation Pattern

Each wrapper follows this pattern:

```python
def sync_<function_name>(*args, **kwargs):
    """Sync wrapper for async <function_name>()"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # No event loop in current thread; create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        async_<function_name>(*args, **kwargs)
    )
```

### Example: Sync Load Semantic

```python
def sync_load_semantic(user_id: str) -> SemanticProfile:
    """Load user facts synchronously"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        long_term.load_semantic(user_id)
    )
```

### Example: Sync Load Long-Term Memory

```python
def sync_load_long_term_memory(
    user_id: str,
    query: str,
    top_k: int = 5
) -> LongTermMemory:
    """Load complete memory context synchronously"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        loader.load_long_term_memory(user_id, query, top_k)
    )
```

---

## Usage in Streamlit

```python
# In frontend.py
from memory.sync_wrapper import (
    sync_load_long_term_memory,
    sync_load_semantic,
    sync_summarise_session,
    sync_create_session
)

# Load memory for current chat
ltm = sync_load_long_term_memory(user_id, user_message)

# Display user profile
sem = sync_load_semantic(user_id)
st.write(f"Welcome, {sem.name}!")

# Save session at end
sync_summarise_session(session_id, user_id, session_state)
```

---

## Event Loop Management

Streamlit runs in a single thread. The sync wrappers:

1. **Check for existing event loop** (`asyncio.get_event_loop()`)
2. **Create new one if needed** (on first call from Streamlit app)
3. **Run async function to completion** (`loop.run_until_complete()`)
4. **Return result** to caller

The event loop persists across Streamlit reruns, so subsequent calls reuse the same loop.

---

## Error Handling

```python
def sync_load_semantic(user_id: str) -> SemanticProfile:
    """Load user facts, return empty profile on error"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(
            long_term.load_semantic(user_id)
        )
    except Exception as e:
        logger.error(f"Failed to load semantic: {e}")
        return SemanticProfile()  # Empty profile; chat continues
```

---

## Performance Notes

- Sync wrappers add minimal overhead (~1-2ms per call)
- Event loop creation happens once on first call
- No difference in execution speed vs async (same underlying code)
- Blocking: Streamlit will freeze while async code runs (expected)

---

## Testing Sync Wrappers

```python
# Unit test sync_load_semantic
def test_sync_load_semantic():
    # Create test user
    user_id = "test_user_123"
    profile = SemanticProfile(name="Test", income_monthly=100000)
    
    # Save async
    loop = asyncio.get_event_loop()
    loop.run_until_complete(long_term.save_semantic(user_id, profile))
    
    # Load via sync wrapper
    loaded = sync_load_semantic(user_id)
    assert loaded.name == "Test"
    assert loaded.income_monthly == 100000
```

---

## Notes

- Complete implementation should reference STREAMLIT_MEMORY_SPEC.md section 11
- Essential for using async memory code in Streamlit
- Works transparently; Streamlit code doesn't need to know about async
- Graceful error handling ensures app stability
