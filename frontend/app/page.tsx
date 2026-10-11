"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Orb from "@/components/Orb";
import LatencyPanel, { type ClientTimings } from "@/components/LatencyPanel";
import MemoryPanel from "@/components/MemoryPanel";
import { chat, clearMemories, getMemories } from "@/lib/api";
import { useSpeechRecognition } from "@/lib/useSpeechRecognition";

type Status = "idle" | "listening" | "thinking" | "speaking";
type Turn = { role: "user" | "sarjy"; text: string };

function getUserId(): string {
  const key = "sarjy_user_id";
  let id = localStorage.getItem(key);
  if (!id) { id = crypto.randomUUID(); localStorage.setItem(key, id); }
  return id;
}

export default function Home() {
  const [userId, setUserId] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [memories, setMemories] = useState<Record<string, string>>({});
  const [timings, setTimings] = useState<ClientTimings | null>(null);
  const [typed, setTyped] = useState("");
  const [error, setError] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const id = getUserId();
    setUserId(id);
    getMemories(id).then(r => setMemories(r.memories)).catch(() => {});
  }, []);

  const send = useCallback(async (text: string) => {
    if (!text.trim() || !userId) return;
    setError("");
    setStatus("thinking");
    setTurns(t => [...t, { role: "user", text }]);
    const tSpeechEnd = performance.now();

    try {
      const res = await chat(userId, text);
      const tResponse = performance.now();
      setTurns(t => [...t, { role: "sarjy", text: res.reply }]);
      setStatus("speaking");

      const finish = (tFirstAudio: number, source: "elevenlabs" | "browser") => {
        setTimings({
          server: res.timings,
          round_trip_ms: tResponse - tSpeechEnd,
          network_overhead_ms: tResponse - tSpeechEnd - res.timings.server_total_ms,
          time_to_first_audio_ms: tFirstAudio - tSpeechEnd,
          tts_source: source,
        });
      };

      if (res.audio_b64) {
        const audio = new Audio(`data:${res.audio_mime};base64,${res.audio_b64}`);
        audioRef.current = audio;
        audio.onplaying = () => finish(performance.now(), "elevenlabs");
        audio.onended = () => setStatus("idle");
        audio.onerror = () => setStatus("idle");
        await audio.play();
      } else {
        const u = new SpeechSynthesisUtterance(res.reply);
        u.onstart = () => finish(performance.now(), "browser");
        u.onend = () => setStatus("idle");
        u.onerror = () => setStatus("idle");
        speechSynthesis.speak(u);
      }
      // memories update in background; refresh shortly after
      setTimeout(() => getMemories(userId).then(r => setMemories(r.memories)).catch(() => {}), 1500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      setStatus("idle");
    }
  }, [userId]);

  const { supported, listening, interim, start, stop } = useSpeechRecognition({ onFinal: send });

  useEffect(() => { if (listening) setStatus("listening"); else if (status === "listening") setStatus("idle"); }, [listening]); // eslint-disable-line

  const onOrb = () => {
    if (status === "speaking") { audioRef.current?.pause(); speechSynthesis.cancel(); setStatus("idle"); return; }
    if (listening) stop(); else start();
  };

  const onClear = async () => { await clearMemories(userId); setMemories({}); setTurns([]); };

  return (
    <main className="mx-auto grid min-h-screen max-w-6xl gap-8 p-6 lg:grid-cols-[1fr_320px]">
      <section className="flex flex-col items-center justify-center gap-6">
        <h1 className="text-3xl font-semibold tracking-tight">Sarjy</h1>
        <p className="text-sm text-slate-400">It looks like you want to talk. Tap the orb.</p>

        <Orb status={status} onClick={onOrb} disabled={!userId || status === "thinking"} />

        <p className="h-6 text-center text-slate-300">
          {status === "listening" && (interim || "Listening…")}
          {status === "thinking" && "Thinking…"}
          {status === "speaking" && "Speaking — tap to interrupt"}
        </p>

        <form onSubmit={e => { e.preventDefault(); send(typed); setTyped(""); }} className="flex w-full max-w-md gap-2">
          <input value={typed} onChange={e => setTyped(e.target.value)}
            placeholder={supported ? "Or type instead…" : "Mic needs Chrome/Edge — type here"}
            className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-500" />
          <button className="rounded-lg bg-sky-600 px-4 text-sm font-medium hover:bg-sky-500">Send</button>
        </form>

        {error && <p className="text-sm text-rose-400">{error}</p>}

        <div className="w-full max-w-md space-y-2 text-sm">
          {turns.slice(-6).map((t, i) => (
            <p key={i} className={t.role === "user" ? "text-right text-slate-400" : "text-slate-100"}>
              {t.role === "sarjy" && <span className="mr-2 text-emerald-400">Sarjy</span>}{t.text}
            </p>
          ))}
        </div>
      </section>

      <aside className="space-y-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Latency</h2>
          <LatencyPanel t={timings} />
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Sarjy remembers</h2>
          <MemoryPanel memories={memories} onClear={onClear} />
        </div>
      </aside>
    </main>
  );
}
