import {glob} from 'glob';
import fs from 'fs/promises';

const FILE_GLOB = 'src/**/*.{js,jsx,ts,tsx,css,scss,sass}';
const RE_COLORS = /#[0-9a-fA-F]{3,8}\b|rgba?\([^()]*\)|hsla?\([^()]*\)|linear-gradient\([^()]*\)/g;
const RE_IN_GRAD = /#[0-9a-fA-F]{3,8}\b|rgba?\([^()]*\)|hsla?\([^()]*\)/g;

const set = new Set();

for (const file of await glob(FILE_GLOB, {ignore: ['**/node_modules/**']})) {
  const txt = await fs.readFile(file, 'utf8');
  const matches = txt.match(RE_COLORS) || [];
  for (const m of matches) {
    if (m.startsWith('linear-gradient')) {
      const inside = m.match(RE_IN_GRAD) || [];
      inside.forEach(c => set.add(c));
      set.add(m); // tieni anche la forma completa del gradient
    } else {
      set.add(m);
    }
  }
}

const list = [...set].sort((a,b)=>a.localeCompare(b));
await fs.writeFile('colors_unique.txt', list.join('\n'));
console.log(`Trovati ${list.length} colori unici → colors_unique.txt`);
