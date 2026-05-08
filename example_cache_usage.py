"""Example: caching layer in action.

Run this twice to see cache hits on the second run.
"""

import time
from utils.cache import get_cache, cached


# --- Direct cache usage ---
from utils.cache import MemoryCache

cache = MemoryCache(default_ttl=60)

cache.set("greeting", "hello")
hit, val = cache.get("greeting")
print(f"Direct cache: hit={hit}, value={val}")


# --- Decorator usage ---
@cached(ttl=120)
def expensive_call(x: int) -> int:
    """Simulates a slow operation."""
    time.sleep(0.5)
    return x * 2


# First call - cache miss
start = time.time()
result1 = expensive_call(5)
elapsed1 = time.time() - start
print(f"\nFirst call:  result={result1}, took={elapsed1:.3f}s (cache miss)")

# Second call - cache hit
start = time.time()
result2 = expensive_call(5)
elapsed2 = time.time() - start
print(f"Second call: result={result2}, took={elapsed2:.3f}s (cache hit)")

# Different input - cache miss
start = time.time()
result3 = expensive_call(10)
elapsed3 = time.time() - start
print(f"Diff input:  result={result3}, took={elapsed3:.3f}s (cache miss)")


# --- Service-level demo ---
print("\n--- Service cache stats ---")
c = get_cache()
print(f"Cache size: {c.size()} entries")
print(f"Speedup: {elapsed1 / elapsed2:.0f}x on cached calls")
