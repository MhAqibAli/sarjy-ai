"""FastAPI entrypoint. Routes only — logic lives in llm/tools/memory/tts/db."""
import base64
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .config import CORS_ORIGINS, GROQ_API_KEY
from .llm import run_llm
from .memory import extract_and_store
from .schemas import ChatRequest, ChatResponse, MemoryResponse, Timings
from .tts import synthesize


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Sarjy API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, background: BackgroundTasks):
    if not GROQ_API_KEY:
        raise HTTPException(500, "GROQ_API_KEY is not configured")

    t0 = perf_counter()
    memories = db.get_memories(req.user_id)
    history = db.get_recent_messages(req.user_id, limit=8)

    try:
        reply, used_tools, timings = await run_llm(req.text, memories, history)
    except Exception as exc:
        raise HTTPException(502, f"LLM error: {exc}") from exc

    audio, ttfb, tts_total = await synthesize(reply)
    timings["tts_ttfb_ms"] = ttfb
    timings["tts_total_ms"] = tts_total
    timings["server_total_ms"] = (perf_counter() - t0) * 1000

    db.add_message(req.user_id, "user", req.text)
    db.add_message(req.user_id, "assistant", reply)
    background.add_task(extract_and_store, req.user_id, req.text, reply, memories)

    return ChatResponse(
        reply=reply,
        audio_b64=base64.b64encode(audio).decode() if audio else None,
        tool_calls=used_tools,
        timings=Timings(**timings),
        memories=memories,
    )


@app.get("/api/memory/{user_id}", response_model=MemoryResponse)
async def get_memory(user_id: str):
    return MemoryResponse(memories=db.get_memories(user_id))


@app.delete("/api/memory/{user_id}")
async def clear_memory(user_id: str):
    db.delete_memories(user_id)
    return {"deleted": True}
