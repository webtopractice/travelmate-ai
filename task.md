# Task List — AI Travel Assistant

## Phase 1: Backend Setup
- [x] Initialize `uv` project with `pyproject.toml`
- [x] Install backend dependencies
- [x] Create `.env.example` and `config.py`

## Phase 2: LangGraph Agent
- [x] Create `state.py` — TravelState TypedDict
- [x] Create `nodes.py` — agent, tool_executor nodes (conversational confirmation instead of formal `interrupt()` — see note below)
- [x] Create `builder.py` — graph construction + compile with MemorySaver
- [x] Create `prompts/system.py` — travel agent system prompt

## Phase 3: Tools
- [x] `flights.py` — Kiwi.com MCP flight search
- [x] `hotels.py` — OpenTripMap hotel search (free)
- [x] `activities.py` — OpenTripMap activity search (free)
- [x] `weather.py` — OpenWeather API

## Phase 4: FastAPI Routes
- [x] `main.py` — FastAPI app with CORS, chat endpoint, SSE streaming, history endpoint

## Phase 5: Frontend Setup
- [x] Scaffold React + Vite project
- [x] Install frontend dependencies
- [x] Create `vercel.json`

## Phase 6: UI Components
- [x] `App.jsx` — main layout (dark theme, glassmorphism)
- [x] `ChatWindow.jsx` — chat with SSE streaming
- [x] `MessageBubble.jsx` — message rendering
- [x] `VoiceButton.jsx` — STT/TTS controls
- [ ] `FlightCard.jsx` — flight results display (currently rendered as formatted text in chat, not a dedicated card)
- [ ] `HotelCard.jsx` — hotel results display (currently rendered as formatted text in chat, not a dedicated card)
- [ ] `ConfirmationModal.jsx` — human-in-loop UI (currently handled via natural chat replies, no dedicated modal/interrupt)
- [ ] `ItineraryCard.jsx` — final plan display (currently text in chat, not a dedicated card)
- [x] `useChat.js` — chat hook with SSE
- [x] `useVoice.js` — voice hook (implemented; VoiceButton/ChatWindow currently use the Web Speech API directly rather than this hook)

## Phase 7: Polish & Deploy
- [x] README.md
- [x] Test end-to-end flow (verified: backend imports cleanly, starts, `/api/health` and `/api/chat` SSE stream work, `/api/history` works, frontend `npm run build` succeeds)
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel

## Blocking on the user
- [ ] Add a **real** `ANTHROPIC_API_KEY` to `backend/.env` — currently a placeholder, so all chat requests fail with `401 invalid x-api-key`. This is the only thing preventing the app from working end-to-end right now.
- [ ] (Optional) Add a real `OPENWEATHER_API_KEY` to `backend/.env` — without it, `get_weather` returns a friendly fallback message instead of real forecast data.
