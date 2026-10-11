"""Pydantic models = the public API contract. Keep in sync with frontend/lib/api.ts."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=8, max_length=64)
    text: str = Field(min_length=1, max_length=2000)


class Timings(BaseModel):
    llm_first_call_ms: float = 0
    tool_ms: float = 0
    llm_second_call_ms: float = 0
    llm_total_ms: float = 0
    tts_ttfb_ms: float = 0
    tts_total_ms: float = 0
    server_total_ms: float = 0


class ChatResponse(BaseModel):
    reply: str
    audio_b64: str | None = None
    audio_mime: str = "audio/mpeg"
    tool_calls: list[str] = []
    timings: Timings
    memories: dict[str, str] = {}


class MemoryResponse(BaseModel):
    memories: dict[str, str]
