/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Niaga warm-earth palette (Indonesian-inspired, not generic SaaS purple)
        terracotta: {
          50:  "#fdf5f0",
          100: "#f9e3d4",
          200: "#f2c5a3",
          300: "#e89f6f",
          400: "#dc7b48",
          500: "#c95c2a",
          600: "#a8451f",
          700: "#83351a",
          800: "#5d2614",
          900: "#3a170c",
        },
        sandstone: {
          50:  "#faf8f4",
          100: "#f0ebe0",
          200: "#ddd1bb",
          300: "#c7b58e",
          400: "#b29a66",
          500: "#9c8044",
          600: "#7a6334",
          700: "#5a4726",
          800: "#3a2e18",
          900: "#1f180d",
        },
        // Per-agent feed colors
        agent: {
          prospector: "#0d9488",  // teal
          bull:       "#16a34a",  // green
          bear:       "#dc2626",  // red
          judge:      "#ca8a04",  // gold
          outreach:   "#2563eb",  // blue
          reply:      "#9333ea",  // purple
          closer:     "#c95c2a",  // terracotta
          aftercare:  "#0891b2",  // cyan
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
};
