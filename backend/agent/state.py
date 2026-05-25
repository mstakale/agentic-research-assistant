from typing import Annotated, TypedDict
import operator


class ResearchState(TypedDict):
    """State that flows through the LangGraph agent."""

    # Input
    topic: str
    llm_provider: str  # "claude" | "openai"
    user_id: str       # for budget tracking

    # Routing
    complexity_tier: str   # "simple" | "complex"

    # Planning
    sub_questions: list[str]

    # Search & reading
    search_results: Annotated[list[dict], operator.add]
    extracted_facts: Annotated[list[dict], operator.add]

    # Output
    report: str

    # Cost tracking — accumulated across all nodes
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float

    # Control
    steps: Annotated[list[dict], operator.add]
    iteration: int
    max_iterations: int
