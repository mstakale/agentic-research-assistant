import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

load_dotenv()

# Default models (overridden by router when cost management is active)
DEFAULT_MODELS = {
    "claude": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
}


def get_llm(provider: str = "claude", streaming: bool = False, model: str = None):
    """
    Factory that returns the chosen LLM.

    Args:
        provider: "claude" or "openai"
        streaming: whether to enable token streaming
        model: specific model name (overrides default — used by router)

    Returns:
        LangChain chat model instance
    """
    if provider == "claude":
        return ChatAnthropic(
            model=model or DEFAULT_MODELS["claude"],
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=streaming,
            max_tokens=2048,  # reduced from 4096 — saves output tokens
        )
    elif provider == "openai":
        return ChatOpenAI(
            model=model or DEFAULT_MODELS["openai"],
            api_key=os.getenv("OPENAI_API_KEY"),
            streaming=streaming,
            max_tokens=2048,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'claude' or 'openai'.")
