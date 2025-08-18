// scripts/tokenize-css.mjs
// Usage:
//   node scripts/tokenize-css.mjs --root src --mapping scripts/color-mapping.js --ext css,scss,js,jsx,ts,tsx --write
// Flags:
//   --dry-run (default): no writes, only report
//   --write: actually overwrite files
//   --report <path>: write JSON report with stats (default: stdout only)
//   --ignore "<glob1,glob2>": comma-separated ignore globs
//   --case-insensitive: also match uppercased HEX etc.
//
// Notes:
// - Longest patterns are applied first (so complete gradients are replaced before single colors).
// - For rgba()/hsl() forms the matcher is whitespace-tolerant and accepts `.1` or `0.1` alpha.
import fs from 'fs';
import path from 'path';
import url from 'url';
import { glob } from 'glob';

const argv = processArgs(process.argv.slice(2));
const root = argv.root ?? 'src';
const mappingFile = argv.mapping ?? 'scripts/color-mapping.js';
const exts = (argv.ext ?? 'css,scss,js,jsx,ts,tsx').split(',').map(s => s.trim()).filter(Boolean);
const ignore = (argv.ignore ?? [
  'node_modules/**',
  'dist/**',
  'build/**',
  'src/styles/tokens.css',
  'src/styles/themes/**/*',
  'src/styles/legacy/**/*',
  'src/assets/scss/partials/font/_fontawesome.scss'
].join(',')).split(',').map(s => s.trim()).filter(Boolean);
const dryRun = !argv.write;
const caseInsensitive = Boolean(argv['case-insensitive']);
const reportPath = argv.report ?? null;

function processArgs(args) {
  const out = {};
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = args[i + 1];
      if (next && !next.startsWith('--')) { out[key] = next; i++; }
      else out[key] = true;
    }
  }
  return out;
}

function toCanonicalHex(hex) {
  // Normalize to lowercase #rrggbb
  let h = hex.toLowerCase();
  if (/^#[0-9a-f]{3}$/.test(h)) {
    h = '#' + h[1] + h[1] + h[2] + h[2] + h[3] + h[3];
  }
  return h;
}

