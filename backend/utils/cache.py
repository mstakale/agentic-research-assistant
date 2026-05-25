"""
Two-level cache for research results:

  Level 1 — Exact cache:  hash(topic + provider) → stored result (free replay)
  Level 2 — Semantic cache: embedding similarity check (skips similar queries)

Falls back gracefully if Redis is unavailable — app still works, just no caching.
"""

import os
import json
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Optional Redis import ──────────────────────────────────────────────────
try:
    import redis
    _redis_available = True
except ImportError:
    _redis_available = False
    logger.warning("redis package not installed — caching disabled. pip install redis")

# ── Optional numpy for cosine sim ─────────────────────────────────────────
try:
    import numpy as np
    _numpy_available = True
except ImportError:
    _numpy_available = False


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 3600 * 24))  # 24h default
SEMANTIC_THRESHOLD = float(os.getenv("SEMANTIC_THRESHOLD", 0.92))    # 92% similarity = cache hit


def _get_redis():
    if not _redis_available:
        return None
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1)
        r.ping()
        return r
    except Exception as e:
        logger.warning(f"Redis unavailable: {e} — running without cache")
        return None


def _make_key(topic: str, provider: str) -> str:
    raw = f"{topic.strip().lower()}:{provider}"
    return "research:" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not _numpy_available:
        return 0.0
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom else 0.0


def _embed(text: str) -> Optional[list[float]]:
    """Lightweight embedding via sentence-transformers (optional)."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model.encode(text).tolist()
    except Exception:
        return None


class ResearchCache:
    """
    Usage:
        cache = ResearchCache()
        hit = cache.get(topic, provider)
        if hit:
            return hit
        # ... run agent ...
        cache.set(topic, provider, result)
    """

    def __init__(self):
        self._r = _get_redis()
        self._available = self._r is not None

    def get(self, topic: str, provider: str) -> Optional[dict]:
        if not self._available:
            return None

        # Level 1: exact hash
        key = _make_key(topic, provider)
        raw = self._r.get(key)
        if raw:
            logger.info(f"[cache] Exact hit for '{topic[:40]}'")
            data = json.loads(raw)
            data["cache_hit"] = "exact"
            return data

        # Level 2: semantic similarity scan
        embedding = _embed(topic)
        if embedding and _numpy_available:
            for k in self._r.scan_iter("research:*"):
                stored_raw = self._r.get(k)
                if not stored_raw:
                    continue
                stored = json.loads(stored_raw)
                stored_emb = stored.get("_embedding")
                if not stored_emb:
                    continue
                sim = _cosine_similarity(embedding, stored_emb)
                if sim >= SEMANTIC_THRESHOLD:
                    logger.info(f"[cache] Semantic hit ({sim:.3f}) for '{topic[:40]}'")
                    stored["cache_hit"] = f"semantic:{sim:.3f}"
                    return stored

        return None

    def set(self, topic: str, provider: str, result: dict):
        if not self._available:
            return
        key = _make_key(topic, provider)
        payload = dict(result)
        payload.pop("cache_hit", None)

        # Store embedding for future semantic lookups
        embedding = _embed(topic)
        if embedding:
            payload["_embedding"] = embedding

        self._r.setex(key, CACHE_TTL_SECONDS, json.dumps(payload))
        logger.info(f"[cache] Stored result for '{topic[:40]}' (TTL {CACHE_TTL_SECONDS}s)")

    def invalidate(self, topic: str, provider: str):
        if not self._available:
            return
        self._r.delete(_make_key(topic, provider))

    @property
    def is_available(self) -> bool:
        return self._available


# Singleton
research_cache = ResearchCache()
