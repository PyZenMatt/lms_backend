import { globby } from 'globby';
import fs from 'node:fs/promises';

// Replace `from 'react-bootstrap'` imports with our local legacy shims wrapper.
// Keeps the same named imports to minimize diff; shims internally map to new primitives or minimal Tailwind wrappers.

const files = await globby(['src/**/*.{js,jsx,ts,tsx}']);
let count = 0;
for (const f of files) {
  let txt = await fs.readFile(f, 'utf8');
  if (txt.includes("from 'react-bootstrap'")) {
    txt = txt.replace(/from 'react-bootstrap'/g, "from '@/components/ui/legacy-shims'")
             .replace(/from \"react-bootstrap\"/g, "from '@/components/ui/legacy-shims'");
    await fs.writeFile(f, txt, 'utf8');
    console.log('Updated import in', f);
    count++;
  }
}
console.log(`Done. Rewritten ${count} files.`);
