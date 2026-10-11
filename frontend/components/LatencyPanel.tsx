import type { Timings } from "@/lib/api";

export type ClientTimings = {
  server: Timings;
  round_trip_ms: number;
  network_overhead_ms: number;
  time_to_first_audio_ms: number;
  tts_source: "elevenlabs" | "browser";
};

const fmt = (n: number) => `${Math.round(n)} ms`;

export default function LatencyPanel({ t }: { t: ClientTimings | null }) {
  if (!t) {
    return <p className="text-sm text-slate-500">Speak once to see the latency waterfall.</p>;
  }
  const total = Math.max(t.time_to_first_audio_ms, 1);
  const rows: [string, number][] = [
    ["LLM first call", t.server.llm_first_call_ms],
    ["Tool (Open-Meteo)", t.server.tool_ms],
    ["LLM second call", t.server.llm_second_call_ms],
    ["TTS first byte", t.server.tts_ttfb_ms],
    ["TTS remainder", Math.max(t.server.tts_total_ms - t.server.tts_ttfb_ms, 0)],
    ["Network + decode", Math.max(t.time_to_first_audio_ms - t.server.server_total_ms, 0)],
  ];
  return (
    <div className="space-y-2 text-sm">
      <div className="flex items-baseline justify-between">
        <span className="text-slate-400">Time to first audio</span>
        <span className="text-2xl font-semibold text-emerald-300">{fmt(t.time_to_first_audio_ms)}</span>
      </div>
      {rows.filter(([, v]) => v > 0).map(([label, v]) => (
        <div key={label}>
          <div className="flex justify-between text-slate-400">
            <span>{label}</span><span>{fmt(v)}</span>
          </div>
          <div className="h-1.5 w-full rounded bg-slate-800">
            <div className="h-1.5 rounded bg-sky-400" style={{ width: `${Math.min((v / total) * 100, 100)}%` }} />
          </div>
        </div>
      ))}
      <p className="pt-1 text-xs text-slate-500">
        Server total {fmt(t.server.server_total_ms)} · round trip {fmt(t.round_trip_ms)} · TTS via {t.tts_source}
      </p>
    </div>
  );
}
