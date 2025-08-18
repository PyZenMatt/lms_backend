import { globby } from 'globby';
import fs from 'node:fs/promises';

const FROM = /from\s+["'](?:@\/components\/ui\/legacy-shims|@\/components\/legacy-shims|\.\.{1,2}\/legacy-shims(?:\.\w+)?)["']/g;

const files = await globby(['src/**/*.{ts,tsx,js,jsx}']);
let changed = 0;
for (const f of files) {
  let src = await fs.readFile(f,'utf8');
  if (FROM.test(src)) {
  src = src.replace(FROM, "from '@/components/ui/adapters/bootstrap'");
    await fs.writeFile(f, src, 'utf8');
    console.log('✳︎ migrated import:', f);
    changed++;
  }
}
console.log(`✅ legacy-shims migration done. Files updated: ${changed}`);
