import { Page } from '@playwright/test';

/**
 * Fallisce il test su console.error/console.warn, con una lista di pattern ignorati.
 * Aggiunte CI: puoi passare stringhe/regex via env E2E_IGNORED_CONSOLE_PATTERNS (comma-separated).
 */
export function failOnConsoleErrors(page: Page, extraPatterns: Array<string | RegExp> = []) {
  const baseIgnores: Array<string | RegExp> = [
    /Viewport argument key "minimal-ui" not recognized/i,
    /downloadable font.*rejected by sanitizer/i,
    /Failed to decode downloaded font/i,
    /Source map error/i,
    /Content Security Policy/i,
    /Invalid hook call/i,
  ];

  // Legge env tipo: "/pattern1/i,noise 2,/another.*/"
  const envList = (process.env.E2E_IGNORED_CONSOLE_PATTERNS || '')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
    .map(item => {
      if (item.startsWith('/') && item.endsWith('/')) {
        const body = item.slice(1, -1);
        return new RegExp(body);
      }
      // Supporto /.../i
      const m = item.match(/^\/(.+)\/([gimsuy]*)$/);
      if (m) return new RegExp(m[1], m[2]);
      return item;
    });

  const ignores = [...baseIgnores, ...envList, ...extraPatterns];

  page.on('console', (msg) => {
    const type = msg.type();
    if (type !== 'error' && type !== 'warning') return;
    const text = msg.text();

    const isIgnored = ignores.some(p =>
      typeof p === 'string' ? text.includes(p) : p.test(text)
    );
    if (!isIgnored) {
      throw new Error(`[console.${type}] ${text}`);
    }
  });
}
