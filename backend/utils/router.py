"""
Model router — classifies query complexity and picks the cheapest model that can handle it.

Cost impact:
  Claude Haiku  → ~$0.002 per query  (simple)
  Claude Sonnet → ~$0.05  per query  (complex)
  GPT-4o        → ~$0.08  per query  (complex)

Routing saves ~80-95% on simple queries.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ── Simple heuristic signals ───────────────────────────────────────────────
COMPLEX_SIGNALS = [
    # Multi-part questions
    r"\band\b.{0,40}\band\b",
    r"compare|contrast|difference between|vs\.?|versus",
    r"explain.*how|how does.*work|why does",
    r"pros and cons|advantages|disadvantages|trade-?offs",
    r"history of|evolution of|timeline",
    r"impact of|effect of|implications",
    r"recent|latest|2024|2025|current",
    r"research|study|evidence|data",
    r"technical|architecture|design|implementation",
]

SIMPLE_SIGNALS = [
    r"^what is\b",
    r"^who is\b",
    r"^define\b",
    r"^list\b",
    r"^when (was|did|is)\b",
    r"^where (is|was)\b",
]

# Model names per provider + complexity tier
MODELS = {
    "claude": {
        "simple":  "claude-haiku-4-5-20251001",
        "complex": "claude-sonnet-4-20250514",
    },
    "openai": {
        "simple":  "gpt-4o-mini",
        "complex": "gpt-4o",
    },
}

# Approximate cost multipliers (for logging)
COST_MULTIPLIER = {
    "simple": 1,
    "complex": 20,
}


def classify_complexity(topic: str) -> str:
    """
    Returns 'simple' or 'complex' based on heuristic signals in the topic.
    """
    topic_lower = topic.lower().strip()

    # Short topics with simple signals → cheap model
    if len(topic_lower.split()) <= 5:
        for pattern in SIMPLE_SIGNALS:
            if re.search(pattern, topic_lower):
                return "simple"

    # Complex signals → expensive model
    for pattern in COMPLEX_SIGNALS:
        if re.search(pattern, topic_lower):
            return "complex"

    # Default: use complex for anything ambiguous (accuracy > cost by default)
    return "complex"


def get_routed_model(topic: str, provider: str, force_tier: str = None) -> tuple[str, str]:
    """
    Returns (model_name, tier) for a given topic and provider.

    Args:
        topic: the research topic
        provider: 'claude' or 'openai'
        force_tier: override routing with 'simple' or 'complex'
    """
    tier = force_tier or classify_complexity(topic)
    provider_models = MODELS.get(provider, MODELS["claude"])
    model = provider_models.get(tier, provider_models["complex"])

    logger.info(
        f"[router] topic='{topic[:50]}' → tier={tier} model={model} "
        f"(~{COST_MULTIPLIER[tier]}x cost)"
    )
    return model, tier


def get_node_model(node_name: str, provider: str, topic_tier: str) -> str:
    """
    Per-node model selection:
    - plan / synthesize: use the routed model (needs good reasoning)
    - search / read: always use cheap model (simple extraction tasks)
    """
    if node_name in ("search", "read"):
        # These nodes do simple extraction — always use cheap model
        cheap_tier = "simple"
    else:
        cheap_tier = topic_tier

    return MODELS.get(provider, MODELS["claude"]).get(cheap_tier, MODELS["claude"]["complex"])
