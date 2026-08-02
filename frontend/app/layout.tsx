import type { Metadata } from "next";
import "./globals.css";

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
        <header className="bg-navy text-white">
          <div className="mx-auto max-w-4xl px-6 py-4">
            <h1 className="text-lg font-bold tracking-wide">WVF Content Engine</h1>
          </div>
        </header>
        <main className="mx-auto max-w-4xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
