/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      colors: {
        /* usa direttamente i token CSS (HEX/OKLCH/HSL…) */
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: "var(--card)",
        "card-foreground": "var(--card-foreground)",
        popover: "var(--popover)",
        "popover-foreground": "var(--popover-foreground)",
        primary: "var(--primary)",
        "primary-foreground": "var(--primary-foreground)",
        secondary: "var(--secondary)",
        "secondary-foreground": "var(--secondary-foreground)",
        muted: "var(--muted)",
        "muted-foreground": "var(--muted-foreground)",
        accent: "var(--accent)",
        "accent-foreground": "var(--accent-foreground)",
        destructive: "var(--destructive)",
        "destructive-foreground": "var(--destructive-foreground)",
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
  overlay: "var(--color-overlay)",
      },
      borderRadius: {
        lg: "var(--radius, 0.5rem)",
              background: "hsl(var(--color-background) / <alpha-value>)",
              foreground: "hsl(var(--color-foreground) / <alpha-value>)",
              muted: "hsl(var(--color-muted) / <alpha-value>)",
              "muted-foreground": "hsl(var(--color-muted-foreground) / <alpha-value>)",
              card: "hsl(var(--color-card) / <alpha-value>)",
              "card-foreground": "hsl(var(--color-card-foreground) / <alpha-value>)",
              border: "hsl(var(--color-border) / <alpha-value>)",
              primary: "hsl(var(--color-primary) / <alpha-value>)",
              "primary-foreground": "hsl(var(--color-primary-foreground) / <alpha-value>)",
              accent: "hsl(var(--color-accent) / <alpha-value>)",
              "accent-foreground": "hsl(var(--color-accent-foreground) / <alpha-value>)",
              destructive: "hsl(var(--color-destructive) / <alpha-value>)",
              "destructive-foreground": "hsl(var(--color-destructive-foreground) / <alpha-value>)",
              ring: "hsl(var(--color-ring) / <alpha-value>)",
              overlay: "hsl(var(--color-overlay) / <alpha-value>)",
      fontFamily: {
          sans: ["var(--font-sans)", "system-ui", "sans-serif"],
          mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
        fontSize: {
          xs: ["var(--text-xs)", { lineHeight: "var(--leading-xs)" }],
              xl: "var(--radius-xl)",
              "2xl": "var(--radius-2xl)",
          sm: ["var(--text-sm)", { lineHeight: "var(--leading-sm)" }],
          base: ["var(--text-base)", { lineHeight: "var(--leading-base)" }],
          lg: ["var(--text-lg)", { lineHeight: "var(--leading-lg)" }],
          xl: ["var(--text-xl)", { lineHeight: "var(--leading-xl)" }],
          "2xl": ["var(--text-2xl)", { lineHeight: "var(--leading-2xl)" }],
          "3xl": ["var(--text-3xl)", { lineHeight: "var(--leading-3xl)" }],
          "4xl": ["var(--text-4xl)", { lineHeight: "var(--leading-4xl)" }],
        },
        container: {
          center: true,
              /* additional shadows can be added here */
          padding: "1rem",
            backdropBlur: {
              xs: "2px",
            },
            ringColor: {
              DEFAULT: "hsl(var(--color-ring) / <alpha-value>)",
            },
            container: { center: true, padding: "var(--space-container)" },
          screens: { sm:"640px", md:"768px", lg:"1024px", xl:"1280px", "2xl":"1440px" }
        },
        spacing: {
          "gutter": "1rem",     /* gutter base Figma */
          "gutter-lg": "1.5rem" /* gutter grande */
        },
      boxShadow: {
        xs: "var(--shadow-xs)",
        sm: "var(--shadow-sm)",
        DEFAULT: "var(--shadow-default)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        xl: "var(--shadow-xl)",
        '2xl': "var(--shadow-2xl)",
        card: "var(--shadow-card)",
      },
    },
  },
  plugins: [],
}
