"""Single source of truth for configuration. Everything comes from env vars."""
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Llama 3.x models were retired on Groq's free/dev tiers (Aug 2026). GPT-OSS is the
# recommended replacement and supports tools + json_mode.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")          # conversation + tools
GROQ_FAST_MODEL = os.getenv("GROQ_FAST_MODEL", "openai/gpt-oss-20b")  # memory extraction
# GPT-OSS models reason before answering; "low" keeps voice latency down.
GROQ_REASONING_EFFORT = os.getenv("GROQ_REASONING_EFFORT", "low")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sarjy.db")

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
