export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Timings = {
  llm_first_call_ms: number;
  tool_ms: number;
  llm_second_call_ms: number;
  llm_total_ms: number;
  tts_ttfb_ms: number;
  tts_total_ms: number;
  server_total_ms: number;
};

export type ChatResponse = {
  reply: string;
  audio_b64: string | null;
  audio_mime: string;
  tool_calls: string[];
  timings: Timings;
  memories: Record<string, string>;
};

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export function chat(user_id: string, text: string) {
  return fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, text }),
  }).then(handle<ChatResponse>);
}

export function getMemories(user_id: string) {
  return fetch(`${API_URL}/api/memory/${user_id}`).then(
    handle<{ memories: Record<string, string> }>
  );
}

export function clearMemories(user_id: string) {
  return fetch(`${API_URL}/api/memory/${user_id}`, { method: "DELETE" }).then(
    handle<{ deleted: boolean }>
  );
}
