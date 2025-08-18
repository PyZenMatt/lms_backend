// scripts/rewrite-imports.mjs
// Codemod semplice per spostamento componenti UI e aggiornamento import.
// Esempio:
//   node scripts/rewrite-imports.mjs --from styles/figma-raw --to src/components/ui --names Button,Card,Alert,Badge
import fs from 'fs';
import path from 'path';
import { glob } from 'glob';

const argv = parseArgs(process.argv.slice(2));
const fromDir = argv.from ?? 'styles/figma-raw';
const toDir = argv.to ?? 'src/components/ui';
const names = (argv.names ?? '').split(',').map(s=>s.trim()).filter(Boolean);
const root = argv.root ?? '.';
const exts = ['js','jsx','ts','tsx'];

function parseArgs(args) {
  const out = {};
  for (let i=0;i<args.length;i++) {
    const a = args[i];
    if (a.startsWith('--')) {
      const k = a.slice(2);
      const v = args[i+1] && !args[i+1].startsWith('--') ? args[i+1] : true;
      if (v !== true) i++;
      out[k] = v;
    }
  }
  return out;
}

async function main() {
  const files = await glob([`${root}/**/*.{${exts.join(',')}}`], { ignore: ['node_modules/**','dist/**','build/**'], nodir: true });
  const importRe = new RegExp(`from\\s+['"](?:\\.?\\.?/)*${fromDir.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\$&')}/(.*?)['"]`, 'g');
  let changed = 0;
  for (const f of files) {
    let txt = fs.readFileSync(f, 'utf8');
    const before = txt;
    txt = txt.replace(importRe, (m, subpath) => {
      const base = path.basename(subpath);
      const name = base.replace(/\.(jsx?|tsx?)$/, '');
      if (names.length && !names.includes(name)) return m; // skip if not in whitelist
      return `from '${path.posix.join(toDir, name)}'`;
    });
    if (txt !== before) {
      fs.writeFileSync(f, txt, 'utf8');
      console.log(`✔ Rewritten imports in ${f}`);
      changed++;
    }
  }
  console.log(`Done. Files changed: ${changed}`);
}

main().catch(e => { console.error(e); process.exit(1); });
