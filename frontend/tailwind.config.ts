import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#28030F",
          light: "#5B3E47",
          mid: "#4C2934",
          muted: "#755760",
        },
        cream: {
          DEFAULT: "#FCFAF8",
          card: "#F9F4F1",
          blush: "#F4E7DD",
        },
        mauve: {
          DEFAULT: "#D4C4C9",
          dark: "#C39DA8",
        },
        accent: "#FBF582",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
