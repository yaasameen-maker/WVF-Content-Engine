"use client";

import { useEffect, useState } from "react";

/**
 * Recently-typed values per named field (e.g. "event speaker," "event
 * audience"), persisted to localStorage — so staff filling out the same
 * kind of event/campaign repeatedly (the same speaker, a recurring
 * audience description) get autocomplete suggestions instead of
 * retyping the same text every time. Surfaced via native <datalist>
 * (see recordFieldHistory's usage in app/page.tsx's <input list=...>
 * attributes) rather than a custom dropdown — the browser already
 * renders that natively with no extra UI code.
 *
 * Deliberately per-field, not per-form: "speaker" suggestions should
 * show up whether staff is filling out the tile-flow event form or the
 * standalone AI Generate form, since it's the same real-world speaker
 * either way.
 */

const MAX_HISTORY_PER_FIELD = 8;
const STORAGE_PREFIX = "wvf_field_history_";

function storageKeyFor(fieldName: string): string {
  return `${STORAGE_PREFIX}${fieldName}`;
}

function readHistory(fieldName: string): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(storageKeyFor(fieldName));
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

/** Call when a field is committed (e.g. its onBlur, or right before
 * submit) — not on every keystroke, so history doesn't fill up with
 * every partial value typed along the way. Empty/whitespace-only
 * values are ignored. Most-recent-first, capped at
 * MAX_HISTORY_PER_FIELD, de-duplicated (re-using a past value moves it
 * back to the front rather than creating a duplicate entry). */
export function recordFieldHistory(fieldName: string, value: string): void {
  const trimmed = value.trim();
  if (!trimmed) return;
  try {
    const existing = readHistory(fieldName).filter((v) => v !== trimmed);
    const next = [trimmed, ...existing].slice(0, MAX_HISTORY_PER_FIELD);
    window.localStorage.setItem(storageKeyFor(fieldName), JSON.stringify(next));
  } catch {
    // Storage full/disabled — history just won't record this time.
  }
}

/** Live-reads a field's history, for feeding a <datalist>. Re-reads on
 * every mount rather than staying subscribed — history changes only
 * when this same tab records a new value (via recordFieldHistory,
 * itself only called from this page), so a mount-time read is enough;
 * no cross-tab sync is attempted. */
export function useFieldHistory(fieldName: string): string[] {
  const [history, setHistory] = useState<string[]>([]);
  useEffect(() => {
    setHistory(readHistory(fieldName));
  }, [fieldName]);
  return history;
}
