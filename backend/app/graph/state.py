"""LangGraph state definition for the Travel Assistant agent."""

from __future__ import annotations
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class TravelState(TypedDict):
    """
    State schema carried through every node of the LangGraph agent.

    Fields
    ------
    messages : list
        Full conversation history (HumanMessage / AIMessage / ToolMessage).
        Uses the `add_messages` reducer so new messages are *appended*,
        not replaced.
    travel_context : dict
        Extracted travel preferences accumulated across the conversation.
        Keys: destination, origin, departure_date, return_date, adults,
              budget, interests, cabin_class
    flight_results : list[dict]
        Flight options returned by the search_flights tool.
    hotel_results : list[dict]
        Hotel options returned by the search_hotels tool.
    activity_results : list[dict]
        Activity suggestions returned by the search_activities tool.
    weather_data : dict
        Weather forecast for the destination.
    itinerary : dict | None
        The confirmed, final itinerary once the user approves everything.
    """

    messages: Annotated[list, add_messages]
    travel_context: dict
    flight_results: list[dict]
    hotel_results: list[dict]
    activity_results: list[dict]
    weather_data: dict
    itinerary: dict | None
