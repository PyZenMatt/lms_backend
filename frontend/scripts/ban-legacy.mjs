import { globby } from 'globby';
import fs from 'node:fs/promises';

// Scan only relevant surfaces to cut false positives (variable names, component filenames).
// Only core Bootstrap tokens we must eradicate from runtime markup
const BANNED_CLASS_TOKENS = ['btn','alert','badge','modal'];
// Global patterns limited to explicit imports + lingering .scss
const BANNED_GLOBAL = [
  /react-bootstrap(?!-icons)/,
  /['"]bootstrap\//,
  /legacy-shims/,
  /\.scss\b/,
  /from\s+['"][^'"@]+@\d+(?:\.\d+){0,2}['"\n]/, // versioned import suffix
  /@\/styles\/figma-raw\/[A-Za-z].*\.(t|j)sx?/,      // figma-raw component sourcing
  /@\/components\/legacy-shims/                      // explicit legacy shim path
];

const files = await globby(['src/**/*.{ts,tsx,js,jsx,css,html}']);
const offenders = [];
for (const f of files) {
  let raw = await fs.readFile(f,'utf8');
  // Strip JS/TS single-line & block comments to avoid false positives from commented .scss lines
  if (!f.endsWith('.css')) {
    raw = raw.replace(/\/\*[\s\S]*?\*\//g,'').replace(/(^|\n)\s*\/\/.*(?=\n|$)/g,'$1');
  }
  const isCSS = f.endsWith('.css');
  // global patterns (react-bootstrap, bootstrap imports, .scss refs) always banned
  if (BANNED_GLOBAL.some(r=>r.test(raw))) { offenders.push(f); continue; }
  if (isCSS) continue; // skip raw CSS class selectors
  const classAttrRe = /(className|class)\s*=\s*(?:"([^"]*)"|'([^']*)'|`([^`]*)`)/g;
  let m; let flagged = false;
  while((m = classAttrRe.exec(raw))) {
    const val = m[2]||m[3]||m[4]||'';
    for (const token of BANNED_CLASS_TOKENS) {
      const re = new RegExp(`(^|\s)${token}(-[a-z0-9]+)?(\s|$)`);
      if (re.test(val)) { offenders.push(f); flagged = true; break; }
      // contextual variants like btn-primary, alert-success etc.
      if (/^(btn|alert|badge)/.test(token)) {
        const variantRe = new RegExp(`(^|\s)${token}-(primary|secondary|success|danger|warning|info|light|dark)(\s|$)`);
        if (variantRe.test(val)) { offenders.push(f); flagged = true; break; }
      }
    }
    if (flagged) break;
  }
}

if (offenders.length) {
  console.error('⛔ Legacy UI trovato in:');
  for (const f of offenders) console.error(' -', f);
  process.exit(1);
}
console.log('✅ Legacy UI assente.');
