import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme colors matching mockup
        background: {
          DEFAULT: "#0a0e17",
          secondary: "#0d1421",
          card: "#111827",
        },
        accent: {
          DEFAULT: "#00d4ff",
          dim: "#00a8cc",
          glow: "rgba(0, 212, 255, 0.3)",
        },
        border: {
          DEFAULT: "#1e3a5f",
          light: "#2d4a6f",
        },
      },
      backgroundImage: {
        "grid-pattern": `
          linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px)
        `,
        "gradient-radial": "radial-gradient(ellipse at center, var(--tw-gradient-stops))",
      },
      backgroundSize: {
        "grid": "50px 50px",
      },
      boxShadow: {
        "glow": "0 0 20px rgba(0, 212, 255, 0.3)",
        "glow-sm": "0 0 10px rgba(0, 212, 255, 0.2)",
        "card": "0 4px 20px rgba(0, 0, 0, 0.5)",
      },
      animation: {
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
      },
      keyframes: {
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 20px rgba(0, 212, 255, 0.3)" },
          "50%": { boxShadow: "0 0 30px rgba(0, 212, 255, 0.5)" },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
