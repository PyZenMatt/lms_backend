import { globby } from "globby";
import fs from "node:fs/promises";

const RB_TO_UI = {
  Button: "Button",
  Alert: "Alert",
  Badge: "Badge",
  Card: "Card",
  Modal: "Dialog",
};

const DIALOG_PARTS = [
  { from: /\.Modal\.Header\b/g, to: ".DialogHeader" },
  { from: /\.Modal\.Title\b/g,  to: ".DialogTitle"  },
  { from: /\.Modal\.Body\b/g,   to: ".DialogContent"},
  { from: /\.Modal\.Footer\b/g, to: ".DialogFooter" },
];

function rewriteImports(src) {
  if (!/from\s+["']react-bootstrap["']/.test(src)) return src;
  const m = src.match(/import\s+{([^}]+)}\s+from\s+["']react-bootstrap["'];?/);
  if (!m) return src;
  const names = m[1].split(",").map(s => s.trim()).filter(Boolean);
  const uiImports = names
    .map(n => n.replace(/\s+as\s+.*/,""))
    .filter(n => RB_TO_UI[n]);
  if (uiImports.length === 0) {
    src = src.replace(m[0], "// TODO: react-bootstrap import rimosso (non mappato)\n");
    return src;
  }
  src = src.replace(m[0], "");
  const add = `import { ${[...new Set(uiImports.map(n => RB_TO_UI[n]))].join(", ")} } from "@/components/ui";\n`;
  src = add + src;
  return src;
}

function rewriteModalUsage(src) {
  if (!/Modal\b/.test(src)) return src;
  src = src
    .replace(/<\s*Modal(\s+[^>]*)?>/g, (m, attrs='') => {
      const open = /\bshow={(.*?)}|open={(.*?)}/.exec(attrs);
      const onClose = /\bonHide={(.*?)}/.exec(attrs);
      let replaced = `<Dialog${open ? ` open={${open[1] || open[2]}}` : ""}${onClose ? ` onOpenChange={${onClose[1]}}` : ""}>`;
      return replaced;
    })
    .replace(/<\/\s*Modal\s*>/g, "</Dialog>");
  for (const p of DIALOG_PARTS) src = src.replace(p.from, p.to);
  if (/<\s*Modal\./.test(src)) {
    src = "// TODO: Verifica mapping sottocomponenti Modal\n" + src;
  }
  return src;
}

const files = await globby(["src/**/*.{tsx,jsx}"]);
for (const f of files) {
  let txt = await fs.readFile(f, "utf8");
  const orig = txt;
  txt = rewriteImports(txt);
  txt = rewriteModalUsage(txt);
  if (txt !== orig) { await fs.writeFile(f, txt, "utf8"); console.log("✳︎ codemodded:", f); }
}
console.log("✅ Codemod react-bootstrap → ui completato.");
