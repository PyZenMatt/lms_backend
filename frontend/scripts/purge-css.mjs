import { globby } from "globby";
import fs from "node:fs/promises";
import path from "node:path";

const GLOB_REMOVE_DIRS = [
  "src/assets/scss/**",
  "src/assets/css/**",
  "src/styles/legacy/**",
];
const IMPORT_PATTERNS = [
  /import\s+["'].*assets\/scss\/.*["'];?\n?/g,
  /import\s+["'].*assets\/css\/.*["'];?\n?/g,
  /import\s+["'].*styles\/legacy\/.*["'];?\n?/g,
  /@import\s+["'].*assets\/scss\/.*["'];?\n?/g,
  /@import\s+["'].*assets\/css\/.*["'];?\n?/g,
  /@import\s+["'].*styles\/legacy\/.*["'];?\n?/g,
];

async function removeDirs() {
  const files = await globby(GLOB_REMOVE_DIRS, { dot: true });
  const dirs = new Set(files.map(f => f.split(path.sep).slice(0,3).join(path.sep)));
  for (const d of dirs) {
    try { await fs.rm(d, { recursive: true, force: true }); console.log("🗑️  removed", d); }
    catch (e) { /* ignore */ }
  }
}

async function stripImports() {
  const files = await globby(["src/**/*.{ts,tsx,js,jsx,css,scss}"]);
  for (const f of files) {
    let txt = await fs.readFile(f, "utf8");
    let changed = false;
    for (const re of IMPORT_PATTERNS) {
      if (re.test(txt)) { txt = txt.replace(re, ""); changed = true; }
    }
    if (changed) {
      await fs.writeFile(f, txt, "utf8");
      console.log("✳︎ stripped legacy imports:", f);
    }
  }
}

await removeDirs();
await stripImports();
console.log("✅ Purge CSS/SCSS legacy completato.");
