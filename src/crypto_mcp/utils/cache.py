"""TTL-based response cache for MCP tools."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class CacheEntry:
    """single cache entry with value and expiration time."""
    value: Any
    expires_at: float


@dataclass
class CacheStats:
    """tracks cache hit/miss statistics."""
    hits: int = 0
    misses: int = 0


# global stats instance
_cache_stats = CacheStats()


def get_cache_stats() -> dict[str, int]:
    """returns current cache statistics."""
    return {"hits": _cache_stats.hits, "misses": _cache_stats.misses}


def reset_cache_stats() -> None:
    """resets cache statistics (useful for testing)."""
    global _cache_stats
    _cache_stats = CacheStats()


class TTLCache:
    """simple TTL-based cache for async functions.

    stores results keyed by function arguments.
    entries expire after ttl seconds.
    """

    def __init__(self, ttl: float = 3.0, enabled: bool = True):
        self._ttl = ttl
        self._enabled = enabled
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    @property
    def ttl(self) -> float:
        return self._ttl

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """creates cache key from function arguments."""
        # sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        return f"{args}:{sorted_kwargs}"

    async def get(self, key: str) -> tuple[bool, Any]:
        """gets value from cache if exists and not expired.

        returns (hit, value) tuple.
        """
        if not self._enabled:
            return False, None

        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                _cache_stats.misses += 1
                return False, None

            if time.monotonic() > entry.expires_at:
                # expired, remove entry
                del self._cache[key]
                _cache_stats.misses += 1
                return False, None

            _cache_stats.hits += 1
            return True, entry.value

    async def set(self, key: str, value: Any) -> None:
        """stores value in cache with TTL."""
        if not self._enabled:
            return

        async with self._lock:
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=time.monotonic() + self._ttl,
            )

    async def clear(self) -> None:
        """clears all cache entries."""
        async with self._lock:
            self._cache.clear()

    def cached(
        self, func: Callable[P, R]
    ) -> Callable[P, R]:
        """decorator to cache async function results.

        usage:
            cache = TTLCache(ttl=3.0)

            @cache.cached
            async def get_data(symbol: str) -> dict:
                ...
        """
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = self._make_key(*args, **kwargs)

            hit, value = await self.get(key)
            if hit:
                return value

            result = await func(*args, **kwargs)
            await self.set(key, result)
            return result

        # preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
