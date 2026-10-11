# Sarjy — Product Requirements Document

## 1. Purpose
Sarjy is a voice-first personal assistant built as a take-home for Sarj. A user talks to it,
it answers out loud, remembers personal facts across sessions, and can fetch live weather.
The deep-dive focus is **latency**: minimizing and transparently measuring time-to-first-audio.

## 2. Target user & persona
- **User:** Anyone opening the deployed URL in Chrome/Edge with a mic. No login.
- **Sarjy's persona:** Warm, quick-witted, concise. A spoken assistant, so replies are 1–3
  sentences, no markdown, no lists, no emojis. Mirrors the user's language (English, Urdu,
  Roman Urdu). A light Clippy-style self-awareness ("It looks like you're...") is welcome.

## 3. Core requirements (all mandatory)

| # | Requirement | Acceptance criteria |
|---|---|---|
| R1 | Voice in / voice out | User presses mic, speaks, Sarjy replies with synthesized speech. Text input exists as fallback. |
| R2 | Cross-session memory | User says "my favorite color is teal", closes the tab, reopens tomorrow, asks "what's my favorite color?" → Sarjy answers "teal". |
| R3 | External API | Sarjy answers "what's the weather in Karachi?" with live data. If user has a remembered location, "what's the weather?" works with no city named. |
| R4 | Deployed | Public HTTPS URL. Reviewer opens it, clicks mic, talks. No setup. |
| R5 | Honest tool use | If weather lookup fails, Sarjy says so. It never invents temperatures. |

### API justification (required by brief)
We chose **Open-Meteo** (weather + geocoding). Weather is the most natural *spoken* query
("Do I need an umbrella?") and pairs with memory: once Sarjy knows where you live, you never
have to say the city again. Open-Meteo needs no API key, has no rate-limit friction for a
reviewer, and returns clean JSON — so the deployment has one fewer secret that can break.

## 4. Deep dive: Latency
**Goal:** Time-to-first-audio (TTFA) under ~1.5s on a normal connection; show exactly where
every millisecond goes.

**Delivered:**
- Server returns a `timings` object per request: LLM first call, tool execution, LLM second
  call (if tool used), TTS time-to-first-byte, TTS total, server total.
- Client adds: network overhead, round trip, and true TTFA (speech end → audio playing).
- A live Latency panel in the UI shows the last turn's waterfall.
- Memory extraction runs **after** the response is sent (background task) so it costs 0 ms
  of user-facing latency.
- Fastest-in-class components: Groq (LLM), ElevenLabs Flash v2.5 (TTS, ~75–150 ms TTFB).

**What we'd do with another week:** sentence-level TTS streaming (speak sentence 1 while the
LLM writes sentence 2), server-side streaming STT (Deepgram) instead of browser STT,
persistent WebSocket to drop per-request connection setup, speculative TTS of filler ("Let me
check...") while a tool runs, and a region-pinned deployment close to the reviewer.

## 5. Out of scope (deliberately)
Authentication, multi-user rooms, avatars, telephony, vector memory search, conversation
history UI beyond the current session.

## 6. Success metrics
- All R1–R5 pass in a live reviewer session.
- Median TTFA (ElevenLabs path) ≤ 1.5 s; panel visible and explainable.
- Reviewer can read any file and the author can explain it.

## 7. Demo script (3 minutes)
1. "Hi Sarjy, my name is Ali and I live in Karachi. My favorite color is teal."
2. Refresh the page. "What's my favorite color?" → teal.  (R2)
3. "What's the weather like today?" → uses remembered Karachi. (R3 + memory)
4. Point at Latency panel: explain the waterfall. (Deep dive)
5. "What's the weather on Mars?" → honest failure, no invented numbers. (R5)
