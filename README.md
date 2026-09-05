# ✈️ TravelMate AI — AI-Powered Personal Travel Assistant

> **Hackathon Project** — A conversational AI travel assistant that plans complete trips (flights, hotels, activities, weather) using voice and text, powered by Claude + LangGraph.

## 🎯 Problem Statement

Planning a trip is **fragmented, overwhelming, and time-consuming**. Travelers juggle 5-8 different websites to compare flights, hotels, activities, and weather. There's no unified, intelligent interface that understands your preferences and plans everything in one place.

## 💡 What We're Trying to Achieve

**TravelMate AI** is a single conversational interface (text + voice) that acts like a personal travel agent:

- 🗣️ **Understands** natural language — no forms, no filters, just describe the trip you want
- ✈️ **Searches real, live data** — actual flights, hotels, activities, and weather, not canned examples
- ✅ **Confirms with you** at each step instead of silently deciding for you
- 📋 **Builds a complete itinerary** — flights → hotels → activities → weather, in one conversation

The goal for this hackathon was to prove the *whole loop* works end-to-end with real APIs and a real LLM agent — not a mockup. Every data source below has been tested live against its real backend, with real results, not sample data.

## ✅ Current State — What Actually Works

| Capability | Status |
|---|---|
| Conversational chat with streaming responses (SSE) | ✅ Working |
| Voice input (speech-to-text) and voice output (text-to-speech) | ✅ Working (browser-native) |
| Flight search (real prices, airlines, booking links) | ✅ Working — Kiwi.com MCP server |
| Hotel search (real properties, ratings, location) | ✅ Working — OpenStreetMap |
| Weather + short-range forecast | ✅ Working — OpenWeather |
| Activity/attraction search | ⚠️ Works most of the time — see [Known Limitations](#-known-limitations) |
| Rich result cards (flights/hotels) with a "select & confirm" modal | ✅ Working |
| Running trip summary in the sidebar | ✅ Working |
| Conversation memory within a session | ✅ Working (in-memory only — see limitations) |

## 🏗️ Architecture

```
┌─────────────────────┐     ┌──────────────────────────────────┐
│   React Frontend    │     │      FastAPI Backend              │
│   (Vite + Vercel)   │◄───►│      (Python + Render)           │
│                     │ SSE │                                  │
│  • Chat UI          │     │  ┌──────────────────────────┐    │
│  • Voice (STT/TTS)  │     │  │   LangGraph Agent        │    │
│  • Flight/Hotel     │     │  │                          │    │
│    Cards + Modal    │     │  │  Agent Node (Claude)     │    │
│  • Trip Summary     │     │  │      ↓ ↑                 │    │
│    Sidebar          │     │  │  Tool Executor Node      │    │
│                     │     │  │      ↓                   │    │
│                     │     │  │  [Tools]                 │    │
│                     │     │  │  • search_flights        │    │
│                     │     │  │  • search_hotels         │    │
│                     │     │  │  • search_activities     │    │
│                     │     │  │  • get_weather           │    │
│                     │     │  │                          │    │
│                     │     │  │  MemorySaver (state)     │    │
│                     │     │  └──────────────────────────┘    │
└─────────────────────┘     └──────────────────────────────────┘
                                         ↓
                            ┌─────────────────────────┐
                            │    External APIs         │
                            │  • Kiwi.com MCP (flights)│
                            │  • OSM Overpass (hotels/  │
                            │    activities, via        │
                            │    OpenWeather geocoding) │
                            │  • OpenWeather (weather)  │
                            └─────────────────────────┘
```

Human-in-the-loop confirmation is handled conversationally (the agent asks, you reply in chat) plus a lightweight approve/cancel modal in the UI when you pick a specific flight or hotel card — rather than a formal LangGraph `interrupt()`/resume flow. This was a deliberate simplification: it's simpler to get right with SSE streaming and just as effective for a demo.

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | Claude (Anthropic, `claude-sonnet-5`) | Core reasoning & natural language understanding |
| **Agent Framework** | LangGraph + LangChain | Stateful agentic workflow with tool calling |
| **Backend** | FastAPI + Uvicorn | Async Python API server with SSE streaming |
| **Frontend** | React + Vite | Chat UI with glassmorphism dark theme |
| **Voice (STT/TTS)** | Web Speech API | Browser-native, free, zero-config |
| **Flights** | [Kiwi.com MCP server](https://mcp.kiwi.com/) | Real flight search via the MCP protocol — free, no key |
| **Hotels & Activities** | OpenStreetMap (Overpass API) + OpenWeather (geocoding) | Free, keyless POI data |
| **Weather** | OpenWeather API | Free tier, current + short forecast |
| **State** | LangGraph `MemorySaver` | In-memory conversation checkpointing (per process) |
| **Deployment (FE)** | Vercel | Free hosting for the Vite static build |
| **Deployment (BE)** | Render | Free hosting for the persistent FastAPI process |

## 📁 Project Structure

```
├── backend/                    # Python FastAPI + LangGraph
│   ├── app/
│   │   ├── main.py             # FastAPI app, CORS, SSE chat endpoint
│   │   ├── config.py           # Settings (API keys from .env)
│   │   ├── graph/
│   │   │   ├── state.py        # TravelState TypedDict
│   │   │   ├── nodes.py        # Agent, tool_executor, routing logic
│   │   │   └── builder.py      # Graph construction + compile
│   │   ├── tools/
│   │   │   ├── flights.py      # Kiwi.com MCP flight search
│   │   │   ├── hotels.py       # OSM Overpass hotel search
│   │   │   ├── activities.py   # OSM Overpass activity search
│   │   │   ├── weather.py      # OpenWeather API
│   │   │   └── osm.py          # Shared geocoding + Overpass helpers
│   │   └── prompts/
│   │       └── system.py       # Travel agent system prompt
│   ├── pyproject.toml / uv.lock / requirements.txt
│   └── .env                    # API keys (not committed)
│
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── App.jsx             # Main layout (sidebar + chat)
│   │   ├── index.css           # Dark glassmorphism theme
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── VoiceButton.jsx
│   │   │   ├── FlightCard.jsx      # Selectable flight results
│   │   │   ├── HotelCard.jsx       # Selectable hotel results
│   │   │   ├── ConfirmationModal.jsx # Approve/cancel a pick
│   │   │   └── ItineraryCard.jsx   # Running trip summary (sidebar)
│   │   ├── hooks/
│   │   │   ├── useChat.js      # Chat state + SSE + trip summary
│   │   │   └── useVoice.js     # STT/TTS hook
│   │   └── utils/
│   │       ├── api.js          # Fetch + SSE streaming
│   │       └── textFormat.jsx  # Shared markdown-ish text renderer
│   └── package.json
│
├── .gitignore
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) package manager
- An [Anthropic API key](https://console.anthropic.com/) with access to a Claude model
- An [OpenWeather API key](https://openweathermap.org/api) (free tier) — used for weather **and** for resolving city names to coordinates for hotel/activity search

No key is needed for flights (Kiwi MCP) or for hotel/activity POI data (OpenStreetMap Overpass).

### 1. Backend

```bash
cd backend
uv sync

cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY and OPENWEATHER_API_KEY

uv run uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Open the app

Visit **http://localhost:5173** and start planning your trip.

## 🎮 Demo Flow

1. *"Plan a 5-day trip to Goa from Delhi for 2 people"*
2. Agent extracts preferences → searches real flights via Kiwi.com
3. Flight options render as cards → pick one → confirm in the modal
4. Agent searches real hotels near the destination → pick one → confirm
5. Agent checks weather and suggests activities
6. Sidebar builds a running trip summary as you go

## ⚠️ Known Limitations

- **Activity search occasionally times out.** It uses the free, public OpenStreetMap Overpass API, which has no guaranteed uptime/rate limits. When it times out, the tool fails gracefully — no crash, no broken UI — the agent just apologizes and offers general suggestions instead. Hotels use the same infrastructure but have not shown the same flakiness in testing.
- **Conversation memory is in-memory only** (`MemorySaver`). Restarting the backend (or Render's free-tier process spin-down after 15 min idle) wipes all active conversations. Fine for a demo, not for production.
- **No formal human-in-the-loop interrupt/resume.** Confirmation is conversational + a UI modal, not a paused/resumed LangGraph state. Simpler and more robust for a demo, but means the backend can't "wait indefinitely" for a decision the way a true interrupt-based flow could.
- **Flight prices are real but city-name flight search can surface odd routings** (e.g. sorting by price alone can surface long-layover itineraries) — this is the real Kiwi.com fare data, not a bug, but worth knowing when demoing.

## 🌐 Deployment

### Backend → Render
1. Push this repo to GitHub.
2. New Web Service on [Render](https://render.com) → connect the repo → **Root Directory: `backend`**.
3. Render should pick up `render.yaml` (`pip install -r requirements.txt`, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
4. Set environment variables: `ANTHROPIC_API_KEY`, `OPENWEATHER_API_KEY`.

### Frontend → Vercel
1. New Project on [Vercel](https://vercel.com) → connect the repo → **Root Directory: `frontend`**.
2. Build command `npm run build`, output directory `dist` (Vercel usually auto-detects this for Vite).
3. Set environment variable `VITE_API_URL` to your Render backend's public URL.

## 📜 Key Design Decisions

1. **LangGraph over Rasa** — Claude + LangChain gives far better NLU than training a Rasa pipeline, with far less setup.
2. **Web Speech API over external STT/TTS** — free, zero-config, runs entirely in the browser.
3. **OpenStreetMap over OpenTripMap** — OpenTripMap now requires an API key on every call (including geocoding); OSM's Overpass API needed none, so we switched.
4. **OpenWeather for geocoding, not a dedicated geocoder** — Nominatim and Photon (the usual free options) both blocked requests from our environment during testing, and OpenWeather's own city resolution (which we already needed for weather) turned out to disambiguate regional names like "Goa" *better* than either.
5. **Kiwi.com MCP over Amadeus** — Amadeus's Self-Service API was shut down; Kiwi's MCP server is free and, once implemented against its real (undocumented-outside-the-server) schema, returns real fares and booking links.
6. **SSE over WebSocket** — simpler, one-directional streaming is enough for chat, and plays nicely with Render's free tier.
7. **Conversational confirmation over LangGraph `interrupt()`** — a formal pause/resume flow adds real complexity when combined with SSE streaming; asking in chat + a simple approve/cancel modal gets the same human-in-the-loop effect with much less risk of getting the plumbing wrong.

## 🔭 What's Next

Roughly in priority order:

- **Persistent checkpointing** — swap `MemorySaver` for a real `PostgresSaver`/`SqliteSaver` so conversations survive a backend restart.
- **Resilience for activity search** — retry-with-backoff or a second free POI provider as a fallback when Overpass times out.
- **Richer itinerary output** — a real "build_itinerary" step that compiles confirmed flights/hotels/activities/weather into a single exportable day-by-day plan (PDF/shareable link), not just a live sidebar summary.
- **Multi-currency awareness** — infer currency from the conversation instead of the agent guessing per call.
- **Automated tests** — there are currently none; at minimum, unit tests for the tools' parsing logic and an integration test for the chat endpoint.
- **Formal human-in-the-loop** — revisit a true LangGraph `interrupt()`/`Command(resume=...)` flow if we need the agent to genuinely block (e.g. for a real booking step) rather than just "ask and continue."
- **Dockerize** — a Dockerfile for the backend would make deployment less Render-specific.
- **Booking follow-through** — right now "confirming" a flight/hotel is conversational only; an actual booking handoff (e.g. deep-linking to Kiwi's `bookingUrl`) is not yet wired into the UI beyond showing the link in text.

## 📄 License

Built for the **Travel Tech Hackathon** 🏆
