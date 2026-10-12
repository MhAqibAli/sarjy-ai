"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useCallback, useEffect, useRef, useState } from "react";

type Options = { lang?: string; onFinal: (text: string) => void };

/** Human-readable messages for SpeechRecognition error codes. */
const ERROR_MESSAGES: Record<string, string> = {
  "not-allowed": "Microphone permission was denied. Allow mic access and reload, or type below.",
  "service-not-allowed": "Speech recognition is disabled in this browser. You can still type below.",
  "network": "Speech service unreachable — Chrome needs an internet connection for voice input.",
  "audio-capture": "No microphone was found. You can still type below.",
  "language-not-supported": "This language isn't supported for voice input.",
};

/** Errors that are normal during use (silence, user stopped) — don't disable voice for these. */
const SOFT_ERRORS = new Set(["no-speech", "aborted"]);

/** If the engine "starts" but never opens the mic within this window, assume it's a non-functional stub. */
const WATCHDOG_MS = 8000;

export function useSpeechRecognition({ lang = "en-US", onFinal }: Options) {
  // null = still checking (avoids a banner flash on first paint in Chrome)
  const [supported, setSupported] = useState<boolean | null>(null);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const recRef = useRef<any>(null);
  const onFinalRef = useRef(onFinal);
  const watchdogRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const gotAudioRef = useRef(false);

  useEffect(() => { onFinalRef.current = onFinal; }, [onFinal]);

  const clearWatchdog = () => {
    if (watchdogRef.current) { clearTimeout(watchdogRef.current); watchdogRef.current = null; }
  };

  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setSupported(false); return; }

    // Firefox can expose the constructor while recognition is actually disabled.
    let rec: any;
    try {
      rec = new SR();
    } catch {
      setSupported(false);
      return;
    }

    rec.lang = lang;
    rec.interimResults = true;
    rec.continuous = false;
    rec.maxAlternatives = 1;

    rec.onaudiostart = () => {
      gotAudioRef.current = true;
      clearWatchdog();
      setVoiceError(null); // mic is genuinely working — clear any stale error
    };

    rec.onresult = (e: any) => {
      gotAudioRef.current = true;
      clearWatchdog();
      let finalText = "", interimText = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalText += t; else interimText += t;
      }
      setInterim(interimText);
      if (finalText.trim()) { setInterim(""); onFinalRef.current(finalText.trim()); }
    };

    rec.onend = () => { clearWatchdog(); setListening(false); setInterim(""); };

    rec.onerror = (e: any) => {
      clearWatchdog();
      setListening(false);
      setInterim("");
      const code: string = e?.error ?? "unknown";
      if (SOFT_ERRORS.has(code)) return; // silence / manual stop — not a real failure
      setVoiceError(ERROR_MESSAGES[code] ?? `Voice input failed (${code}). You can still type below.`);
    };

    recRef.current = rec;
    setSupported(true);

    return () => { clearWatchdog(); rec.abort(); };
  }, [lang]);

  const start = useCallback(() => {
    const rec = recRef.current;
    if (!rec) {
      // This is the Firefox case that used to flip "listening" on with no engine behind it.
      setVoiceError("Voice input isn't available in this browser. You can still type below.");
      setListening(false);
      return;
    }

    gotAudioRef.current = false;
    try {
      rec.start();
      setListening(true); // only after start() succeeded
    } catch {
      // Usually "already started" — leave state as-is
      return;
    }

    clearWatchdog();
    watchdogRef.current = setTimeout(() => {
      if (!gotAudioRef.current) {
        try { rec.abort(); } catch { /* noop */ }
        setListening(false);
        setVoiceError("The browser accepted the mic but never captured audio. Falling back to text input.");
      }
    }, WATCHDOG_MS);
  }, []);

  const stop = useCallback(() => { clearWatchdog(); recRef.current?.stop(); }, []);

  /** Lets the UI offer a "try voice again" action after a transient error. */
  const resetVoiceError = useCallback(() => setVoiceError(null), []);

  const voiceAvailable = supported === true && voiceError === null;

  return { supported, voiceError, voiceAvailable, resetVoiceError, listening, interim, start, stop };
}
