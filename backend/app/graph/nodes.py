"""LangGraph nodes — agent reasoning, tool execution, human confirmation."""

from __future__ import annotations

import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.types import interrupt

from app.config import get_settings
from app.graph.state import TravelState
from app.prompts.system import TRAVEL_AGENT_SYSTEM_PROMPT
from app.tools.flights import search_flights
from app.tools.hotels import search_hotels
from app.tools.activities import search_activities
from app.tools.weather import get_weather

# All available tools for the agent
ALL_TOOLS = [search_flights, search_hotels, search_activities, get_weather]


def _get_llm():
    """Create the Claude LLM instance with tools bound."""
    settings = get_settings()
    llm = ChatAnthropic(
        model="claude-sonnet-5",
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=4096,
    )
    return llm.bind_tools(ALL_TOOLS)


async def agent_node(state: TravelState) -> dict:
    """
    Core agent node — invokes Claude with conversation history and tools.

    The LLM will either:
    1. Respond with text (end of turn → goes to user)
    2. Request tool calls (→ routes to tool_executor)
    3. Ask for confirmation (embedded in text → routes to human_confirmation)
    """
    llm = _get_llm()

    # Prepend the system prompt to the messages
    messages = [SystemMessage(content=TRAVEL_AGENT_SYSTEM_PROMPT)] + state["messages"]

    response = await llm.ainvoke(messages)

    return {"messages": [response]}


async def tool_executor_node(state: TravelState) -> dict:
    """
    Executes tool calls requested by the agent.

    Reads the last AIMessage's tool_calls, runs each tool,
    and returns ToolMessages with results.
    """
    last_message = state["messages"][-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    tool_map = {t.name: t for t in ALL_TOOLS}
    tool_messages = []
    state_update: dict = {}

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name in tool_map:
            try:
                result = await tool_map[tool_name].ainvoke(tool_args)
            except Exception as e:
                result = f"Tool error ({tool_name}): {str(e)}"
        else:
            result = f"Unknown tool: {tool_name}"

        result_str = str(result)

        # Tools that return a structured JSON envelope ({"type", "summary", ...})
        # still hand the LLM just the human-readable "summary" text, so the
        # agent's conversational behavior is unchanged either way.
        parsed = None
        try:
            candidate = json.loads(result_str)
            if isinstance(candidate, dict) and "summary" in candidate:
                parsed = candidate
        except (json.JSONDecodeError, TypeError):
            parsed = None

        display_text = parsed["summary"] if parsed else result_str

        tool_messages.append(
            ToolMessage(
                content=display_text,
                tool_call_id=tool_call["id"],
                name=tool_name,
            )
        )

        # Also store results in state for the frontend
        if tool_name == "search_flights":
            state_update["flight_results"] = (parsed or {}).get("items") or [{"raw": result_str}]
        elif tool_name == "search_hotels":
            state_update["hotel_results"] = (parsed or {}).get("items") or [{"raw": result_str}]
        elif tool_name == "search_activities":
            state_update["activity_results"] = (parsed or {}).get("items") or [{"raw": result_str}]
        elif tool_name == "get_weather":
            if parsed:
                state_update["weather_data"] = {
                    "current": parsed.get("current"),
                    "forecast": parsed.get("forecast"),
                }
            else:
                state_update["weather_data"] = {"raw": result_str}

    return {"messages": tool_messages, **state_update}


async def human_confirmation_node(state: TravelState) -> dict:
    """
    Human-in-the-loop node — pauses the graph and waits for user input.

    Uses LangGraph's interrupt() to pause execution. The frontend shows
    the agent's message and waits for the user to respond. The graph
    resumes when Command(resume=...) is called.
    """
    # The interrupt value is sent to the frontend as context
    # The user's response comes back via Command(resume=user_input)
    user_response = interrupt(
        {
            "type": "confirmation",
            "message": "Waiting for your confirmation or feedback...",
        }
    )

    # The user's response is injected here when the graph resumes
    from langchain_core.messages import HumanMessage

    return {"messages": [HumanMessage(content=user_response)]}


def should_continue(state: TravelState) -> str:
    """
    Routing function — determines next node after the agent.

    Returns:
        'tool_executor' — if the LLM wants to call tools
        'human_confirmation' — if we should pause for user input
        '__end__' — if the agent is done (no tool calls, just text)
    """
    last_message = state["messages"][-1]

    # If the LLM made tool calls, execute them
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool_executor"

    # Otherwise, the agent responded with text — end this turn
    # (the response goes back to the user, who can send a new message)
    return "__end__"
