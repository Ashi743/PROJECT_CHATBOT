"""Sync wrappers for async memory functions — Streamlit compatibility."""

import asyncio
import logging
from typing import Optional
from memory.loader import load_long_term_memory
from memory.models import LongTermMemory, SemanticProfile, ProceduralProfile, SessionState
from memory.store import MemoryStore
from memory.config import REDIS_URL, CHROMA_HOST, CHROMA_PORT

logger = logging.getLogger(__name__)

# Singleton MemoryStore instance to avoid repeated connection creation
_store_instance: Optional[MemoryStore] = None
_store_lock = __import__('threading').Lock()


def _get_store() -> MemoryStore:
    """Get or create singleton MemoryStore instance."""
    global _store_instance
    if _store_instance is None:
        with _store_lock:
            if _store_instance is None:
                _store_instance = MemoryStore(redis_url=REDIS_URL, chroma_host=CHROMA_HOST, chroma_port=CHROMA_PORT)
    return _store_instance


def _get_or_create_loop():
    """Get event loop, create if needed."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def sync_load_long_term_memory(
    user_id: str,
    query: str,
    top_k: int = 5,
) -> LongTermMemory:
    """Sync wrapper for load_long_term_memory()."""
    try:
        return load_long_term_memory(user_id, query, top_k)
    except Exception as e:
        logger.error(f"Failed to load long-term memory: {e}")
        return LongTermMemory(
            semantic=SemanticProfile(),
            procedural=ProceduralProfile(),
            episodic_chunks=[],
        )


def sync_load_semantic(user_id: str) -> SemanticProfile:
    """Load semantic profile synchronously."""
    try:
        return _get_store().get_semantic(user_id)
    except Exception as e:
        logger.error(f"Failed to load semantic: {e}")
        return SemanticProfile()


def sync_load_procedural(user_id: str) -> ProceduralProfile:
    """Load procedural profile synchronously."""
    try:
        return _get_store().get_procedural(user_id)
    except Exception as e:
        logger.error(f"Failed to load procedural: {e}")
        return ProceduralProfile()


def sync_save_semantic(user_id: str, profile: SemanticProfile) -> None:
    """Save semantic profile synchronously."""
    try:
        _get_store().set_semantic(user_id, profile)
    except Exception as e:
        logger.error(f"Failed to save semantic: {e}")


def sync_save_procedural(user_id: str, profile: ProceduralProfile) -> None:
    """Save procedural profile synchronously."""
    try:
        _get_store().set_procedural(user_id, profile)
    except Exception as e:
        logger.error(f"Failed to save procedural: {e}")


def sync_update_semantic(user_id: str, updates: dict) -> None:
    """Update semantic profile synchronously."""
    try:
        _get_store().update_semantic(user_id, updates)
    except Exception as e:
        logger.error(f"Failed to update semantic: {e}")


def sync_update_procedural(user_id: str, updates: dict) -> None:
    """Update procedural profile synchronously."""
    try:
        _get_store().update_procedural(user_id, updates)
    except Exception as e:
        logger.error(f"Failed to update procedural: {e}")


def sync_create_session(session_id: str, user_id: str) -> SessionState:
    """Create new session synchronously."""
    try:
        from datetime import datetime

        session = SessionState(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
        )
        _get_store().set_session(session_id, session)
        return session
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise


def sync_load_session(session_id: str) -> Optional[SessionState]:
    """Load session synchronously."""
    try:
        return _get_store().get_session(session_id)
    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        return None


def sync_delete_session(session_id: str) -> None:
    """Delete session synchronously."""
    try:
        _get_store().delete_session(session_id)
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")


if __name__ == "__main__":
    # Test
    sem = sync_load_semantic("test_user")
    print(f"[OK] Loaded semantic: {sem}")
