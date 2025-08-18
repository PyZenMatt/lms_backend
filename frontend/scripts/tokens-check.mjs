// scripts/tokens-check.mjs
// Scan the codebase for hardcoded colors and fail if found (unless in allowlist).
// Usage: node scripts/tokens-check.mjs --root src --allow "hsl(var(--...),var(--...))" --ignore "README.md,**/*.svg"
import fs from 'fs';
import { glob } from 'glob';

const argv = parseArgs(process.argv.slice(2));
const root = argv.root ?? 'src';
const ignore = (argv.ignore ?? [
  'node_modules/**',
  'dist/**',
  'build/**',
  'src/styles/tokens.css',
  'src/styles/themes/**/*',
  'src/styles/legacy/**/*',
  'src/assets/scss/partials/font/_fontawesome.scss'
].join(',')).split(',').map(s=>s.trim()).filter(Boolean);
const allow = new Set((argv.allow ?? '').split(',').map(s=>s.trim()).filter(Boolean));

function parseArgs(args) {
  const out = {};
  for (let i=0;i<args.length;i++) {
    const a = args[i];
    if (a.startsWith('--')) {
      const k = a.slice(2);
      const v = args[i+1] && !args[i+1].startsWith('--') ? (args[i+1]) : true;
      if (v !== true) i++;
      out[k] = v;
    }
  }
  return out;
}

const COLOR_PATTERNS = [
  /#[0-9a-fA-F]{3,8}\b/g,
  /\brgba?\([^()]+\)/gi,
  /\bhsla?\([^()]+\)/gi,
  // common named colors that sneak in
  /\b(white|black|red|green|blue|orange|yellow|purple|gray|grey|silver|gold)\b/gi
];

function findColors(text) {
  const found = new Set();
  for (const r of COLOR_PATTERNS) {
    const m = text.match(r) || [];
    for (const s of m) {
      if (!allow.has(s)) found.add(s);
    }
  }
  return Array.from(found);
}

async function main() {
  const patterns = [`${root}/**/*.{css,scss,js,jsx,ts,tsx}`];
  const files = await glob(patterns, { ignore, nodir: true });
  const offenders = {};
  for (const f of files) {
    const txt = fs.readFileSync(f, 'utf8');
    const colors = findColors(txt);
    if (colors.length) offenders[f] = colors.sort();
  }
  if (Object.keys(offenders).length) {
    console.error('Found hardcoded colors in files:');
    for (const [f, cols] of Object.entries(offenders)) {
      console.error(`- ${f}`);
      for (const c of cols) console.error(`   • ${c}`);
    }
    process.exit(1);
  } else {
    console.log('No hardcoded colors found. ✅');
  }
}

main().catch(err => { console.error(err); process.exit(2); });
