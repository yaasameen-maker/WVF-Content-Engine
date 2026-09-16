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
 * back to the front rather than creating a duplicate entry). Returns
 * the updated list so a caller holding its own copy (see
 * useFieldHistory below) can update immediately without waiting for a
 * remount — a value recorded via onBlur wouldn't otherwise appear as a
 * suggestion until the field's component happened to unmount and
 * remount (e.g. closing and reopening the panel), since nothing told
 * an already-mounted <datalist> to re-read storage after the write. */
export function recordFieldHistory(fieldName: string, value: string): string[] {
  const trimmed = value.trim();
  if (!trimmed) return readHistory(fieldName);
  try {
    const existing = readHistory(fieldName).filter((v) => v !== trimmed);
    const next = [trimmed, ...existing].slice(0, MAX_HISTORY_PER_FIELD);
    window.localStorage.setItem(storageKeyFor(fieldName), JSON.stringify(next));
    return next;
  } catch {
    // Storage full/disabled — history just won't record this time.
    return readHistory(fieldName);
  }
}

/** Live-reads a field's history, for feeding a <datalist>, plus a
 * setter so a caller can push an updated list in immediately after
 * calling recordFieldHistory (see that function's docstring for why
 * this needs to happen explicitly rather than automatically). */
export function useFieldHistory(fieldName: string): [string[], (next: string[]) => void] {
  const [history, setHistory] = useState<string[]>([]);
  useEffect(() => {
    setHistory(readHistory(fieldName));
  }, [fieldName]);
  return [history, setHistory];
}
