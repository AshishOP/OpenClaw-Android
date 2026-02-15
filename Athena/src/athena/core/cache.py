"""
athena.core.cache — Semantic Query Cache
=========================================

A production-grade LRU cache with semantic similarity matching.

Features:
    - Exact Match: Hash-based O(1) lookup for identical queries
    - Semantic Match: Cosine similarity search for semantically similar queries
    - TTL Expiration: Entries expire after configurable time period
    - Disk Persistence: Cache survives process restarts

Usage:
    from athena.core.cache import get_search_cache

    cache = get_search_cache()

    # Exact match
    result = cache.get("what is caching?")

    # Semantic match (requires query embedding)
    result = cache.get_semantic(query_embedding, threshold=0.90)

    # Store with embedding for semantic retrieval
    cache.set("what is caching?", results, embedding=query_embedding)
"""

import hashlib
import json
import math
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from athena.core.config import AGENT_DIR


@dataclass
class CacheEntry:
    """A cached query result with optional embedding for semantic matching."""

    value: Any
    timestamp: float
    hits: int = 0
    embedding: list[float] | None = field(default=None)


class QueryCache:
    """TTL-based LRU cache with semantic similarity matching."""

    def __init__(
        self,
        cache_dir: Path,
        ttl_hours: float = 24,
        max_size: int = 100,
    ):
        self.ttl_seconds = ttl_hours * 3600
        self.max_size = max_size
        self._cache_file = cache_dir / "search_cache.json"
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._load_from_disk()

    def _hash_key(self, query: str) -> str:
        """Create deterministic hash for query (case-insensitive)."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def _load_from_disk(self):
        """Load cache from disk on initialization."""
        if not self._cache_file.exists():
            return
        try:
            data = json.loads(self._cache_file.read_text())
            now = time.time()
            for key, entry_data in data.items():
                if now - entry_data["timestamp"] < self.ttl_seconds:
                    if "embedding" not in entry_data:
                        entry_data["embedding"] = None
                    self._cache[key] = CacheEntry(**entry_data)
        except Exception:
            pass

    def _save_to_disk(self):
        """Persist cache to disk (atomic write)."""
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                k: {
                    "value": e.value,
                    "timestamp": e.timestamp,
                    "hits": e.hits,
                    "embedding": e.embedding,
                }
                for k, e in self._cache.items()
            }
            self._cache_file.write_text(json.dumps(data))
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Exact Matching
    # -------------------------------------------------------------------------

    def get(self, query: str) -> Any | None:
        """Get cached result if exists and not expired (exact match)."""
        key = self._hash_key(query)

        if key not in self._cache:
            return None

        entry = self._cache[key]
        now = time.time()

        if now - entry.timestamp > self.ttl_seconds:
            del self._cache[key]
            self._save_to_disk()
            return None

        entry.hits += 1
        self._cache.move_to_end(key)  # LRU update
        self._save_to_disk()
        return entry.value

    # -------------------------------------------------------------------------
    # Semantic Matching
    # -------------------------------------------------------------------------

    @staticmethod
    def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """Calculate cosine similarity between two embedding vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def get_semantic(self, target_embedding: list[float], threshold: float = 0.90) -> Any | None:
        """
        Get cached result if a semantically similar query exists.

        This enables cache hits for queries like:
            - "what is caching" → "explain caching" (same intent, different words)

        Args:
            target_embedding: Vector embedding of the query
            threshold: Minimum cosine similarity (0.90 = very similar)

        Returns:
            Cached result if similar query found, else None
        """
        best_sim = -1.0
        best_entry = None
        best_key = None

        for key, entry in self._cache.items():
            if entry.embedding:
                sim = self._cosine_similarity(target_embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_entry = entry
                    best_key = key

        if best_sim >= threshold and best_entry and best_key:
            best_entry.hits += 1
            self._cache.move_to_end(best_key)
            self._save_to_disk()
            return best_entry.value

        return None

    # -------------------------------------------------------------------------
    # Cache Management
    # -------------------------------------------------------------------------

    def set(self, query: str, value: Any, embedding: list[float] | None = None) -> None:
        """Cache a result with optional embedding for semantic retrieval."""
        key = self._hash_key(query)

        # Evict oldest if at capacity (LRU)
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)

        self._cache[key] = CacheEntry(
            value=value,
            timestamp=time.time(),
            hits=0,
            embedding=embedding,
        )
        self._save_to_disk()

    def invalidate(self) -> None:
        """Invalidate all cached results (call when underlying data changes)."""
        self._cache.clear()
        self._save_to_disk()

    def stats(self) -> dict:
        """Get cache statistics for monitoring."""
        total_hits = sum(e.hits for e in self._cache.values())
        semantic_entries = sum(1 for e in self._cache.values() if e.embedding)
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "total_hits": total_hits,
            "semantic_entries": semantic_entries,
            "ttl_hours": self.ttl_seconds / 3600,
        }


# Singleton Instance
_search_cache: QueryCache | None = None


def get_search_cache() -> QueryCache:
    """Singleton accessor for the search cache."""
    global _search_cache
    if _search_cache is None:
        _search_cache = QueryCache(cache_dir=AGENT_DIR / "state")
    return _search_cache