function expandVariants(key) {
  const variants = new Set([key]);
  // HEX variants
  if (/^#[0-9a-fA-F]{3,6}$/.test(key)) {
    variants.add(toCanonicalHex(key));
    variants.add(toCanonicalHex(key).toUpperCase());
  }
  // rgba()/rgb() variants – tolerate spaces and .x vs 0.x
  if (/^rgba?\(/i.test(key) || /^hsla?\(/i.test(key)) {
      const loose = key
        .replace(/\s+/g, '')
        .replace(/,0\./g, ',.')
        .replace(/\)/g, '\\s*\\)');
    // Rebuild a tolerant regex from the compact form
    // Insert optional spaces after commas and around numbers
    const tolerant = loose 
      .replace(/,/g, '\\s*,\\s*') 
      .replace(/\(/, '\\(') 
      .replace(/\\s\*\\\)/, '\\s*\\)'); // ensure closing )
    variants.add({ regex: new RegExp(tolerant, 'gi') });
  }
  // linear-gradient / radial-gradient: make a whitespace-tolerant regex
  if (/gradient\(/i.test(key)) {
    const escaped = key
      .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      .replace(/\\,\\ /g, '\\s*,\\s*') // tolerate commas + spaces
      .replace(/\s+/g, '\\s*'); // any whitespace becomes optional
    variants.add({ regex: new RegExp(escaped, 'gi') });
  }
  return Array.from(variants);
}

function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function loadMapping(filePath) {
  // Support JS module exporting "mapping" or default, and JSON file with an object
  const abs = path.isAbsolute(filePath) ? filePath : path.join(process.cwd(), filePath);
  if (!fs.existsSync(abs)) {
    throw new Error(`Mapping file not found: ${abs}`);
  }
  if (abs.endsWith('.json')) {
    const obj = JSON.parse(fs.readFileSync(abs, 'utf8'));
    return obj;
  }
  // ESM import from file path
  const fileUrl = url.pathToFileURL(abs).href;
  return import(fileUrl).then(mod => {
    if (mod.mapping) return mod.mapping;
    if (mod.default) return mod.default;
    throw new Error('Mapping JS must export "mapping" or default object');
  });
}

function buildMatchers(mapping, caseInsensitive=false) {
  // Return array of {match: RegExp, replacement: string, key: string, isRegex: boolean}
  // Longer keys first to prefer phrase replacements before single colors
  const entries = Object.entries(mapping).sort((a,b) => b[0].length - a[0].length);
  const matchers = [];
  for (const [raw, replacement] of entries) {
    const expanded = expandVariants(raw);
    for (const v of expanded) {
      if (typeof v === 'string') {
        const flags = caseInsensitive ? 'gi' : 'g';
        matchers.push({ match: new RegExp(escapeRegex(v), flags), replacement, key: raw, isRegex: false });
      } else if (v && v.regex) {
        matchers.push({ match: v.regex, replacement, key: raw, isRegex: true });
      }
    }
  }
  return matchers;
}

function fileGlobs() {
  const patterns = exts.map(ext => `${root.replace(/\/+$/,'')}/**/*.${ext}`);
  return { patterns, ignore };
}

function replaceInContent(content, matchers, stats) {
  let out = content;
  for (const m of matchers) {
    let before = out;
    out = out.replace(m.match, () => {
      stats.replacements[m.key] = (stats.replacements[m.key] || 0) + 1;
      return m.replacement;
    });
    if (before !== out) stats.touchedMatchers.add(m.key);
  }
  return out;
}

function collectUnmapped(content, mapping) {
  const set = new Set();
  // Basic patterns for colors not yet tokenized
  const patterns = [
    /#[0-9a-fA-F]{3,8}\b/g,
    /\brgba?\([^()]+\)/gi,
    /\bhsla?\([^()]+\)/gi
  ];
  for (const p of patterns) {
    const matches = content.match(p) || [];
    for (const m of matches) {
      // Skip if already mapped
      const canon = m.toLowerCase().replace(/\s+/g,'');
      let known = false;
      for (const key of Object.keys(mapping)) {
        const canonKey = key.toLowerCase().replace(/\s+/g,'');
        if (canon === canonKey) { known = true; break; }
      }
      if (!known) set.add(m);
    }
  }
  return Array.from(set);
}

async function main() {
  const mapping = await loadMapping(mappingFile);
  const matchers = buildMatchers(mapping, caseInsensitive);
  const { patterns, ignore } = fileGlobs();

  const files = await glob(patterns, { ignore, nodir: true, withFileTypes: false });
  if (files.length === 0) {
    console.error(`No files found in ${root} with extensions: ${exts.join(', ')}`);
    process.exit(2);
  }
  const stats = {
    scanned: 0,
    modified: 0,
    replacements: {},
    files: {},
    unmapped: {}
  };

  for (const file of files) {
    let content = fs.readFileSync(file, 'utf8');
    const original = content;

    content = replaceInContent(content, matchers, { replacements: stats.replacements, touchedMatchers: new Set() });

    if (content !== original) {
      stats.modified++;
      if (!dryRun) fs.writeFileSync(file, content, 'utf8');
      stats.files[file] = stats.files[file] || {};
      stats.files[file].modified = true;
    }
    // Always collect unmapped for the report
    const um = collectUnmapped(content, mapping);
    if (um.length) stats.unmapped[file] = um;
    stats.scanned++;
  }

  const summary = {
    root,
    dryRun,
    modified: stats.modified,
    scanned: stats.scanned,
    totalReplacements: Object.values(stats.replacements).reduce((a,b)=>a+b,0),
    byToken: stats.replacements,
    filesModified: Object.keys(stats.files).length,
    unmappedByFile: stats.unmapped
  };

  if (reportPath) {
    fs.writeFileSync(reportPath, JSON.stringify(summary, null, 2));
    console.log(`Report written to ${reportPath}`);
  } else {
    console.log(JSON.stringify(summary, null, 2));
  }

  // Exit non-zero if there are unmapped colors (useful for CI guardrails)
  if (Object.keys(summary.unmappedByFile).length > 0) {
    process.exitCode = 3;
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
