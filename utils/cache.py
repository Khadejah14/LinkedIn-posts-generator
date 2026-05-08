"""In-memory caching utility with TTL and hash-based keys."""

import hashlib
import json
import time
import functools
from threading import Lock
from typing import Any, Callable


class MemoryCache:
    """Thread-safe in-memory cache with TTL eviction."""

    def __init__(self, default_ttl: int = 3600, max_size: int = 256):
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
        self.max_size = max_size

    def get(self, key: str) -> tuple[bool, Any]:
        with self._lock:
            if key not in self._store:
                return False, None
            ts, value = self._store[key]
            if time.time() - ts > self.default_ttl:
                del self._store[key]
                return False, None
            return True, value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        with self._lock:
            if len(self._store) >= self.max_size:
                oldest_key = min(self._store, key=lambda k: self._store[k][0])
                del self._store[oldest_key]
            self._store[key] = (time.time(), value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        return len(self._store)


_cache = MemoryCache()


def cached(ttl: int | None = None):
    """Decorator that caches function results based on input hash.

    Args:
        ttl: Time-to-live in seconds. Uses cache default (3600s) if not set.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key_prefix = func.__qualname__
            raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
            cache_key = f"{key_prefix}:{hashlib.sha256(raw.encode()).hexdigest()[:32]}"

            hit, value = _cache.get(cache_key)
            if hit:
                return value

            result = func(*args, **kwargs)
            _cache.set(cache_key, result)
            return result

        wrapper.cache_clear = _cache.clear
        return wrapper
    return decorator


def get_cache() -> MemoryCache:
    return _cache
