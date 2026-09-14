"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Persists in-progress form state to localStorage so a refresh or
 * accidental tab close doesn't lose a half-typed event/campaign draft.
 * Previously nothing on the New Campaign form autosaved at all — only
 * a *successfully generated* result got saved (to sessionStorage, in
 * app/page.tsx's handleSubmit/handleSocialAiSubmit) right before
 * navigating to /review. Everything typed before that point had no
 * recovery path.
 *
 * localStorage (not sessionStorage) is deliberate here: an in-progress
 * draft should survive a closed tab, not just a refresh within the
 * same tab — losing a half-written event description because someone
 * closed the tab by mistake is the same problem this is meant to fix.
 *
 * Debounced (not written on every keystroke) to avoid thrashing
 * localStorage on a long description field — DEBOUNCE_MS is a balance
 * between "recent enough to not lose much on a crash" and "not writing
 * dozens of times per second while typing."
 */

const DEBOUNCE_MS = 500;

export function useDraftState<T>(
  storageKey: string,
  initialValue: T
): [T, React.Dispatch<React.SetStateAction<T>>, () => void] {
  // Always starts at initialValue — matching what the server rendered
  // (it has no localStorage to read) — and restores in an effect below
  // instead of a lazy useState initializer. Reading localStorage in the
  // initializer made the client's very first render diverge from the
  // server-rendered HTML whenever a draft existed, which is a React
  // hydration mismatch: React detects the mismatch, throws (visible in
  // the console as minified errors #418/#423), and discards the
  // mismatched client render — falling back to the server-rendered
  // (empty) tree. That's what "refreshing wipes the whole form" actually
  // was: not a failure to save or restore the draft, but React
  // rejecting the restored render because it didn't match SSR output.
  const [value, setValue] = useState<T>(initialValue);
  const [isRestored, setIsRestored] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Runs once, after mount — by definition client-only, so this is the
  // safe place to touch localStorage and diverge from the SSR output;
  // effects run after hydration completes, not during it.
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw) setValue(JSON.parse(raw) as T);
    } catch {
      // Corrupt/unparseable stored value — keep initialValue rather
      // than crashing.
    } finally {
      setIsRestored(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    // Skip the write that would otherwise fire the instant the restore
    // effect above sets state — that write is redundant (it'd just
    // save back the same value just read) and, before restore
    // finishes, would overwrite a real stored draft with initialValue.
    if (!isRestored) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      try {
        window.localStorage.setItem(storageKey, JSON.stringify(value));
      } catch {
        // Storage full/disabled — the draft just won't persist this
        // time; not worth surfacing an error for an autosave.
      }
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, isRestored]);

  function clearDraft() {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    try {
      window.localStorage.removeItem(storageKey);
    } catch {
      // Nothing to do if storage is unavailable — the in-memory state
      // reset below is what actually matters to the user.
    }
    setValue(initialValue);
  }

  return [value, setValue, clearDraft];
}
