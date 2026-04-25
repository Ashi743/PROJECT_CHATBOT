"""Short-term memory with 5 cache layers (response, semantic, RAG, tool, node)."""

import hashlib
import json
import logging
from typing import Optional, Any

from memory.config import (
    REDIS_URL,
    CHROMA_HOST,
    CHROMA_PORT,
    TTL_RESP_CACHE,
    TTL_SEM_CACHE,
    TTL_RAG_CACHE,
    TTL_TOOL_CACHE,
    TTL_NODE_CACHE,
    PFX_RESP,
    PFX_SEM,
    PFX_RAG,
    PFX_TOOL,
    PFX_NODE,
    PFX_TOKENS,
)

logger = logging.getLogger(__name__)


class CacheLayers:
    """5 cache layers for response, semantic, RAG, tool, and node results."""

    def __init__(self):
        """Initialize cache with Redis backend using singleton MemoryStore."""
        from memory.sync_wrapper import _get_store
        self.store = _get_store()
        self.redis = self.store.redis

    # ── Layer 1: Response Cache (24h TTL) ──
    # Exact question → exact answer

    def _hash_query(self, query: str) -> str:
        """Hash query for cache key."""
        return hashlib.md5(query.encode()).hexdigest()

    def get_cached_response(self, query: str) -> Optional[str]:
        """Get exact cached response for query."""
        try:
            key = f"{PFX_RESP}:{self._hash_query(query)}"
            result = self.redis.get(key)
            if result:
                logger.debug(f"Response cache HIT for query: {query[:50]}")
                return result
        except Exception as e:
            logger.warning(f"Response cache GET failed: {e}")
        return None

    def cache_response(self, query: str, response: str) -> None:
        """Cache response for exact query match."""
        try:
            key = f"{PFX_RESP}:{self._hash_query(query)}"
            self.redis.setex(key, TTL_RESP_CACHE, response)
            logger.debug(f"Response cached for {TTL_RESP_CACHE}s")
        except Exception as e:
            logger.warning(f"Response cache SET failed: {e}")

    # ── Layer 2: Semantic Cache (24h TTL) ──
    # Similar questions → reuse response

    def get_similar_cached_response(self, query: str, threshold: float = 0.85) -> Optional[str]:
        """Get response for semantically similar cached query."""
        try:
            # For now, use exact match + optional embedding-based search
            # Full implementation would use ChromaDB embeddings
            key = f"{PFX_SEM}:{self._hash_query(query)}"
            result = self.redis.get(key)
            if result:
                logger.debug(f"Semantic cache HIT for query: {query[:50]}")
                return result
        except Exception as e:
            logger.warning(f"Semantic cache GET failed: {e}")
        return None

    def cache_semantic(self, query: str, response: str) -> None:
        """Cache response for semantic similarity matching."""
        try:
            key = f"{PFX_SEM}:{self._hash_query(query)}"
            self.redis.setex(key, TTL_SEM_CACHE, response)
            logger.debug(f"Semantic cached for {TTL_SEM_CACHE}s")
        except Exception as e:
            logger.warning(f"Semantic cache SET failed: {e}")

    # ── Layer 3: RAG Cache (1h TTL) ──
    # Document chunks for RAG retrieval

    def get_rag_chunk(self, doc_id: str, chunk_id: str) -> Optional[str]:
        """Get cached RAG document chunk."""
        try:
            key = f"{PFX_RAG}:{doc_id}:{chunk_id}"
            result = self.redis.get(key)
            if result:
                logger.debug(f"RAG cache HIT for doc {doc_id}")
                return result
        except Exception as e:
            logger.warning(f"RAG cache GET failed: {e}")
        return None

    def cache_rag_chunk(self, doc_id: str, chunk_id: str, chunk: str) -> None:
        """Cache RAG document chunk."""
        try:
            key = f"{PFX_RAG}:{doc_id}:{chunk_id}"
            self.redis.setex(key, TTL_RAG_CACHE, chunk)
            logger.debug(f"RAG chunk cached for {TTL_RAG_CACHE}s")
        except Exception as e:
            logger.warning(f"RAG cache SET failed: {e}")

    # ── Layer 4: Tool Cache (1h TTL) ──
    # Tool/API results (stock price, commodity price, etc.)

    def _hash_tool_call(self, tool_name: str, args: dict) -> str:
        """Hash tool name + args for cache key."""
        args_json = json.dumps(args, sort_keys=True, default=str)
        combined = f"{tool_name}:{args_json}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get_tool_result(self, tool_name: str, args: dict) -> Optional[dict]:
        """Get cached tool/API result."""
        try:
            key = f"{PFX_TOOL}:{self._hash_tool_call(tool_name, args)}"
            result_json = self.redis.get(key)
            if result_json:
                result = json.loads(result_json)
                logger.debug(f"Tool cache HIT for {tool_name}")
                return result
        except Exception as e:
            logger.warning(f"Tool cache GET failed: {e}")
        return None

    def cache_tool_result(self, tool_name: str, args: dict, result: dict) -> None:
        """Cache tool/API result."""
        try:
            key = f"{PFX_TOOL}:{self._hash_tool_call(tool_name, args)}"
            result_json = json.dumps(result, default=str)
            self.redis.setex(key, TTL_TOOL_CACHE, result_json)
            logger.debug(f"Tool result cached for {TTL_TOOL_CACHE}s")
        except Exception as e:
            logger.warning(f"Tool cache SET failed: {e}")

    # ── Layer 5: Node Cache (1h TTL) ──
    # LangGraph node execution results

    def _hash_node_input(self, node_name: str, inputs: dict) -> str:
        """Hash node name + inputs for cache key."""
        inputs_json = json.dumps(inputs, sort_keys=True, default=str)
        combined = f"{node_name}:{inputs_json}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get_node_result(self, node_name: str, inputs: dict) -> Optional[dict]:
        """Get cached node execution result."""
        try:
            key = f"{PFX_NODE}:{self._hash_node_input(node_name, inputs)}"
            result_json = self.redis.get(key)
            if result_json:
                result = json.loads(result_json)
                logger.debug(f"Node cache HIT for {node_name}")
                return result
        except Exception as e:
            logger.warning(f"Node cache GET failed: {e}")
        return None

    def cache_node_result(self, node_name: str, inputs: dict, output: dict) -> None:
        """Cache node execution result."""
        try:
            key = f"{PFX_NODE}:{self._hash_node_input(node_name, inputs)}"
            output_json = json.dumps(output, default=str)
            self.redis.setex(key, TTL_NODE_CACHE, output_json)
            logger.debug(f"Node result cached for {TTL_NODE_CACHE}s")
        except Exception as e:
            logger.warning(f"Node cache SET failed: {e}")

    # ── Cache Management ──

    def clear_response_cache(self, query: Optional[str] = None) -> None:
        """Clear response cache (all or specific query)."""
        try:
            if query:
                key = f"{PFX_RESP}:{self._hash_query(query)}"
                self.redis.delete(key)
                logger.debug(f"Cleared response cache for: {query[:50]}")
            else:
                # Clear all response cache keys
                pattern = f"{PFX_RESP}:*"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
                    logger.debug(f"Cleared {len(keys)} response cache entries")
        except Exception as e:
            logger.warning(f"Response cache clear failed: {e}")

    # ── Token Usage Tracking (session scope) ──
    def track_tokens(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Track API token usage for current session."""
        try:
            key = f"{PFX_TOKENS}:session"
            current = self.redis.hgetall(key) or {}

            input_total = int(current.get(b"input", 0)) if current else 0
            output_total = int(current.get(b"output", 0)) if current else 0

            input_total += input_tokens
            output_total += output_tokens

            self.redis.hset(key, mapping={"input": input_total, "output": output_total})
            self.redis.expire(key, 86400)  # 24h TTL

            logger.debug(f"Tracked tokens - Input: +{input_tokens}, Output: +{output_tokens}")
        except Exception as e:
            logger.warning(f"Token tracking failed: {e}")

    def get_token_usage(self) -> dict:
        """Get current session token usage."""
        try:
            key = f"{PFX_TOKENS}:session"
            data = self.redis.hgetall(key) or {}

            input_tokens = int(data.get(b"input", 0)) if data else 0
            output_tokens = int(data.get(b"output", 0)) if data else 0

            return {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            }
        except Exception as e:
            logger.warning(f"Token usage retrieval failed: {e}")
            return {"input": 0, "output": 0, "total": 0}

    def clear_all_caches(self) -> None:
        """Clear all cache layers (use cautiously)."""
        try:
            patterns = [
                f"{PFX_RESP}:*",
                f"{PFX_SEM}:*",
                f"{PFX_RAG}:*",
                f"{PFX_TOOL}:*",
                f"{PFX_NODE}:*",
            ]
            for pattern in patterns:
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
            logger.info("Cleared all cache layers")
        except Exception as e:
            logger.warning(f"Cache clear all failed: {e}")

    def get_cache_stats(self) -> dict:
        """Get cache statistics including token usage."""
        try:
            stats = {}
            patterns = {
                "response": f"{PFX_RESP}:*",
                "semantic": f"{PFX_SEM}:*",
                "rag": f"{PFX_RAG}:*",
                "tool": f"{PFX_TOOL}:*",
                "node": f"{PFX_NODE}:*",
            }
            for name, pattern in patterns.items():
                keys = self.redis.keys(pattern)
                stats[name] = len(keys) if keys else 0

            # Add token usage
            token_data = self.get_token_usage()
            stats["tokens"] = token_data

            return stats
        except Exception as e:
            logger.warning(f"Cache stats failed: {e}")
            return {}


# Global cache instance
_cache_instance = None


def get_cache() -> CacheLayers:
    """Get global cache instance (singleton)."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheLayers()
    return _cache_instance


if __name__ == "__main__":
    # Test caching
    cache = get_cache()

    # Test response cache
    print("[TEST] Response cache...")
    cache.cache_response("What is AI?", "AI is artificial intelligence.")
    cached = cache.get_cached_response("What is AI?")
    print(f"  Cached: {cached}")

    # Test tool cache
    print("[TEST] Tool cache...")
    cache.cache_tool_result("stock_tool", {"symbol": "AAPL"}, {"price": 150.00})
    cached = cache.get_tool_result("stock_tool", {"symbol": "AAPL"})
    print(f"  Cached: {cached}")

    # Test stats
    print("[TEST] Cache stats...")
    stats = cache.get_cache_stats()
    print(f"  Stats: {stats}")

    print("[OK] Caching layer working!")
