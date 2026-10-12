"use client";

export function BrowserBanner({ reason }: { reason?: string }) {
  return (
    <div className="mb-4 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
      <strong>Voice input unavailable in this browser.</strong>{" "}
      {reason ?? "The Web Speech API is only supported in Chrome and Edge."}{" "}
      You can still chat by typing below — replies will be spoken aloud.
    </div>
  );
}
