import { globby } from "globby";
import fs from "node:fs/promises";

// Remove "@<semver>" suffix from any import path (e.g. '@radix-ui/react-dialog@1.1.6')
const VERSIONED = /from\s+["']([^"']+?)@\d+(?:\.\d+){0,2}["']/g;

// Additional direct fixes (idempotent)
const DIRECT_FIXES = [
  { re: /from\s+["']lucide-react@[^"']+["']/g, to: 'from "lucide-react"' },
  { re: /from\s+["']sonner@[^"']+["']/g, to: 'from "sonner"' },
  { re: /from\s+["']recharts@[^"']+["']/g, to: 'from "recharts"' },
  { re: /from\s+["']cmdk@[^"']+["']/g, to: 'from "cmdk"' },
  { re: /from\s+["']vaul@[^"']+["']/g, to: 'from "vaul"' },
  { re: /from\s+["']input-otp@[^"']+["']/g, to: 'from "input-otp"' },
  { re: /from\s+["']react-hook-form@[^"']+["']/g, to: 'from "react-hook-form"' },
  { re: /from\s+["']react-day-picker@[^"']+["']/g, to: 'from "react-day-picker"' },
  { re: /from\s+["']embla-carousel-react@[^"']+["']/g, to: 'from "embla-carousel-react"' },
  { re: /from\s+["']react-resizable-panels@[^"']+["']/g, to: 'from "react-resizable-panels"' },
  { re: /from\s+["']next-themes@[^"']+["']/g, to: 'from "next-themes"' },
  { re: /from\s+["']class-variance-authority@[^"']+["']/g, to: 'from "class-variance-authority"' },
];

const files = await globby(["src/**/*.{ts,tsx,js,jsx}"]);
let changed = 0;
for (const f of files) {
  let src = await fs.readFile(f, "utf8");
  const before = src;

  src = src.replace(VERSIONED, (_m, lib) => `from "${lib}"`);
  for (const { re, to } of DIRECT_FIXES) src = src.replace(re, to);

  if (src !== before) {
    await fs.writeFile(f, src, "utf8");
    console.log("✳︎ normalized:", f);
    changed++;
  }
}
console.log(`✅ normalize-imports done. Files updated: ${changed}`);
