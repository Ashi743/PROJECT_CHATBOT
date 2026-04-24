"""Memory system configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI ────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHAT_MODEL = "gpt-4o"
SUMMARISER_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# ── Redis ─────────────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# TTLs (seconds)
TTL_SESSION = 7_200  # 2 h — working context
TTL_RESP_CACHE = 86_400  # 24 h — exact response cache
TTL_SEM_CACHE = 86_400  # 24 h — semantic cache
TTL_RAG_CACHE = 3_600  # 1 h — RAG chunk cache
TTL_TOOL_CACHE = 3_600  # 1 h — tool/API result cache
TTL_NODE_CACHE = 3_600  # 1 h — pipeline node cache

# Key prefixes
PFX_SESSION = "session"
PFX_RESP = "cache:resp"
PFX_SEM = "cache:sem"
PFX_RAG = "cache:rag"
PFX_TOOL = "cache:tool"
PFX_NODE = "cache:node"
PFX_MEM_SEMANTIC = "memory:semantic"
PFX_MEM_PROCEDURAL = "memory:procedural"

# Session
MAX_TURNS = 12
SUMMARISE_AFTER_TURNS = 10

# Similarity threshold
SEM_CACHE_THRESHOLD = 0.85
EPISODIC_MIN_IMP = 0.3
EPISODIC_TOP_K = 5
MEMORY_BLOCK_MAX_TOKENS = 400

# ChromaDB
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

COL_EPISODIC = "episodic_{user_id}"
COL_SEMANTIC = "semantic_{user_id}"

# ── Monitoring Memory Bridge ──────────────────────────────────────────────
MONITOR_EVENT_IMPORTANCE = 0.7  # Higher = more likely to be retrieved
MONITOR_MEMORY_ENABLED = os.getenv("MONITOR_MEMORY_ENABLED", "true").lower() == "true"
