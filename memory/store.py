"""Memory store abstraction — Redis + ChromaDB."""

import json
import logging
from typing import Optional
import redis
import chromadb
from chromadb.config import Settings

from memory.models import (
    SemanticProfile,
    ProceduralProfile,
    SessionState,
    EpisodicDoc,
)
from memory.config import (
    REDIS_URL,
    CHROMA_HOST,
    CHROMA_PORT,
    PFX_MEM_SEMANTIC,
    PFX_MEM_PROCEDURAL,
    COL_EPISODIC,
    TTL_SESSION,
)

logger = logging.getLogger(__name__)


class MemoryStore:
    """Abstraction over Redis + ChromaDB for memory persistence."""

    def __init__(self, redis_url: str = REDIS_URL, chroma_host: str = CHROMA_HOST, chroma_port: int = CHROMA_PORT):
        """Initialize Redis + ChromaDB connections."""
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise

        try:
            # ChromaDB client
            self.chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
            logger.info(f"ChromaDB connected to {chroma_host}:{chroma_port}")
        except Exception as e:
            logger.error(f"ChromaDB connection failed: {e}")
            raise

    # ── Redis Operations (Semantic/Procedural/Session) ──

    def set_semantic(self, user_id: str, profile: SemanticProfile) -> None:
        """Store user facts in Redis."""
        key = f"{PFX_MEM_SEMANTIC}:{user_id}"
        json_str = profile.model_dump_json()
        self.redis.set(key, json_str)
        logger.debug(f"Stored semantic profile for {user_id}")

    def get_semantic(self, user_id: str) -> SemanticProfile:
        """Retrieve user facts from Redis."""
        key = f"{PFX_MEM_SEMANTIC}:{user_id}"
        json_str = self.redis.get(key)
        if json_str:
            return SemanticProfile(**json.loads(json_str))
        return SemanticProfile()

    def update_semantic(self, user_id: str, updates: dict) -> None:
        """Partial update to semantic profile."""
        current = self.get_semantic(user_id)
        for key, value in updates.items():
            if value is not None and hasattr(current, key):
                setattr(current, key, value)
        self.set_semantic(user_id, current)
        logger.debug(f"Updated semantic profile for {user_id}")

    def delete_semantic(self, user_id: str) -> None:
        """Erase all facts for user."""
        key = f"{PFX_MEM_SEMANTIC}:{user_id}"
        self.redis.delete(key)
        logger.debug(f"Deleted semantic profile for {user_id}")

    def set_procedural(self, user_id: str, profile: ProceduralProfile) -> None:
        """Store user preferences in Redis."""
        key = f"{PFX_MEM_PROCEDURAL}:{user_id}"
        json_str = profile.model_dump_json()
        self.redis.set(key, json_str)
        logger.debug(f"Stored procedural profile for {user_id}")

    def get_procedural(self, user_id: str) -> ProceduralProfile:
        """Retrieve user preferences from Redis."""
        key = f"{PFX_MEM_PROCEDURAL}:{user_id}"
        json_str = self.redis.get(key)
        if json_str:
            return ProceduralProfile(**json.loads(json_str))
        return ProceduralProfile()

    def update_procedural(self, user_id: str, updates: dict) -> None:
        """Partial update to procedural profile."""
        current = self.get_procedural(user_id)
        for key, value in updates.items():
            if value is not None and hasattr(current, key):
                setattr(current, key, value)
        self.set_procedural(user_id, current)
        logger.debug(f"Updated procedural profile for {user_id}")

    def delete_procedural(self, user_id: str) -> None:
        """Erase all preferences for user."""
        key = f"{PFX_MEM_PROCEDURAL}:{user_id}"
        self.redis.delete(key)
        logger.debug(f"Deleted procedural profile for {user_id}")

    def set_session(self, session_id: str, state: SessionState) -> None:
        """Store session state in Redis with TTL."""
        key = f"session:{session_id}"
        json_str = state.model_dump_json()
        self.redis.setex(key, TTL_SESSION, json_str)
        logger.debug(f"Stored session {session_id}")

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Retrieve session from Redis."""
        key = f"session:{session_id}"
        json_str = self.redis.get(key)
        if json_str:
            return SessionState(**json.loads(json_str))
        return None

    def delete_session(self, session_id: str) -> None:
        """Delete session from Redis."""
        key = f"session:{session_id}"
        self.redis.delete(key)
        logger.debug(f"Deleted session {session_id}")

    # ── ChromaDB Operations (Episodic) ──

    def save_episodic(self, doc: EpisodicDoc) -> None:
        """Store episodic document in ChromaDB."""
        collection_name = f"episodic_{doc.user_id}"
        try:
            collection = self.chroma_client.get_or_create_collection(name=collection_name)
            collection.add(
                ids=[doc.doc_id],
                documents=[doc.document],
                metadatas=[
                    {
                        "type": doc.type,
                        "importance": doc.importance,
                        "tags": ",".join(doc.tags),
                        "created_at": doc.created_at.isoformat(),
                    }
                ],
            )
            logger.debug(f"Stored episodic doc {doc.doc_id}")
        except Exception as e:
            logger.error(f"Failed to save episodic: {e}")
            raise

    def get_episodic(self, user_id: str, doc_id: str) -> Optional[EpisodicDoc]:
        """Retrieve single episodic document by ID."""
        collection_name = f"episodic_{user_id}"
        try:
            collection = self.chroma_client.get_or_create_collection(name=collection_name)
            results = collection.get(ids=[doc_id])
            if results and results["documents"]:
                doc = results["documents"][0]
                meta = results["metadatas"][0]
                return EpisodicDoc(
                    doc_id=doc_id,
                    document=doc,
                    user_id=user_id,
                    type=meta.get("type", "raw_turn"),
                    session_id="",
                    created_at=meta.get("created_at", ""),
                    importance=float(meta.get("importance", 0.5)),
                    tags=meta.get("tags", "").split(",") if meta.get("tags") else [],
                )
        except Exception as e:
            logger.error(f"Failed to get episodic: {e}")
        return None

    def search_episodic(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        min_importance: float = 0.3,
    ) -> list[EpisodicDoc]:
        """Semantic search episodic memory by similarity."""
        collection_name = f"episodic_{user_id}"
        try:
            collection = self.chroma_client.get_or_create_collection(name=collection_name)
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                where={"importance": {"$gte": min_importance}},
            )

            docs = []
            if results and results["documents"]:
                for i, doc_text in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i]
                    docs.append(
                        EpisodicDoc(
                            doc_id=results["ids"][0][i],
                            document=doc_text,
                            user_id=user_id,
                            type=meta.get("type", "raw_turn"),
                            session_id="",
                            created_at=meta.get("created_at", ""),
                            importance=float(meta.get("importance", 0.5)),
                            tags=meta.get("tags", "").split(",") if meta.get("tags") else [],
                        )
                    )
            return docs
        except Exception as e:
            logger.error(f"Failed to search episodic: {e}")
            return []

    def delete_episodic(self, user_id: str, doc_id: str) -> None:
        """Remove single episodic document."""
        collection_name = f"episodic_{user_id}"
        try:
            collection = self.chroma_client.get_or_create_collection(name=collection_name)
            collection.delete(ids=[doc_id])
            logger.debug(f"Deleted episodic doc {doc_id}")
        except Exception as e:
            logger.error(f"Failed to delete episodic: {e}")


if __name__ == "__main__":
    # Test connection
    store = MemoryStore()
    print("[OK] Memory store initialized")
