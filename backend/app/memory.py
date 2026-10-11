"""Background fact extraction. Runs AFTER the response is sent — costs 0 ms of latency."""
import json
import re

from groq import AsyncGroq

from .config import GROQ_API_KEY, GROQ_FAST_MODEL
from .db import upsert_memories

client = AsyncGroq(api_key=GROQ_API_KEY)
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,39}$")

EXTRACT_PROMPT = """Extract durable personal facts the USER states about themselves.
Return JSON: {"facts": {"snake_case_key": "value"}}.
Good keys: name, home_city, favorite_color, favorite_food, job, language_preference, pet, birthday.
Only include facts explicitly stated by the user in this turn. If none, return {"facts": {}}.
Values must be short strings. Never include questions or assistant statements."""


async def extract_and_store(
    user_id: str, user_text: str, assistant_reply: str, existing: dict[str, str]
) -> None:
    try:
        resp = await client.chat.completions.create(
            model=GROQ_FAST_MODEL,
            messages=[
                {"role": "system", "content": EXTRACT_PROMPT},
                {
                    "role": "user",
                    "content": f"Known so far: {json.dumps(existing)}\n\n"
                               f"USER: {user_text}\nASSISTANT: {assistant_reply}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=200,
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        facts = {
            k: str(v)[:200]
            for k, v in (data.get("facts") or {}).items()
            if isinstance(k, str) and _KEY_RE.match(k) and str(v).strip()
        }
        upsert_memories(user_id, facts)
    except Exception as exc:  # never crash the app over memory
        print(f"[memory] extraction failed: {exc}")
