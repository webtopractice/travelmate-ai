"""LangGraph builder — assembles and compiles the travel agent graph."""

from __future__ import annotations

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import TravelState
from app.graph.nodes import (
    agent_node,
    tool_executor_node,
    should_continue,
)


def build_travel_graph():
    """
    Build and compile the Travel Assistant LangGraph.

    Flow:
        agent → (tool_executor → agent) loop
               ↘ __end__ (when agent responds with text)

    The graph uses MemorySaver for in-memory checkpointing,
    enabling conversation persistence across API calls within
    a thread_id.
    """
    # 1. Create the state graph
    builder = StateGraph(TravelState)

    # 2. Add nodes
    builder.add_node("agent", agent_node)
    builder.add_node("tool_executor", tool_executor_node)

    # 3. Set the entry point
    builder.set_entry_point("agent")

    # 4. Add conditional edges from agent
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tool_executor": "tool_executor",
            "__end__": END,
        },
    )

    # 5. After tool execution, always go back to agent
    #    (so it can process tool results and decide next step)
    builder.add_edge("tool_executor", "agent")

    # 6. Compile with MemorySaver checkpointer
    #    This enables conversation state to persist across requests
    #    within the same thread_id
    checkpointer = MemorySaver()

    graph = builder.compile(checkpointer=checkpointer)

    return graph


# Singleton graph instance — reused across all requests
travel_graph = build_travel_graph()
