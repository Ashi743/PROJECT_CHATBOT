"""Sync cache wrappers for Streamlit compatibility."""

import logging
from typing import Optional, Any
from memory.short_term import get_cache

logger = logging.getLogger(__name__)


def sync_get_cached_response(query: str) -> Optional[str]:
    """Get cached LLM response for exact query match."""
    try:
        cache = get_cache()
        return cache.get_cached_response(query)
    except Exception as e:
        logger.warning(f"Response cache lookup failed: {e}")
        return None


def sync_cache_response(query: str, response: str) -> None:
    """Cache LLM response for exact query."""
    try:
        cache = get_cache()
        cache.cache_response(query, response)
    except Exception as e:
        logger.warning(f"Response caching failed: {e}")


def sync_get_similar_cached_response(query: str) -> Optional[str]:
    """Get cached response for semantically similar query."""
    try:
        cache = get_cache()
        return cache.get_similar_cached_response(query)
    except Exception as e:
        logger.warning(f"Semantic cache lookup failed: {e}")
        return None


def sync_cache_semantic(query: str, response: str) -> None:
    """Cache for semantic similarity matching."""
    try:
        cache = get_cache()
        cache.cache_semantic(query, response)
    except Exception as e:
        logger.warning(f"Semantic caching failed: {e}")


def sync_get_tool_result(tool_name: str, args: dict) -> Optional[dict]:
    """Get cached tool/API result."""
    try:
        cache = get_cache()
        return cache.get_tool_result(tool_name, args)
    except Exception as e:
        logger.warning(f"Tool cache lookup failed: {e}")
        return None


def sync_cache_tool_result(tool_name: str, args: dict, result: dict) -> None:
    """Cache tool/API result."""
    try:
        cache = get_cache()
        cache.cache_tool_result(tool_name, args, result)
    except Exception as e:
        logger.warning(f"Tool result caching failed: {e}")


def sync_get_node_result(node_name: str, inputs: dict) -> Optional[dict]:
    """Get cached node execution result."""
    try:
        cache = get_cache()
        return cache.get_node_result(node_name, inputs)
    except Exception as e:
        logger.warning(f"Node cache lookup failed: {e}")
        return None


def sync_cache_node_result(node_name: str, inputs: dict, output: dict) -> None:
    """Cache node execution result."""
    try:
        cache = get_cache()
        cache.cache_node_result(node_name, inputs, output)
    except Exception as e:
        logger.warning(f"Node result caching failed: {e}")


def sync_clear_cache(cache_type: str = "all") -> None:
    """Clear specific cache layer or all."""
    try:
        cache = get_cache()
        if cache_type == "all":
            cache.clear_all_caches()
        elif cache_type == "response":
            cache.clear_response_cache()
        logger.debug(f"Cleared {cache_type} cache")
    except Exception as e:
        logger.warning(f"Cache clear failed: {e}")


def sync_track_tokens(input_tokens: int = 0, output_tokens: int = 0) -> None:
    """Track API token usage."""
    try:
        cache = get_cache()
        cache.track_tokens(input_tokens, output_tokens)
    except Exception as e:
        logger.warning(f"Token tracking failed: {e}")


def sync_get_token_usage() -> dict:
    """Get current token usage."""
    try:
        cache = get_cache()
        return cache.get_token_usage()
    except Exception as e:
        logger.warning(f"Token usage retrieval failed: {e}")
        return {"input": 0, "output": 0, "total": 0}


def sync_get_cache_stats() -> dict:
    """Get cache statistics."""
    try:
        cache = get_cache()
        return cache.get_cache_stats()
    except Exception as e:
        logger.warning(f"Cache stats failed: {e}")
        return {}


if __name__ == "__main__":
    # Test
    sync_cache_response("Test query", "Test response")
    result = sync_get_cached_response("Test query")
    print(f"[OK] Cache wrapper: {result}")
