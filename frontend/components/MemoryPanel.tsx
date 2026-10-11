export default function MemoryPanel({ memories, onClear }: {
  memories: Record<string, string>; onClear: () => void;
}) {
  const entries = Object.entries(memories);
  return (
    <div className="space-y-2 text-sm">
      {entries.length === 0 ? (
        <p className="text-slate-500">Nothing remembered yet. Tell Sarjy your name or city.</p>
      ) : (
        <ul className="space-y-1">
          {entries.map(([k, v]) => (
            <li key={k} className="flex justify-between gap-3">
              <span className="text-slate-400">{k.replace(/_/g, " ")}</span>
              <span className="text-right text-slate-100">{v}</span>
            </li>
          ))}
        </ul>
      )}
      {entries.length > 0 && (
        <button onClick={onClear} className="text-xs text-rose-400 hover:text-rose-300">
          Forget everything
        </button>
      )}
    </div>
  );
}
