"""ElevenLabs streaming TTS. Returns (audio_bytes | None, ttfb_ms, total_ms)."""
from time import perf_counter

import httpx

from .config import ELEVENLABS_API_KEY, ELEVENLABS_MODEL, ELEVENLABS_VOICE_ID


async def synthesize(text: str) -> tuple[bytes | None, float, float]:
    if not ELEVENLABS_API_KEY or not text:
        return None, 0.0, 0.0

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    body = {
        "text": text,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    t0 = perf_counter()
    ttfb: float | None = None
    chunks: list[bytes] = []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            async with client.stream(
                "POST", url, headers=headers, json=body,
                params={"output_format": "mp3_22050_32", "optimize_streaming_latency": 3},
            ) as r:
                if r.status_code != 200:
                    print(f"[tts] ElevenLabs {r.status_code}")
                    return None, 0.0, 0.0
                async for chunk in r.aiter_bytes():
                    if ttfb is None:
                        ttfb = (perf_counter() - t0) * 1000
                    chunks.append(chunk)
    except Exception as exc:
        print(f"[tts] failed: {exc}")
        return None, 0.0, 0.0

    total = (perf_counter() - t0) * 1000
    return b"".join(chunks), ttfb or total, total
