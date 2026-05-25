"""
Budget guard — enforces per-user daily limits on token spend.

Limits are checked BEFORE each LLM call.
Counters are stored in Redis with a 24h TTL (rolling day window).

Falls back gracefully if Redis is unavailable.
"""

import os
import json
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ── Config (override via env vars) ────────────────────────────────────────
DAILY_TOKEN_LIMIT   = int(float(os.getenv("DAILY_TOKEN_LIMIT",   "100000")))   # 100k tokens/user/day
DAILY_COST_LIMIT    = float(os.getenv("DAILY_COST_LIMIT",        "1.00"))      # $1.00/user/day
GLOBAL_COST_LIMIT   = float(os.getenv("GLOBAL_COST_LIMIT",       "50.00"))     # $50/day total
MAX_INPUT_CHARS     = int(os.getenv("MAX_INPUT_CHARS",            "500"))       # topic length cap
MAX_ITERATIONS      = int(os.getenv("MAX_ITERATIONS",             "2"))         # agent loop cap
BUDGET_WINDOW_SECS  = 86400                                                     # 24 hours


class BudgetExceededError(Exception):
    """Raised when a user or global budget limit is hit."""
    def __init__(self, reason: str, limit_type: str):
        self.reason = reason
        self.limit_type = limit_type
        super().__init__(reason)


class BudgetGuard:
    """
    Usage:
        guard = BudgetGuard()
        guard.check(user_id)                    # raises BudgetExceededError if over limit
        guard.record(user_id, tokens, cost)     # call after each LLM response
        summary = guard.get_usage(user_id)      # current day stats
    """

    def __init__(self):
        self._r = self._connect()

    def _connect(self):
        try:
            import redis
            r = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                decode_responses=True,
                socket_connect_timeout=1,
            )
            r.ping()
            return r
        except Exception as e:
            logger.warning(f"[budget] Redis unavailable: {e} — budget guard disabled")
            return None

    def _key(self, user_id: str) -> str:
        return f"budget:{user_id}"

    def _global_key(self) -> str:
        return "budget:__global__"

    def _get_usage(self, key: str) -> dict:
        if not self._r:
            return {"tokens": 0, "cost": 0.0, "requests": 0}
        raw = self._r.get(key)
        if raw:
            return json.loads(raw)
        return {"tokens": 0, "cost": 0.0, "requests": 0}

    def _save_usage(self, key: str, data: dict):
        if not self._r:
            return
        self._r.setex(key, BUDGET_WINDOW_SECS, json.dumps(data))

    # ── Public API ──────────────────────────────────────────────────────

    def check(self, user_id: str, topic: str = ""):
        """
        Pre-flight check before running the agent.
        Raises BudgetExceededError if any limit is hit.
        """
        # Input length guard
        if len(topic) > MAX_INPUT_CHARS:
            raise BudgetExceededError(
                f"Topic too long ({len(topic)} chars). Max {MAX_INPUT_CHARS}.",
                "input_length"
            )

        if not self._r:
            return  # Redis down — allow through (fail open)

        # Per-user checks
        usage = self._get_usage(self._key(user_id))
        if usage["tokens"] >= DAILY_TOKEN_LIMIT:
            raise BudgetExceededError(
                f"Daily token limit reached ({DAILY_TOKEN_LIMIT:,} tokens). Resets in 24h.",
                "user_tokens"
            )
        if usage["cost"] >= DAILY_COST_LIMIT:
            raise BudgetExceededError(
                f"Daily cost limit reached (${DAILY_COST_LIMIT:.2f}). Resets in 24h.",
                "user_cost"
            )

        # Global checks
        global_usage = self._get_usage(self._global_key())
        if global_usage["cost"] >= GLOBAL_COST_LIMIT:
            raise BudgetExceededError(
                f"Global daily cost limit reached (${GLOBAL_COST_LIMIT:.2f}). Try again tomorrow.",
                "global_cost"
            )

    def record(self, user_id: str, tokens: int, cost: float):
        """Call this after each successful agent run to update counters."""
        if not self._r:
            return

        # Per-user
        key = self._key(user_id)
        usage = self._get_usage(key)
        usage["tokens"] += tokens
        usage["cost"] = round(usage["cost"] + cost, 6)
        usage["requests"] = usage.get("requests", 0) + 1
        self._save_usage(key, usage)

        # Global
        gkey = self._global_key()
        gusage = self._get_usage(gkey)
        gusage["tokens"] += tokens
        gusage["cost"] = round(gusage["cost"] + cost, 6)
        gusage["requests"] = gusage.get("requests", 0) + 1
        self._save_usage(gkey, gusage)

        logger.info(
            f"[budget] user={user_id} +{tokens} tokens +${cost:.5f} "
            f"| day total: {usage['tokens']} tokens ${usage['cost']:.4f}"
        )

    def get_usage(self, user_id: str) -> dict:
        """Return current day usage for a user."""
        usage = self._get_usage(self._key(user_id))
        return {
            "user_id": user_id,
            "tokens_used": usage["tokens"],
            "tokens_limit": DAILY_TOKEN_LIMIT,
            "tokens_remaining": max(0, DAILY_TOKEN_LIMIT - usage["tokens"]),
            "cost_usd": round(usage["cost"], 4),
            "cost_limit_usd": DAILY_COST_LIMIT,
            "cost_remaining_usd": round(max(0.0, DAILY_COST_LIMIT - usage["cost"]), 4),
            "requests_today": usage.get("requests", 0),
        }

    def get_global_usage(self) -> dict:
        usage = self._get_usage(self._global_key())
        return {
            "total_tokens": usage["tokens"],
            "total_cost_usd": round(usage["cost"], 4),
            "total_requests": usage.get("requests", 0),
            "global_cost_limit_usd": GLOBAL_COST_LIMIT,
        }


# Singleton
budget_guard = BudgetGuard()
