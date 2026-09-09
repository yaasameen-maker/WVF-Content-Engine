import type { Metadata, Viewport } from "next";
import "./globals.css";
import { SiteNav } from "@/components/SiteNav";

export const metadata: Metadata = {
  title: "WVF Content Engine",
  description: "AI-powered marketing content generation for Women's Venture Fund",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {/*
          Single white header bar (not the earlier white-strip-above-navy
          split): the logo file is a flattened raster PNG (see git history
          — no editable text/paths to selectively recolor), so rather than
          risk poor contrast placing it directly on navy, the whole header
          stays white and the nav/toolbar sit on white too. See
          docs/PROJECT_CONTEXT.md Brand Assets.
        */}
        <header className="border-b border-gray-200 bg-white">
          {/* Full-width, not mx-auto max-w-4xl: logo sits at the true left
              edge of the window and nav at the true right edge, rather than
              both centered together as one group within the narrower
              content column. */}
          <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
            <div className="flex items-center gap-2 sm:gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/wvf-logo.svg" alt="Women's Venture Fund" className="h-8 w-auto sm:h-10" />
              <span className="text-base font-bold text-navy sm:text-lg">Content Engine</span>
            </div>
            <SiteNav />
          </div>
        </header>
        {/*
          side-rail-slot docks a page's collapsed tile rail (New Campaign,
          Profiles) to the TRUE left edge of the window on desktop —
          absolutely positioned relative to this full-width wrapper, so it
          never affects <main>'s own centering (unlike putting it in normal
          flex flow next to <main>, which would shift main's center point
          by however wide the rail is). Pages reach this via
          SideRailPortal rather than nesting the rail inside their own
          centered content. Not `fixed` — it scrolls with the page.

          Below sm (640px), there's no room to the left of <main> for an
          absolutely-positioned rail — it would sit directly on top of
          <main>'s own content instead of beside it (both start flush
          against the window edge on a narrow screen). Below that
          breakpoint the slot instead sits in normal flow, above <main>,
          full-width, and horizontally scrollable — same portal target,
          same children, only the CSS placement changes (see the
          collapsed-rail components' own sm: overflow-x-auto handling for
          how the tile row itself adapts to that horizontal strip).
        */}
        <div className="relative w-full">
          <div
            id="side-rail-slot"
            className="static mb-2 flex justify-start overflow-x-auto px-4 sm:absolute sm:left-6 sm:top-4 sm:mb-0 sm:block sm:overflow-visible sm:px-0"
          />
          <main className="mx-auto max-w-4xl px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
