import type { Metadata } from "next";
import "./globals.css";
import { SiteNav } from "@/components/SiteNav";

export const metadata: Metadata = {
  title: "WVF Content Engine",
  description: "AI-powered marketing content generation for Women's Venture Fund",
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
          <div className="flex items-center justify-between px-6 py-3">
            <div className="flex items-center gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/wvf-logo.svg" alt="Women's Venture Fund" className="h-10 w-auto" />
              <span className="text-lg font-bold text-navy">Content Engine</span>
            </div>
            <SiteNav />
          </div>
        </header>
        {/*
          side-rail-slot docks a page's collapsed tile rail (New Campaign,
          Profiles) to the TRUE left edge of the window — absolutely
          positioned relative to this full-width wrapper, so it never
          affects <main>'s own centering (unlike putting it in normal
          flex flow next to <main>, which would shift main's center point
          by however wide the rail is). Pages reach this via
          SideRailPortal rather than nesting the rail inside their own
          centered content. Not `fixed` — it scrolls with the page.
        */}
        <div className="relative w-full">
          <div id="side-rail-slot" className="absolute left-6 top-4" />
          <main className="mx-auto max-w-4xl px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
