"""
Token counter — tracks input/output tokens and estimates cost per request.

Pricing (as of mid-2025, per 1M tokens):
  Claude Sonnet:  input $3.00  / output $15.00
  GPT-4o:         input $5.00  / output $15.00
  Claude Haiku:   input $0.25  / output $1.25
"""

from dataclasses import dataclass, field
from typing import Literal

# ── Pricing table (per 1M tokens) ──────────────────────────────────────────
PRICING: dict[str, dict[str, float]] = {
    "claude": {"input": 3.00,  "output": 15.00},
    "openai": {"input": 5.00,  "output": 15.00},
    "haiku":  {"input": 0.25,  "output": 1.25},
}


@dataclass
class TokenUsage:
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0
    node_breakdown: dict[str, dict] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        p = PRICING.get(self.provider, PRICING["claude"])
        cost = (self.input_tokens / 1_000_000) * p["input"]
        cost += (self.output_tokens / 1_000_000) * p["output"]
        return round(cost, 6)

    def add(self, node: str, input_tokens: int, output_tokens: int):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.calls += 1
        if node not in self.node_breakdown:
            self.node_breakdown[node] = {"input": 0, "output": 0, "calls": 0}
        self.node_breakdown[node]["input"] += input_tokens
        self.node_breakdown[node]["output"] += output_tokens
        self.node_breakdown[node]["calls"] += 1

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "llm_calls": self.calls,
            "node_breakdown": self.node_breakdown,
        }


def count_tokens_from_response(response, provider: str) -> tuple[int, int]:
    """
    Extract input/output token counts from a LangChain response object.
    Returns (input_tokens, output_tokens).
    """
    usage = getattr(response, "usage_metadata", None) or getattr(response, "response_metadata", {})

    if hasattr(usage, "input_tokens"):
        # Anthropic style
        return usage.input_tokens, usage.output_tokens
    if isinstance(usage, dict):
        # OpenAI style via response_metadata
        token_usage = usage.get("token_usage", usage)
        inp = token_usage.get("prompt_tokens") or token_usage.get("input_tokens", 0)
        out = token_usage.get("completion_tokens") or token_usage.get("output_tokens", 0)
        return inp, out

    # Fallback: rough estimate via character count (~4 chars per token)
    content = getattr(response, "content", "")
    estimated = max(1, len(str(content)) // 4)
    return estimated * 3, estimated  # assume 3:1 input:output ratio
