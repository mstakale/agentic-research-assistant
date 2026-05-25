import os
import json
import logging
from duckduckgo_search import ddg
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from agent.state import ResearchState
from utils.llm import get_llm
from utils.router import get_node_model, classify_complexity
from utils.token_counter import TokenUsage, count_tokens_from_response
from utils.budget import budget_guard

load_dotenv()
logger = logging.getLogger(__name__)


def _llm_invoke(state: ResearchState, node: str, messages: list) -> tuple:
    """
    Centralised LLM call with:
      - model routing (cheap vs expensive per node)
      - token counting
      - cost accumulation into state
    Returns (response_content, updated_token_fields)
    """
    provider = state["llm_provider"]
    tier = state.get("complexity_tier", "complex")

    model = get_node_model(node, provider, tier)
    llm = get_llm(provider=provider, model=model)

    logger.info(f"[{node}] calling {model}")
    response = llm.invoke(messages)

    inp, out = count_tokens_from_response(response, provider)

    # Return incremental cost to merge into state
    from utils.token_counter import PRICING
    p = PRICING.get(provider, PRICING["claude"])
    cost = (inp / 1_000_000) * p["input"] + (out / 1_000_000) * p["output"]

    return response.content, {
        "total_input_tokens": state.get("total_input_tokens", 0) + inp,
        "total_output_tokens": state.get("total_output_tokens", 0) + out,
        "estimated_cost_usd": round(state.get("estimated_cost_usd", 0.0) + cost, 6),
    }


# ── NODE 1: PLAN ──────────────────────────────────────────────────────────────

def plan_node(state: ResearchState) -> dict:
    """Break the research topic into focused sub-questions."""
    messages = [
        SystemMessage(content=(
            "You are a research planner. Given a topic, produce 4 focused sub-questions "
            "that together give a comprehensive understanding. "
            "Return ONLY a JSON array of strings. No explanation, no markdown."
        )),
        HumanMessage(content=f"Topic: {state['topic']}")
    ]

    content, cost_delta = _llm_invoke(state, "plan", messages)

    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    sub_questions = json.loads(raw.strip())

    return {
        "sub_questions": sub_questions,
        "steps": [{"type": "plan", "title": "Research Plan", "content": sub_questions}],
        **cost_delta,
    }


# ── NODE 2: SEARCH ────────────────────────────────────────────────────────────

def search_node(state: ResearchState) -> dict:
    """Run DuckDuckGo searches — free, no API key needed."""
    all_results = []
    step_content = []

    for question in state["sub_questions"]:
        try:
            hits = ddg(question, max_results=3) or []
            all_results.extend([
                {
                    "question": question,
                    "url":     r.get("href", ""),
                    "title":   r.get("title", ""),
                    "content": r.get("body", ""),
                }
                for r in hits
            ])
            step_content.append(f"[{question[:60]}] → {len(hits)} results")
        except Exception as e:
            step_content.append(f"[{question[:60]}] → error: {str(e)}")

    return {
        "search_results": all_results,
        "steps": [{"type": "search", "title": "Web Search (DuckDuckGo)", "content": step_content}],
    }


# ── NODE 3: READ & EXTRACT ────────────────────────────────────────────────────

def read_node(state: ResearchState) -> dict:
    """Extract key facts. Uses cheap model — simple extraction task."""
    extracted = []
    step_content = []
    cost_delta = {"total_input_tokens": 0, "total_output_tokens": 0, "estimated_cost_usd": 0.0}

    for result in state["search_results"]:
        if not result.get("content"):
            continue

        messages = [
            SystemMessage(content=(
                "Extract the 3 most important facts from the text relevant to the question. "
                "Return ONLY a JSON array of fact strings. Each fact must be one complete sentence."
            )),
            HumanMessage(content=(
                f"Question: {result['question']}\n\n"
                f"Source: {result['title']}\n\n"
                # cost control: truncate to 1000 chars instead of 2000
                f"Text:\n{result['content'][:1000]}"
            ))
        ]

        try:
            content, delta = _llm_invoke(state, "read", messages)
            raw = content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            facts = json.loads(raw.strip())
            extracted.append({
                "question": result["question"],
                "source_title": result["title"],
                "source_url": result["url"],
                "facts": facts,
            })
            step_content.append(f"✓ {result['title'][:60]}")
            # accumulate
            cost_delta["total_input_tokens"]  += delta["total_input_tokens"] - state.get("total_input_tokens", 0)
            cost_delta["total_output_tokens"] += delta["total_output_tokens"] - state.get("total_output_tokens", 0)
            cost_delta["estimated_cost_usd"]  += delta["estimated_cost_usd"] - state.get("estimated_cost_usd", 0.0)
        except Exception:
            step_content.append(f"✗ {result['title'][:60]}")

    return {
        "extracted_facts": extracted,
        "steps": [{"type": "read", "title": "Reading & Extracting", "content": step_content}],
        "total_input_tokens":  state.get("total_input_tokens", 0)  + cost_delta["total_input_tokens"],
        "total_output_tokens": state.get("total_output_tokens", 0) + cost_delta["total_output_tokens"],
        "estimated_cost_usd":  round(state.get("estimated_cost_usd", 0.0) + cost_delta["estimated_cost_usd"], 6),
    }


# ── NODE 4: SYNTHESIZE ────────────────────────────────────────────────────────

def synthesize_node(state: ResearchState) -> dict:
    """Synthesize all facts into a markdown report. Uses routed model."""
    facts_block = ""
    for item in state["extracted_facts"]:
        facts_block += f"\n### {item['question']}\nSource: [{item['source_title']}]({item['source_url']})\n"
        for fact in item["facts"]:
            facts_block += f"- {fact}\n"

    messages = [
        SystemMessage(content=(
            "You are a senior research analyst. Synthesize the research notes into a "
            "structured markdown report with: executive summary, key findings with headers, "
            "inline citations as [Title](url), a conclusion, and a sources list. "
            "Be concise — aim for 400-600 words."   # cost control: word limit
        )),
        HumanMessage(content=f"Topic: {state['topic']}\n\nNotes:\n{facts_block}")
    ]

    content, cost_delta = _llm_invoke(state, "synthesize", messages)

    # Record final cost to budget guard
    total_tokens = cost_delta["total_input_tokens"] + cost_delta["total_output_tokens"]
    total_cost   = cost_delta["estimated_cost_usd"]
    budget_guard.record(state.get("user_id", "anonymous"), total_tokens, total_cost)

    logger.info(
        f"[synthesize] query done | tokens={total_tokens} | "
        f"cost=${total_cost:.5f} | user={state.get('user_id')}"
    )

    return {
        "report": content,
        "steps": [{
            "type": "synthesize",
            "title": "Synthesizing Report",
            "content": [
                f"Report generated.",
                f"Total tokens: {total_tokens:,}",
                f"Estimated cost: ${total_cost:.5f}",
            ],
        }],
        **cost_delta,
    }


# ── ROUTING ───────────────────────────────────────────────────────────────────

def should_continue(state: ResearchState) -> str:
    iteration = state.get("iteration", 0) + 1
    max_iter  = state.get("max_iterations", 1)
    if iteration < max_iter and len(state.get("extracted_facts", [])) < 5:
        return "search"
    return "synthesize"
