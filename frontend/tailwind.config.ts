import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Estimated from a screenshot of WVF's real July 2026 newsletter
        // (docs/PROJECT_CONTEXT.md Brand Assets) — not pixel-picked from a
        // source file, so treat as close-but-approximate. Replace with
        // exact values once the team exports real logo/brand files.
        navy: "#4A7EBB",
        "sky-blue": "#87ACD1",
      },
    },
  },
  plugins: [],
};

export default config;
