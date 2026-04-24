# TOOL SPEC: Memory Store Abstraction (`memory/store.py`)

## Purpose
Single abstraction layer over Redis + ChromaDB. Allows future migration to PostgreSQL/pgvector without changing upstream code.

---

## Implementation Notes

Reference `STREAMLIT_MEMORY_SPEC.md` section 5 for complete MemoryStore class implementation.

This spec should include:

### Core Methods
```
MemoryStore:
  ├─ Redis Operations
  │  ├─ set_semantic(user_id, profile) → None
  │  ├─ get_semantic(user_id) → SemanticProfile
  │  ├─ set_procedural(user_id, profile) → None
  │  ├─ get_procedural(user_id) → ProceduralProfile
  │  ├─ set_session(session_id, state) → None
  │  ├─ get_session(session_id) → SessionState
  │  ├─ update_semantic(user_id, updates) → None
  │  └─ delete_session(session_id) → None
  │
  └─ ChromaDB Operations
     ├─ save_episodic(doc) → None
     ├─ get_episodic(user_id, session_id, doc_id) → EpisodicDoc
     ├─ search_episodic(user_id, query, limit) → list[EpisodicDoc]
     └─ delete_episodic(user_id, doc_id) → None
```

### Constructor
```python
def __init__(self, redis_url: str, chroma_host: str, chroma_port: int):
    # Initialize Redis connection
    # Initialize ChromaDB connection
    # Setup collections
```

### Error Handling
- Redis connection errors (ConnectionError, RedisError)
- ChromaDB errors (DocumentNotFound, DuplicateIDError)
- JSON serialization for complex types (datetime, enum)

### Serialization
- Redis uses JSON for Pydantic models → dict → JSON string
- ChromaDB uses documents (text) + metadata (dict) + embeddings (auto-generated)

---

## Design Rationale

**Why abstract?**
- Decouples storage from business logic
- Allows Redis → PostgreSQL migration later without touching `loader.py`, `summariser.py`, etc.
- Testable: can mock MemoryStore for unit tests

**Why Redis for semantic/procedural?**
- Key-value access is O(1) per user
- No schema changes needed
- TTL/expiration supported

**Why ChromaDB for episodic?**
- Semantic search (embedding-based retrieval)
- Handles variable-length documents
- Built-in similarity scoring

---

## Usage Example

```python
from memory.store import MemoryStore
from memory.config import REDIS_URL, CHROMA_HOST, CHROMA_PORT
from memory.models import SemanticProfile, EpisodicDoc

# Initialize
store = MemoryStore(REDIS_URL, CHROMA_HOST, CHROMA_PORT)

# Save semantic profile
sem = SemanticProfile(name="Ashish", income_monthly=100000)
store.set_semantic("user_123", sem)

# Retrieve
retrieved = store.get_semantic("user_123")
print(retrieved.name)  # "Ashish"

# Search episodic memory
results = store.search_episodic("user_123", "retirement planning", limit=5)
for doc in results:
    print(doc.document)

# Update semantic (partial)
store.update_semantic("user_123", {"income_monthly": 120000})
```

---

## Migration Path (Future)

For PostgreSQL migration:

```python
class MemoryStorePostgres(MemoryStore):
    """Drop-in replacement for PostgreSQL + pgvector"""
    
    def __init__(self, db_url: str):
        self.db = create_engine(db_url)
        # Initialize pgvector tables
    
    def set_semantic(self, user_id: str, profile: SemanticProfile):
        # INSERT or UPDATE into semantic_profiles table
        
    def search_episodic(self, user_id: str, query: str, limit: int):
        # Use pgvector <-> operator for similarity search
```

Then swap in frontend:
```python
# Current
from memory.store import MemoryStore

# Future
from memory.store_postgres import MemoryStorePostgres as MemoryStore
```

---

## Notes

- Complete implementation should be copied from referenced STREAMLIT_MEMORY_SPEC.md
- Ensures consistency across memory system
- Provides all methods needed by loader, summariser, and monitor_bridge modules
