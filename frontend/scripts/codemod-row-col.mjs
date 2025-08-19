#!/usr/bin/env node
import { globby } from 'globby';
import fs from 'node:fs/promises';

// Codemod: replace <Row>/<Col> bootstrap-like grid with Tailwind CSS grid utilities.
// Heuristics: <Row className="..."> -> <div className="grid grid-cols-12 gap-4 ...">
// <Col xs={12} md={6} lg={4} className="foo"> -> <div className="col-span-12 md:col-span-6 lg:col-span-4 foo">
// Removes Row, Col from barrel imports.

const files = await globby(['src/**/*.{jsx,tsx}']);
const rowRe = /<Row(\s+[^>]*)?>/g;
const rowCloseRe = /<\/Row>/g;
const importRe = /(import\s+[^;]*from\s+['"]@\/components\/ui['"];?)/g;

let changed = 0;

for (const f of files) {
  let code = await fs.readFile(f,'utf8');
  if (!/\bRow\b|\bCol\b/.test(code)) continue;
  let original = code;
  // Adjust import: remove Row/Col specifiers
  code = code.replace(importRe, m => {
    // remove Row and Col inside curly braces
    return m.replace(/\{([^}]*)\}/, (mm, inside) => {
      const updated = inside.split(',').map(s=>s.trim()).filter(Boolean).filter(x=>x!=='Row' && x!=='Col').join(', ');
      return updated ? `{ ${updated} }` : '';
    });
  });

  // Transform <Row ...>
  code = code.replace(rowRe, (match, attrs='') => {
    // Extract className value if present
    const classMatch = attrs.match(/className=\"([^\"]*)\"|className=\'([^\']*)\'|className={`([^`}]*)`}/);
    let cls = 'grid grid-cols-12 gap-4';
    if (classMatch) {
      const val = classMatch[1]||classMatch[2]||classMatch[3]||'';
      cls += ' ' + val;
      // remove original className attr
      attrs = attrs.replace(/className=({`[^`]*`}|"[^"]*"|'[^']*')/,'').trim();
    }
    // Remove leftover leading/trailing
    return `<div className="${cls.trim()}"${attrs? ' '+attrs: ''}>`;
  });
  code = code.replace(rowCloseRe, '</div>');

  // Transform <Col ...>
  // We'll capture attributes, build class additions, then output div
  code = code.replace(/<Col(\s+[^>]*)?>/g, (match, attrs='') => {
    const bp = { xs:12 };
    const attrMap = {};
    (['xs','sm','md','lg','xl']).forEach(k=>{
      const m = attrs.match(new RegExp(k+"=\\{(\\d+)\\}"));
      if (m) { attrMap[k]=m[1]; }
    });
    let className = 'col-span-12';
    Object.entries(attrMap).forEach(([k,v])=>{
      if (k==='xs') { className = `col-span-${v}`; return; }
      className += ` ${k}:col-span-${v}`;
    });
    const classMatch = attrs.match(/className=\"([^\"]*)\"|className=\'([^\']*)\'|className={`([^`}]*)`}/);
    if (classMatch) {
      const val = classMatch[1]||classMatch[2]||classMatch[3]||'';
      className += ' ' + val;
      attrs = attrs.replace(/className=({`[^`]*`}|"[^"]*"|'[^']*')/,'');
    }
    // Remove breakpoint attrs
    attrs = attrs.replace(/\b(xs|sm|md|lg|xl)=\{\d+\}/g,'').replace(/\s+/g,' ').trim();
    return `<div className="${className.trim()}"${attrs? ' '+attrs: ''}>`;
  });
  code = code.replace(/<\/Col>/g,'</div>');

  if (code !== original) {
    await fs.writeFile(f,code,'utf8');
    changed++;
  }
}

console.log(`Row/Col codemod applied to ${changed} file(s).`);
