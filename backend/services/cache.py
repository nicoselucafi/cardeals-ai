"""In-memory caching layer using cachetools."""

import logging
from typing import Any

from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Cache search results: keyed on sorted parameters, 1 hour TTL
search_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)

# Track cache stats
_cache_hits = 0
_cache_misses = 0


def get_cache_key(**params) -> str:
    """Generate consistent cache key from search parameters."""
    # Filter out None values and sort for consistency
    filtered = {k: v for k, v in params.items() if v is not None}
    sorted_params = sorted(filtered.items())
    return str(sorted_params)


def get_cached(key: str) -> Any | None:
    """Get item from cache, returns None if not found."""
    global _cache_hits, _cache_misses

    result = search_cache.get(key)
    if result is not None:
        _cache_hits += 1
        logger.debug(f"Cache HIT for key: {key[:50]}...")
        return result

    _cache_misses += 1
    logger.debug(f"Cache MISS for key: {key[:50]}...")
    return None


def set_cached(key: str, value: Any) -> None:
    """Store item in cache."""
    search_cache[key] = value
    logger.debug(f"Cache SET for key: {key[:50]}...")


def invalidate_all_caches() -> None:
    """Clear all caches. Call this after scraper runs."""
    global _cache_hits, _cache_misses

    search_cache.clear()
    _cache_hits = 0
    _cache_misses = 0
    logger.info("All caches invalidated")


def get_cache_stats() -> dict:
    """Get cache statistics."""
    total = _cache_hits + _cache_misses
    hit_rate = (_cache_hits / total * 100) if total > 0 else 0

    return {
        "hits": _cache_hits,
        "misses": _cache_misses,
        "total_requests": total,
        "hit_rate_percent": round(hit_rate, 2),
        "cache_size": len(search_cache),
        "max_size": search_cache.maxsize,
        "ttl_seconds": search_cache.ttl,
    }
