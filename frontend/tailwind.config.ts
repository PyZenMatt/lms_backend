import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";
import forms from "@tailwindcss/forms";

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx,js,jsx,html}"
  ],
  darkMode: ["class", '[data-theme="dark"]'],
  important: true, // <— temporaneo: le utility diventano !important
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary:{ DEFAULT:"hsl(var(--secondary))",foreground:"hsl(var(--secondary-foreground))"},
        muted:    { DEFAULT:"hsl(var(--muted))",    foreground:"hsl(var(--muted-foreground))" },
        accent:   { DEFAULT:"hsl(var(--accent))",   foreground:"hsl(var(--accent-foreground))" },
        destructive:{DEFAULT:"hsl(var(--destructive))",foreground:"hsl(var(--destructive-foreground))"},
        border: "hsl(var(--border))",
        input:  "hsl(var(--input))",
        ring:   "hsl(var(--ring))",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [typography, forms],
};

export default config;
