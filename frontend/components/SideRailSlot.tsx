"use client";

import { type ReactNode } from "react";
import { createPortal } from "react-dom";

/**
 * Lets a page (New Campaign, Profiles) render its collapsed tile rail at
 * the TRUE left edge of the browser window — docked like a real sidebar —
 * while its own main content stays in the normal centered max-w-4xl
 * column. A plain nested <div> can't do this: it's constrained by
 * <main>'s centering. Instead, RootLayout renders an empty slot element
 * (#side-rail-slot) as a true sibling of <main> inside one full-width
 * flex row, and pages reach it via a portal instead of local nesting.
 *
 * Not `position: fixed` — the rail scrolls with the page like normal
 * content; it just starts flush against the window's left edge instead
 * of the left edge of the centered content column.
 */
export function SideRailPortal({ children }: { children: ReactNode }) {
  if (typeof document === "undefined") return null;
  const target = document.getElementById("side-rail-slot");
  if (!target) return null;
  return createPortal(children, target);
}
