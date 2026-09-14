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
  // Lazy initializer so the restore only runs once, on first mount —
  // and only in the browser, since localStorage doesn't exist during
  // Next.js's server render.
  const [value, setValue] = useState<T>(() => {
    if (typeof window === "undefined") return initialValue;
    try {
      const raw = window.localStorage.getItem(storageKey);
      return raw ? (JSON.parse(raw) as T) : initialValue;
    } catch {
      // Corrupt/unparseable stored value — fall back to a fresh draft
      // rather than crashing the page on mount.
      return initialValue;
    }
  });

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
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
  }, [value]);

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
