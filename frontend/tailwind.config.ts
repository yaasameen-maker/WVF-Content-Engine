import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // WVF Content Engine style kit — confirmed from the logo/site
        navy: "#1B2A5E",
        "sky-blue": "#6FA8DC",
      },
    },
  },
  plugins: [],
};

export default config;
