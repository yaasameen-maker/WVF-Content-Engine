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
          Logo placed on a white strip, not directly on bg-navy below: the
          SVG's colors are baked in via internal mask/filter compositing
          (not plain fills), so they can't be reliably assumed to read well
          against navy. White guarantees visibility regardless of the
          logo's actual palette — see docs/PROJECT_CONTEXT.md Brand Assets.
        */}
        <div className="bg-white">
          <div className="mx-auto max-w-4xl px-6 py-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/wvf-logo.svg" alt="Women's Venture Fund" className="h-10 w-auto" />
          </div>
        </div>
        <header className="bg-navy text-white">
          <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
            <h1 className="text-lg font-bold tracking-wide">WVF Content Engine</h1>
            <SiteNav />
          </div>
        </header>
        <main className="mx-auto max-w-4xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
