#!/usr/bin/env node
import { globby } from "globby";
import fs from "node:fs";

const GLOBS = ["src/**/*.{ts,tsx,js,jsx}"];
const RX = /from\s+["']([^"']+)@[\w.\-]+["']/g; // es: "lucide-react@0.487.0"

const files = await globby(GLOBS, { gitignore: true });
let count = 0;
for (const f of files) {
  const txt = fs.readFileSync(f, "utf8");
  const next = txt.replaceAll(RX, (_m, pkg) => `from "${pkg}"`);
  if (next !== txt) {
    fs.writeFileSync(f, next, "utf8");
    count++;
  }
}
console.log(`✓ Strip versioni import: ${count} file aggiornati`);
