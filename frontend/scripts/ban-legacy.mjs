import { globby } from 'globby';
import fs from 'node:fs/promises';

// Regex list for banned legacy patterns (imports or class usage)
const BANNED = [
  /bootstrap(\/dist\/css\/bootstrap\.min\.css)?/,
  /react-bootstrap/,
  /\/styles\/legacy\//,
  /\/assets\/scss\//,
  /\/assets\/css\//,
  /\bbtn(-| )/, /\balert(-| )/, /\bbadge(-| )/, /\bcard(-| )/
];

const files = await globby(['src/**/*.{ts,tsx,js,jsx,css,scss}']);
let errors = [];
for (const f of files) {
  const txt = await fs.readFile(f, 'utf8');
  for (const re of BANNED) {
    if (re.test(txt)) { errors.push(`${f} :: ${re}`); break; }
  }
}
if (errors.length) {
  console.error('❌ Legacy UI rilevato:\n' + errors.join('\n'));
  process.exit(1);
} else {
  console.log('✅ Nessun riferimento legacy trovato.');
}
