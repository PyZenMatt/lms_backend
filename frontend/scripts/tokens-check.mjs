// Simplified hardcoded color ban: allow only CSS variables + transparent/ currentColor.
import fs from 'node:fs';
import { glob } from 'glob';

const files = await glob(['src/**/*.{ts,tsx,js,jsx,css}'], { nodir: true, ignore: ['**/node_modules/**','dist/**','build/**'] });
const COLOR_RE = /(:|=|\s)(#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)|\b(white|black|red|green|blue|orange|yellow|purple|gray|grey|silver|gold)\b)/g;
const ALLOW = new Set(['transparent','currentColor']);
let bad = [];
for (const f of files) {
  const txt = fs.readFileSync(f,'utf8');
  if (/tokens-check-ignore/.test(txt)) continue; // local escape hatch comment
  let m; let flagged = false;
  while ((m = COLOR_RE.exec(txt))) {
    const color = m[2];
    if (ALLOW.has(color)) continue;
    // allow CSS vars
    if (/var\(--/.test(color)) continue;
    bad.push(`${f}:${color}`); flagged = true; break;
  }
}
if (bad.length) {
  console.error('⛔ Hardcoded colors trovati:');
  for (const l of bad) console.error(' -', l);
  process.exit(1);
}
console.log('✅ Nessun colore hardcoded.');
