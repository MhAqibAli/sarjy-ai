# Sarjy 🎙️
Voice assistant for the Sarj take-home. Talks, remembers you across sessions, checks live
weather. Deep dive: **latency** — every turn shows a time-to-first-audio waterfall.

**Stack:** Next.js 15 + Tailwind (Vercel) · FastAPI (Render/Railway) · Groq Llama 3.3 ·
ElevenLabs Flash v2.5 · Open-Meteo · SQLite/Postgres

## Docs
- [PRD](docs/PRD.md) — what and why, API justification, demo script
- [TDD](docs/TDD.md) — architecture, API contract, how to extend, deploy

## Quick start
```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env   # add GROQ_API_KEY
uvicorn app.main:app --reload --port 8000

cd ../frontend && npm install && cp .env.local.example .env.local && npm run dev
```
Open http://localhost:3000 in Chrome/Edge.

## Try
"My name is Ali, I live in Karachi, my favorite color is teal." → refresh →
"What's my favorite color?" → "What's the weather today?"
