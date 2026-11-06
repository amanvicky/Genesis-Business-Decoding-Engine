import type { Config } from "tailwindcss";

/*
 * Hallmark token block — the single source for every colour the app uses.
 * Deep ink paper (cool, hue 250), one amber signal (hue 75), data colours
 * (rise green, fall red, info cool, psych violet) tinted, never pure.
 * The framework shade names stay so the dossier's 18 content tabs inherit
 * the system without touching their markup.
 */
const ink = (l: number, c = 0.012) => `oklch(${l}% ${c} 250)`;

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: ink(13),
        panel: ink(16),
        edge: ink(24),
        white: ink(96),
        zinc: {
          100: ink(92),
          200: ink(86),
          300: ink(80),
          400: ink(70),
          500: ink(62),
          600: ink(59),
          700: ink(40),
          800: ink(28),
          900: ink(16),
          950: ink(13),
        },
        emerald: {
          100: `oklch(90% 0.05 160)`,
          300: `oklch(82% 0.11 160)`,
          400: `oklch(74% 0.14 160)`,
          500: `oklch(68% 0.15 160)`,
          600: `oklch(60% 0.14 160)`,
          700: `oklch(48% 0.12 160)`,
          800: `oklch(32% 0.08 160)`,
          900: `oklch(26% 0.06 160)`,
          950: `oklch(20% 0.045 160)`,
        },
        red: {
          300: `oklch(78% 0.10 25)`,
          400: `oklch(68% 0.17 25)`,
          500: `oklch(62% 0.19 25)`,
          800: `oklch(34% 0.10 25)`,
          900: `oklch(27% 0.08 25)`,
          950: `oklch(20% 0.055 25)`,
        },
        amber: {
          300: `oklch(84% 0.11 80)`,
          400: `oklch(78% 0.14 75)`,
          500: `oklch(72% 0.15 72)`,
          700: `oklch(48% 0.10 70)`,
          800: `oklch(38% 0.08 72)`,
          900: `oklch(28% 0.06 74)`,
          950: `oklch(21% 0.045 75)`,
        },
        cyan: {
          400: `oklch(74% 0.08 230)`,
          500: `oklch(68% 0.09 230)`,
          600: `oklch(58% 0.09 232)`,
          700: `oklch(46% 0.08 234)`,
          800: `oklch(34% 0.06 236)`,
          900: `oklch(27% 0.045 238)`,
          950: `oklch(20% 0.035 240)`,
        },
        purple: {
          400: `oklch(72% 0.09 310)`,
          900: `oklch(27% 0.05 308)`,
          950: `oklch(20% 0.04 306)`,
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        DEFAULT: "0",
        md: "0",
        lg: "0",
        xl: "0",
      },
      animation: {
        "pulse-dot": "pulseDot 1.4s ease-in-out infinite",
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { opacity: "0.35" },
          "50%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
