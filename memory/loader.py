"""Memory loader — assembles long-term memory for chat."""

import logging
from memory.store import MemoryStore
from memory.models import LongTermMemory
from memory.config import REDIS_URL, CHROMA_HOST, CHROMA_PORT, EPISODIC_TOP_K, EPISODIC_MIN_IMP

logger = logging.getLogger(__name__)


def load_long_term_memory(
    user_id: str,
    query: str,
    top_k: int = EPISODIC_TOP_K,
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
    try:
        store = MemoryStore(redis_url=REDIS_URL, chroma_host=CHROMA_HOST, chroma_port=CHROMA_PORT)

        # Load semantic profile (fast)
        semantic = store.get_semantic(user_id)
        logger.debug(f"Loaded semantic profile for {user_id}")

        # Load procedural profile (fast)
        procedural = store.get_procedural(user_id)
        logger.debug(f"Loaded procedural profile for {user_id}")

        # Search episodic memory (slower, ~200-500ms)
        episodic_docs = store.search_episodic(
            user_id, query, limit=top_k, min_importance=EPISODIC_MIN_IMP
        )
        episodic_chunks = [doc.document for doc in episodic_docs]
        logger.debug(f"Retrieved {len(episodic_chunks)} episodic documents for {user_id}")

        # Assemble
        ltm = LongTermMemory(
            semantic=semantic, procedural=procedural, episodic_chunks=episodic_chunks
        )

        return ltm

    except Exception as e:
        logger.error(f"Failed to load long-term memory: {e}")
        # Graceful degradation: return empty memory
        from memory.models import SemanticProfile, ProceduralProfile

        return LongTermMemory(
            semantic=SemanticProfile(),
            procedural=ProceduralProfile(),
            episodic_chunks=[],
        )


if __name__ == "__main__":
    # Test
    ltm = load_long_term_memory("test_user", "What are my goals?")
    print(f"[OK] Loaded memory: {ltm}")
