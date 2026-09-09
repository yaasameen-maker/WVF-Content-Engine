"use client";

import { usePathname } from "next/navigation";
import { SiteNav } from "@/components/SiteNav";

// Pages an approver reaches directly from an emailed link, not by
// browsing the app, shouldn't show the internal nav (New Campaign /
// Calendar / Profiles) — it's dead weight for someone who's there to do
// one thing, and it's misleading chrome on a page meant to look like a
// standalone reset flow, not the main app shell.
const CHROMELESS_PATHS = ["/reset-passcode"];

export function SiteHeader() {
  const pathname = usePathname();
  if (CHROMELESS_PATHS.includes(pathname)) {
    return null;
  }

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2 sm:gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/wvf-logo.svg" alt="Women's Venture Fund" className="h-8 w-auto sm:h-10" />
          <span className="text-base font-bold text-navy sm:text-lg">Content Engine</span>
        </div>
        <SiteNav />
      </div>
    </header>
  );
}

export function SideRailSlotWrapper() {
  const pathname = usePathname();
  if (CHROMELESS_PATHS.includes(pathname)) {
    return null;
  }

  return (
    <div
      id="side-rail-slot"
      className="static mb-2 flex justify-start overflow-x-auto px-4 sm:absolute sm:left-6 sm:top-4 sm:mb-0 sm:block sm:overflow-visible sm:px-0"
    />
  );
}
