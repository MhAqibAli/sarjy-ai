# Sarjy — Technical Design Document
*Read this first if you are an AI agent or engineer joining the project.*

## 1. Architecture

```
Browser (Next.js, Vercel)                      Backend (FastAPI, Render/Railway)
┌───────────────────────────┐                  ┌────────────────────────────────┐
│ Web Speech API (STT)      │  POST /api/chat  │ 1. load memories + history (DB)│
│  → text ─────────────────────────────────────▶ 2. Groq LLM (+ tool calling)   │
│                           │                  │    └─ get_weather → Open-Meteo │
│ <audio> plays base64 mp3 ◀───────────────────│ 3. ElevenLabs TTS (bytes)      │
│ Latency panel ← timings   │   JSON response  │ 4. respond {reply, audio, timings}
│ Memory panel  ← memories  │                  │ 5. BackgroundTask: extract facts│
└───────────────────────────┘                  └────────────────────────────────┘
                                                            │
                                                   SQLite (dev) / Postgres (prod)
```

One HTTP round-trip per turn. No WebSockets (Vercel-friendly, simple to debug).

## 2. Repository layout
```
backend/app/
  main.py     FastAPI app, routes, CORS, lifespan (creates tables)
  config.py   All env vars in one place
  schemas.py  Pydantic request/response models (= the API contract)
  db.py       SQLAlchemy models + tiny data-access functions
  llm.py      System prompt, Groq call, tool-calling loop, timing capture
  tools.py    Tool JSON schemas + async handlers (Open-Meteo)
  memory.py   Background fact extraction (fast model, JSON mode) → upsert
  tts.py      ElevenLabs streaming request, returns bytes + TTFB
frontend/
  app/page.tsx            The whole UI state machine (idle→listening→thinking→speaking)
  lib/api.ts              Typed fetch wrappers; NEXT_PUBLIC_API_URL
  lib/useSpeechRecognition.ts  Hook around webkitSpeechRecognition
  components/*            Orb (visual state), LatencyPanel, MemoryPanel
```

## 3. API contract

### `POST /api/chat`
Request:
```json
{ "user_id": "uuid-from-localStorage", "text": "what's the weather in Lahore" }
```
Response:
```json
{
  "reply": "Lahore is 31 degrees and sunny right now...",
  "audio_b64": "<base64 mp3 or null>",
  "audio_mime": "audio/mpeg",
  "tool_calls": ["get_weather"],
  "timings": {
    "llm_first_call_ms": 412.3, "tool_ms": 188.0, "llm_second_call_ms": 380.1,
    "llm_total_ms": 980.4, "tts_ttfb_ms": 131.2, "tts_total_ms": 610.5,
    "server_total_ms": 1604.2
  },
  "memories": { "name": "Ali", "home_city": "Karachi" }
}
```
`audio_b64 == null` → client falls back to `speechSynthesis`.

### `GET /api/memory/{user_id}` → `{ "memories": {key: value} }`
### `DELETE /api/memory/{user_id}` → `{ "deleted": true }`
### `GET /health` → `{ "ok": true }`

## 4. Data model
```
memories(id, user_id idx, key, value, updated_at)   UNIQUE(user_id, key)
messages(id, user_id idx, role, content, created_at)
```
Memory is **key/value**, not vector. Keys are snake_case (`favorite_color`, `home_city`).
Upsert = same key overwrites (so "actually my favorite color is red" just works).
History: last 8 messages are sent to the LLM for short-term context.

## 5. Identity
`user_id` is a UUID in `localStorage["sarjy_user_id"]`. Clearing site data = new user.
Good enough for the brief; swap for auth later without touching the backend.

## 6. LLM strategy
- Model: `llama-3.3-70b-versatile` (Groq) for conversation; `llama-3.1-8b-instant` for
  memory extraction (cheap, fast, JSON mode).
- System prompt injects: current date/time, memory block, persona rules, tool rules.
- Tool loop: call 1 with `tools` → if `tool_calls`, execute all, append `tool` messages,
  call 2 without tools → final reply. Max one tool round (keeps latency bounded).
- Hallucination guard: tool handlers return `{"error": ...}` on failure and the prompt
  forbids inventing data. Tool results are the only source of numbers.

### Adding a new tool (agent instructions)
1. In `tools.py`: write `async def my_tool(**kwargs) -> dict`, add its JSON schema to
   `TOOLS`, and register in `TOOL_HANDLERS`.
2. Add one line to the "Tools" section of the system prompt in `llm.py`.
That's it — the loop is generic.

## 7. Latency instrumentation
Server: `time.perf_counter()` around each stage → `timings`.
Client (`page.tsx`): `tSpeechEnd` (final transcript) → `tResponse` (fetch resolved)
→ `tFirstAudio` (`audio.onplaying`). Derived: `round_trip_ms`, `network_overhead_ms =
round_trip - server_total`, `time_to_first_audio_ms = tFirstAudio - tSpeechEnd`.
Typical budget: LLM 400–1000 ms · TTS 500–800 ms · network 100–300 ms.

## 8. Environment variables
Backend (`backend/.env`):
```
GROQ_API_KEY=            required
ELEVENLABS_API_KEY=      optional (no key → browser TTS fallback)
ELEVENLABS_VOICE_ID=     optional, default Rachel
DATABASE_URL=            optional; default sqlite:///./sarjy.db
                         prod: postgresql+psycopg://user:pass@host:5432/db
CORS_ORIGINS=            comma-separated, e.g. http://localhost:3000,https://sarjy.vercel.app
```
Frontend (`frontend/.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 9. Run locally
```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt && cp .env.example .env            # fill keys
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend && npm install && cp .env.local.example .env.local && npm run dev
```
Open http://localhost:3000 in Chrome or Edge (Web Speech API).

## 10. Deploy
- **Backend → Render or Railway** using `backend/Dockerfile`. Set env vars. For persistent
  memory, attach a Postgres instance and set `DATABASE_URL` (Render free disk is ephemeral).
- **Frontend → Vercel**: import repo, root dir `frontend`, set `NEXT_PUBLIC_API_URL` to the
  backend URL. Then add the Vercel URL to backend `CORS_ORIGINS` and redeploy backend.

## 11. Conventions for agents
- Backend: Python 3.12, type hints, async for I/O, no business logic in `main.py`.
- Frontend: TypeScript strict, Tailwind v4, no extra UI libraries, client components only
  where needed (`page.tsx`).
- Never log API keys. Never block the response on memory extraction.
- Keep spoken replies short — the prompt enforces it; don't raise `max_tokens` casually.

## 12. Known limitations
Browser STT is Chrome/Edge only (text input covers others). Single tool round per turn.
No streaming TTS yet (see PRD §4 for roadmap). SQLite is not for multi-instance prod.
