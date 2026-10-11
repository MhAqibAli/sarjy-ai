"""Groq conversation call with a bounded tool-calling loop and per-stage timings."""
import asyncio
import json
from datetime import datetime
from time import perf_counter

from groq import AsyncGroq

from .config import GROQ_API_KEY, GROQ_MODEL, GROQ_REASONING_EFFORT
from .tools import TOOL_HANDLERS, TOOLS

client = AsyncGroq(api_key=GROQ_API_KEY)

# Passed via extra_body so it works regardless of groq SDK version.
_EXTRA = {"reasoning_effort": GROQ_REASONING_EFFORT}


def build_system_prompt(memories: dict[str, str]) -> str:
    memory_block = (
        "\n".join(f"- {k.replace('_', ' ')}: {v}" for k, v in memories.items())
        or "- (nothing yet)"
    )
    now = datetime.now().strftime("%A, %d %B %Y, %H:%M")
    return f"""You are Sarjy, a warm, quick-witted voice assistant built for Sarj.

Everything you say is spoken aloud, so:
- Reply in 1-3 short sentences. No markdown, no lists, no emojis, no URLs.
- Mirror the user's language (English, Urdu, or Roman Urdu).
- Be concise and natural; a little playful self-awareness is fine.

Current date/time: {now}

What you remember about this user:
{memory_block}

Rules:
- Use remembered facts naturally (e.g. use home city for weather if no city is given).
- Tools are the ONLY source of live data. Never invent temperatures, times or facts.
- If a tool returns an error, say plainly that you couldn't fetch it. Do not guess.
- If asked what you remember, summarize the list above honestly."""


def _assistant_with_tool_calls(msg) -> dict:
    return {
        "role": "assistant",
        "content": msg.content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ],
    }


async def _run_tool(tc) -> tuple[str, str, str]:
    name = tc.function.name
    try:
        args = json.loads(tc.function.arguments or "{}")
    except json.JSONDecodeError:
        args = {}
    handler = TOOL_HANDLERS.get(name)
    result = await handler(**args) if handler else {"error": f"Unknown tool {name}"}
    return tc.id, name, json.dumps(result)


async def run_llm(
    text: str, memories: dict[str, str], history: list[dict[str, str]]
) -> tuple[str, list[str], dict[str, float]]:
    """Returns (reply, tools_used, timings)."""
    t_start = perf_counter()
    timings: dict[str, float] = {}
    messages = [
        {"role": "system", "content": build_system_prompt(memories)},
        *history,
        {"role": "user", "content": text},
    ]

    t0 = perf_counter()
    first = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.6,
        max_tokens=300,
        extra_body=_EXTRA,
    )
    timings["llm_first_call_ms"] = (perf_counter() - t0) * 1000

    msg = first.choices[0].message
    used: list[str] = []

    if msg.tool_calls:
        messages.append(_assistant_with_tool_calls(msg))
        t1 = perf_counter()
        results = await asyncio.gather(*(_run_tool(tc) for tc in msg.tool_calls))
        timings["tool_ms"] = (perf_counter() - t1) * 1000
        for call_id, name, content in results:
            used.append(name)
            messages.append(
                {"role": "tool", "tool_call_id": call_id, "name": name, "content": content}
            )

        t2 = perf_counter()
        second = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.6,
            max_tokens=300,
            extra_body=_EXTRA,
        )
        timings["llm_second_call_ms"] = (perf_counter() - t2) * 1000
        reply = second.choices[0].message.content or ""
    else:
        reply = msg.content or ""

    timings["llm_total_ms"] = (perf_counter() - t_start) * 1000
    return reply.strip(), used, timings
