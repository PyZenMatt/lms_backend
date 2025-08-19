 import type { Config } from "tailwindcss";
 import typography from "@tailwindcss/typography";
 import forms from "@tailwindcss/forms";
+import animate from "tailwindcss-animate";

 const config: Config = {
   content: [
     "./index.html",
     "./src/**/*.{ts,tsx,js,jsx,html}"
   ],
   darkMode: ["class", '[data-theme="dark"]'],
   // important flag rimosso dopo cutover V2 per ridurre specificità globale
   theme: {
-    extend: {
+    container: {
+      center: true,
+      padding: "2rem",
+      screens: { "2xl": "1400px" }
+    },
+    extend: {
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
+        popover: { DEFAULT: "hsl(var(--popover))", foreground: "hsl(var(--popover-foreground))" },
+        card:    { DEFAULT: "hsl(var(--card))",    foreground: "hsl(var(--card-foreground))" }
       },
       borderRadius: {
         lg: "var(--radius)",
         md: "calc(var(--radius) - 2px)",
         sm: "calc(var(--radius) - 4px)",
       },
     },
   },
-  plugins: [typography, forms],
+  // Se generi classi dinamiche (es. via template string), valuta di aggiungere una safelist.
+  // safelist: ["bg-card","text-card-foreground","bg-popover","text-popover-foreground","border-border"],
+  plugins: [typography, forms, animate],
 };

 export default config;
