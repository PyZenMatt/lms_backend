import { globby } from 'globby';
import fs from 'node:fs/promises';

// Aggressive mapping Bootstrap → utility V2 (order matters: specific before generic)
const RULES = [
  { re: /\bbtn-primary\b/g, repl: 'bg-primary text-primary-foreground hover:opacity-90' },
  { re: /\bbtn-secondary\b/g, repl: 'bg-secondary text-secondary-foreground hover:opacity-90' },
  { re: /\bbtn-success\b/g, repl: 'bg-success text-success-foreground hover:opacity-90' },
  { re: /\bbtn-danger\b/g, repl: 'bg-destructive text-destructive-foreground hover:opacity-90' },
  { re: /\bbtn-warning\b/g, repl: 'bg-warning text-warning-foreground hover:opacity-90' },
  { re: /\bbtn-info\b/g, repl: 'bg-info text-info-foreground hover:opacity-90' },
  { re: /\bbtn\b/g, repl: 'inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium' },
  { re: /\balert-success\b/g, repl: 'bg-success text-success-foreground' },
  { re: /\balert-danger\b/g, repl: 'bg-destructive text-destructive-foreground' },
  { re: /\balert-warning\b/g, repl: 'bg-warning text-warning-foreground' },
  { re: /\balert-info\b/g, repl: 'bg-info text-info-foreground' },
  { re: /\balert\b/g, repl: 'border rounded-md p-3 bg-muted text-muted-foreground' },
  { re: /\bbadge\b/g, repl: 'inline-flex items-center rounded-md px-2 py-0.5 text-xs bg-accent text-accent-foreground' },
  { re: /\bcard-title\b/g, repl: 'text-base font-semibold' },
  { re: /\bcard-body\b/g, repl: 'p-4' },
  { re: /\bcard-footer\b/g, repl: 'p-4 border-t border-border' },
  { re: /\bcard-header\b/g, repl: 'p-4 border-b border-border' },
  { re: /\bcard\b/g, repl: 'bg-card text-card-foreground rounded-lg border border-border shadow-sm' },
];

const files = await globby(['src/**/*.{tsx,jsx,html}']);
for (const f of files) {
  let txt = await fs.readFile(f, 'utf8');
  const orig = txt;
  for (const r of RULES) txt = txt.replace(r.re, r.repl);
  if (txt !== orig) { await fs.writeFile(f, txt, 'utf8'); console.log('✳︎ migrated:', f); }
}
console.log('✅ Migrazione classi Bootstrap → utility V2 completata.');
