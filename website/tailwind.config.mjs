/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#080808",
          900: "#0D0D0D",
          800: "#111111",
          700: "#151515",
          600: "#1A1A1A",
        },
        line: {
          DEFAULT: "#222222",
          bright: "#292929",
        },
        fg: {
          primary: "#F2F2F2",
          body: "#D5D5D5",
          mute: "#A0A0A0",
          dim: "#737373",
          faint: "#555555",
        },
        ok: "#8BE3B0",
        warn: "#D6A85B",
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "monospace",
        ],
      },
      fontSize: {
        "micro": ["10px", { letterSpacing: "0.14em" }],
        "micro-sm": ["11px", { letterSpacing: "0.12em" }],
      },
      letterSpacing: {
        "tightest": "-0.045em",
        "wider2": "0.18em",
      },
      animation: {
        "pulse-soft": "pulseSoft 2.4s ease-in-out infinite",
        "spin-slow": "spin 8s linear infinite",
        "blink": "blink 1.1s step-end infinite",
      },
      keyframes: {
        pulseSoft: {
          "0%, 100%": { opacity: "0.35" },
          "50%": { opacity: "1" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
      },
    },
  },
  plugins: [],
}
