from langgraph.graph import StateGraph, END

from agent.state import ResearchState
from agent.nodes import plan_node, search_node, read_node, synthesize_node, should_continue


def build_graph() -> StateGraph:
    """
    Build and compile the research agent graph.

    Flow:
        plan → search → read → [loop or synthesize] → END
    """
    graph = StateGraph(ResearchState)

    # Add nodes
    graph.add_node("plan", plan_node)
    graph.add_node("search", search_node)
    graph.add_node("read", read_node)
    graph.add_node("synthesize", synthesize_node)

    # Entry point
    graph.set_entry_point("plan")

    # Edges
    graph.add_edge("plan", "search")
    graph.add_edge("search", "read")

    # Conditional: loop back to search or move to synthesize
    graph.add_conditional_edges(
        "read",
        should_continue,
        {
            "search": "search",
            "synthesize": "synthesize",
        }
    )

    graph.add_edge("synthesize", END)

    return graph.compile()


# Singleton — compiled once at import
research_graph = build_graph()
