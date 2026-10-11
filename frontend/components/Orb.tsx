type Status = "idle" | "listening" | "thinking" | "speaking";

const COLORS: Record<Status, string> = {
  idle: "from-slate-500 to-slate-700",
  listening: "from-sky-400 to-cyan-600",
  thinking: "from-violet-400 to-fuchsia-600",
  speaking: "from-emerald-400 to-teal-600",
};

export default function Orb({ status, onClick, disabled }: {
  status: Status; onClick: () => void; disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={status === "listening" ? "Stop listening" : "Start talking"}
      className={`orb ${status} relative h-40 w-40 rounded-full bg-gradient-to-br ${COLORS[status]}
        shadow-[0_0_80px_rgba(56,189,248,.25)] transition-colors duration-500
        disabled:opacity-50 focus:outline-none focus:ring-4 focus:ring-white/20`}
    />
  );
}
