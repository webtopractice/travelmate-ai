"""FastAPI application — chat endpoint with SSE streaming for the travel agent."""

from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage, AIMessage

from app.config import get_settings
from app.graph.builder import travel_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print("[OK] TravelMate AI backend starting...")
    yield
    print("[OK] TravelMate AI backend shutting down.")


app = FastAPI(
    title="TravelMate AI",
    description="AI-Powered Personal Travel Assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend origins
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS + ["*"],  # permissive for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "TravelMate AI"}


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    Main chat endpoint — accepts a user message, runs the LangGraph agent,
    and streams the response via Server-Sent Events (SSE).

    Request body:
        {
            "message": "Plan a trip to Goa",
            "thread_id": "optional-uuid"  // omit for new conversation
        }

    SSE Events:
        - type: "token"     → streaming text chunk
        - type: "tool_call" → agent is calling a tool
        - type: "tool_result" → tool execution result
        - type: "done"      → stream complete
        - type: "error"     → error occurred
    """
    body = await request.json()
    user_message = body.get("message", "").strip()
    thread_id = body.get("thread_id", str(uuid.uuid4()))

    if not user_message:
        return JSONResponse(
            status_code=400,
            content={"error": "Message is required"},
        )

    async def event_generator():
        """Generate SSE events from the LangGraph agent stream."""
        try:
            # Send the thread_id first so frontend can track it
            yield {
                "event": "thread_id",
                "data": json.dumps({"thread_id": thread_id}),
            }

            # Prepare the input
            input_data = {
                "messages": [HumanMessage(content=user_message)],
            }

            config = {"configurable": {"thread_id": thread_id}}

            # Stream events from the graph
            full_response = ""

            async for event in travel_graph.astream_events(
                input_data, config=config, version="v2"
            ):
                event_type = event.get("event", "")
                event_name = event.get("name", "")

                # LLM streaming tokens
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", None)
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        # Handle string content
                        if isinstance(chunk.content, str):
                            full_response += chunk.content
                            yield {
                                "event": "token",
                                "data": json.dumps({"content": chunk.content}),
                            }
                        # Handle list content (tool use blocks etc.)
                        elif isinstance(chunk.content, list):
                            for block in chunk.content:
                                if isinstance(block, dict):
                                    if block.get("type") == "text" and block.get("text"):
                                        full_response += block["text"]
                                        yield {
                                            "event": "token",
                                            "data": json.dumps(
                                                {"content": block["text"]}
                                            ),
                                        }

                # Tool calls
                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    yield {
                        "event": "tool_call",
                        "data": json.dumps(
                            {
                                "tool": tool_name,
                                "input": tool_input,
                                "status": "started",
                            }
                        ),
                    }

                # Tool results
                elif event_type == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    output = event.get("data", {}).get("output", "")
                    output_str = str(output)

                    # Tools may return a structured JSON envelope
                    # ({"type", "summary", "items"/"current"/"forecast"}) so the
                    # frontend can render rich cards. Fall back to plain text
                    # for tools/errors that don't (never breaks the stream).
                    structured = None
                    try:
                        candidate = json.loads(output_str)
                        if isinstance(candidate, dict) and "type" in candidate:
                            structured = candidate
                    except (json.JSONDecodeError, TypeError):
                        structured = None

                    result_text = structured["summary"] if structured else output_str

                    payload = {
                        "tool": tool_name,
                        "result": result_text[:2000],  # Truncate for SSE
                        "status": "completed",
                    }
                    if structured is not None:
                        payload["data"] = structured

                    yield {
                        "event": "tool_result",
                        "data": json.dumps(payload),
                    }

            # Stream complete
            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "full_response": full_response,
                        "thread_id": thread_id,
                    }
                ),
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())


@app.get("/api/history/{thread_id}")
async def get_history(thread_id: str):
    """
    Get conversation history for a thread.

    Returns the last N messages from the checkpointed state.
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = await travel_graph.aget_state(config)

        if not state or not state.values:
            return {"messages": [], "thread_id": thread_id}

        messages = state.values.get("messages", [])

        # Serialize messages for the frontend
        serialized = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                serialized.append(
                    {"role": "user", "content": msg.content}
                )
            elif isinstance(msg, AIMessage):
                # Only include text content, not tool calls
                content = msg.content
                if isinstance(content, list):
                    text_parts = [
                        b.get("text", "")
                        for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                    ]
                    content = "".join(text_parts)
                if content:
                    serialized.append(
                        {"role": "assistant", "content": content}
                    )

        return {"messages": serialized, "thread_id": thread_id}

    except Exception as e:
        return {"messages": [], "thread_id": thread_id, "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
