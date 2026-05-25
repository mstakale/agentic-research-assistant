import json
import asyncio
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agent.graph import research_graph
from agent.state import ResearchState
from utils.cache import research_cache
from utils.budget import budget_guard, BudgetExceededError
from utils.router import classify_complexity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic Research Assistant API",
    description="Autonomous research agent — with cost management",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── SCHEMAS ───────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    topic: str
    llm_provider: str = "claude"
    max_iterations: int = 1
    user_id: str = "anonymous"


# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "cache": research_cache.is_available,
        "budget_guard": budget_guard._r is not None,
    }


# ── USAGE / BUDGET STATUS ─────────────────────────────────────────────────────

@app.get("/usage/{user_id}")
def get_usage(user_id: str):
    """Return today's token and cost usage for a user."""
    return budget_guard.get_usage(user_id)

@app.get("/usage/global/summary")
def get_global_usage():
    """Return global daily usage stats (admin use)."""
    return budget_guard.get_global_usage()


# ── STREAMING RESEARCH ENDPOINT ───────────────────────────────────────────────

@app.post("/research/stream")
async def research_stream(request: ResearchRequest):
    """
    Stream agent progress as SSE events.
    Checks cache first, budget guard second, then runs the agent.
    """
    topic = request.topic.strip()
    if not topic:
        raise HTTPException(status_code=422, detail="Topic cannot be empty")
    if request.llm_provider not in ("claude", "openai"):
        raise HTTPException(status_code=422, detail="llm_provider must be 'claude' or 'openai'")

    async def generate() -> AsyncGenerator[dict, None]:

        # ── 1. Budget pre-flight check ─────────────────────────────────────
        try:
            budget_guard.check(request.user_id, topic)
        except BudgetExceededError as e:
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "error",
                    "data": {"message": e.reason, "limit_type": e.limit_type}
                })
            }
            return

        # ── 2. Cache check ─────────────────────────────────────────────────
        cached = research_cache.get(topic, request.llm_provider)
        if cached:
            cache_type = cached.get("cache_hit", "exact")
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "step",
                    "node": "cache",
                    "data": {
                        "type": "plan",
                        "title": f"Cache hit ({cache_type})",
                        "content": ["Returning cached result — $0.00 cost"],
                    }
                })
            }
            yield {
                "event": "message",
                "data": json.dumps({"type": "report", "data": {"report": cached["report"]}})
            }
            yield {
                "event": "message",
                "data": json.dumps({"type": "cost", "data": {
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                    "cache_hit": cache_type,
                }})
            }
            yield {"event": "message", "data": json.dumps({"type": "done", "data": {}})}
            return

        # ── 3. Route model complexity ──────────────────────────────────────
        complexity = classify_complexity(topic)

        # ── 4. Run the agent ───────────────────────────────────────────────
        initial_state: ResearchState = {
            "topic": topic,
            "llm_provider": request.llm_provider,
            "user_id": request.user_id,
            "complexity_tier": complexity,
            "sub_questions": [],
            "search_results": [],
            "extracted_facts": [],
            "report": "",
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "steps": [],
            "iteration": 0,
            "max_iterations": min(request.max_iterations, 2),  # hard cap
        }

        try:
            final_state = None
            async for event in research_graph.astream(initial_state):
                for node_name, node_output in event.items():
                    for step in node_output.get("steps", []):
                        yield {
                            "event": "message",
                            "data": json.dumps({"type": "step", "node": node_name, "data": step})
                        }
                        await asyncio.sleep(0)

                    if node_output.get("report"):
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "type": "report",
                                "data": {"report": node_output["report"]}
                            })
                        }
                    final_state = node_output

            # ── 5. Emit cost summary ───────────────────────────────────────
            if final_state:
                cost_summary = {
                    "total_tokens": (
                        final_state.get("total_input_tokens", 0) +
                        final_state.get("total_output_tokens", 0)
                    ),
                    "input_tokens":  final_state.get("total_input_tokens", 0),
                    "output_tokens": final_state.get("total_output_tokens", 0),
                    "estimated_cost_usd": final_state.get("estimated_cost_usd", 0.0),
                    "complexity_tier": complexity,
                    "cache_hit": None,
                }
                yield {
                    "event": "message",
                    "data": json.dumps({"type": "cost", "data": cost_summary})
                }

                # ── 6. Store in cache ──────────────────────────────────────
                if final_state.get("report"):
                    research_cache.set(topic, request.llm_provider, {
                        "report": final_state["report"],
                        "sub_questions": final_state.get("sub_questions", []),
                    })

            yield {"event": "message", "data": json.dumps({"type": "done", "data": {}})}

        except BudgetExceededError as e:
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "error",
                    "data": {"message": e.reason, "limit_type": e.limit_type}
                })
            }
        except Exception as e:
            logger.exception("Agent error")
            yield {
                "event": "message",
                "data": json.dumps({"type": "error", "data": {"message": str(e)}})
            }

    return EventSourceResponse(generate())


# ── BLOCKING ENDPOINT (testing) ───────────────────────────────────────────────

@app.post("/research")
async def research(request: ResearchRequest):
    topic = request.topic.strip()
    try:
        budget_guard.check(request.user_id, topic)
    except BudgetExceededError as e:
        raise HTTPException(status_code=429, detail=e.reason)

    cached = research_cache.get(topic, request.llm_provider)
    if cached:
        return {**cached, "cache_hit": True, "cost_usd": 0.0}

    complexity = classify_complexity(topic)
    initial_state: ResearchState = {
        "topic": topic,
        "llm_provider": request.llm_provider,
        "user_id": request.user_id,
        "complexity_tier": complexity,
        "sub_questions": [],
        "search_results": [],
        "extracted_facts": [],
        "report": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "steps": [],
        "iteration": 0,
        "max_iterations": 1,
    }
    final = await research_graph.ainvoke(initial_state)
    research_cache.set(topic, request.llm_provider, {"report": final["report"]})
    return {
        "topic": topic,
        "report": final["report"],
        "cost_usd": final.get("estimated_cost_usd", 0),
        "total_tokens": final.get("total_input_tokens", 0) + final.get("total_output_tokens", 0),
        "complexity_tier": complexity,
        "cache_hit": False,
    }
