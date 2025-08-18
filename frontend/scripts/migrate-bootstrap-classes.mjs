import { globby } from 'globby';
import fs from 'node:fs/promises';

// Simple heuristic replacements for obvious bootstrap classes -> new design tokens/primitives
const REPLACERS = [
  // Buttons
  { re: /\bbtn-primary\b/g, repl: 'bg-primary text-primary-foreground' },
  { re: /\bbtn-secondary\b/g, repl: 'bg-secondary text-secondary-foreground' },
  { re: /\bbtn-danger\b/g, repl: 'bg-destructive text-destructive-foreground' },
  { re: /\bbtn-warning\b/g, repl: 'bg-warning text-warning-foreground' },
  { re: /\bbtn-info\b/g, repl: 'bg-info text-info-foreground' },
  { re: /\bbtn-success\b/g, repl: 'bg-success text-success-foreground' },
  { re: /\bbtn\b/g, repl: 'inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground' },
  // Alerts
  { re: /\balert-success\b/g, repl: 'bg-success/15 border-success text-success-foreground' },
  { re: /\balert-danger\b/g, repl: 'bg-destructive/15 border-destructive text-destructive-foreground' },
  { re: /\balert-warning\b/g, repl: 'bg-warning/15 border-warning text-warning-foreground' },
  { re: /\balert-info\b/g, repl: 'bg-info/15 border-info text-info-foreground' },
  { re: /\balert\b/g, repl: 'border rounded-md p-3 bg-muted text-muted-foreground' },
  // Badges
  { re: /\bbadge\b/g, repl: 'inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-accent text-accent-foreground' },
  // Cards
  { re: /\bcard-body\b/g, repl: 'p-4' },
  { re: /\bcard-header\b/g, repl: 'px-4 py-2 border-b border-border' },
  { re: /\bcard-footer\b/g, repl: 'px-4 py-2 border-t border-border' },
  { re: /\bcard\b/g, repl: 'bg-card text-card-foreground border border-border rounded-lg shadow-sm' },
];

const files = await globby(['src/**/*.{jsx,tsx}']);
for (const f of files) {
  let txt = await fs.readFile(f, 'utf8');
  let changed = false;
  for (const r of REPLACERS) {
    if (r.re.test(txt)) {
      txt = txt.replace(r.re, typeof r.repl === 'function' ? r.repl : r.repl);
      changed = true;
    }
  }
  if (changed) {
    await fs.writeFile(f, txt, 'utf8');
    console.log('✳︎ migrated:', f);
  }
}
console.log('Done.');
