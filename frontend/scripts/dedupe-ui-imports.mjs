import { globby } from "globby";
import fs from "node:fs/promises";

const COMPONENTS = [
  "button","card","alert","badge","dialog","dropdown-menu","tooltip","tabs",
  "accordion","checkbox","select","input-otp","slider","switch","sonner",
  "sidebar","pagination","sheet","popover","separator","radio-group",
  "menubar","navigation-menu","scroll-area","progress","form","breadcrumb",
  "calendar","carousel","chart","label","toggle","toggle-group","resizable",
];

const BAD_SOURCES = [
  '@/components/ui/components/ui',
  '@/styles/figma-raw',
  '@/components/legacy-shims',
  '@\\/components\\/legacy-shims',
];

const files = await globby(["src/**/*.{ts,tsx,js,jsx}"]);
let count = 0;
for (const f of files) {
  let code = await fs.readFile(f, "utf8");
  const before = code;

  for (const c of COMPONENTS) {
    const rxA = new RegExp(`from\\s+["']@\\/components\\/ui\\/components\\/ui\\/${c}["']`, "g");
    const rxB = new RegExp(`from\\s+["']@\\/components\\/ui\\/${c}["']`, "g");
    code = code.replace(rxA, 'from "@/components/ui"');
    code = code.replace(rxB, 'from "@/components/ui"');
  }

  code = code.replace(/from\s+["']@\/styles\/figma-raw\/[^"']+["']/g, 'from "@/components/ui"');
  code = code.replace(/from\s+["']@\/components\/legacy-shims["']/g, 'from "@/components/ui"');

  for (const bad of BAD_SOURCES) {
    const rx = new RegExp(`from\\s+["']${bad}[^"']*["']`, "g");
    code = code.replace(rx, 'from "@/components/ui"');
  }

  if (code !== before) {
    await fs.writeFile(f, code, "utf8");
    console.log("✳︎ deduped:", f);
    count++;
  }
}
console.log(`✅ dedupe-ui-imports done. Files updated: ${count}`);
