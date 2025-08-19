import { describe, it, expect } from 'vitest';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import ReactDOMServer from 'react-dom/server';

// Eagerly import every view component (tsx/jsx) under src/views
// Vite will expand this at build-time.
// eslint-disable-next-line
// @ts-ignore - glob import provided by Vite
const modules: Record<string, any> = import.meta.glob('../views/**/*.{tsx,jsx}', { eager: true });

// Helper: attempt server render and capture only "invalid element" style errors.
function tryRender(name: string, Comp: any) {
  try {
    if (typeof Comp !== 'function' && typeof Comp !== 'object') {
      throw new Error('Not a valid component export');
    }
    // Components that expect props: we pass nothing; if they truly need mandatory props they will throw (acceptable for smoke test) but
    // we only flag structural invalid element errors.
    const element = (
      <MemoryRouter>
        {/* Some pages export objects; try default if object has default */}
        {React.createElement(Comp as any)}
      </MemoryRouter>
    );
    ReactDOMServer.renderToString(element);
    return null; // success
  } catch (e: any) {
    const msg = e?.message || '';
    if (/Element type is invalid/i.test(msg) || /Cannot read properties of undefined.*createElement/i.test(msg)) {
      return msg;
    }
    // Non-structural error: skip (return null so it doesn't fail undefined-component scan)
    return null;
  }
}

describe('pages smoke (undefined component detection)', () => {
  it('renders all view modules without invalid element errors', () => {
    const failures: { path: string; error: string }[] = [];

    Object.entries(modules).forEach(([path, mod]) => {
      // Prefer default export; else pick first export that looks like a component (capitalized key)
      let Comp: any = mod?.default;
      if (!Comp) {
        const candidateKey = Object.keys(mod).find(k => /^[A-Z]/.test(k) && typeof (mod as any)[k] === 'function');
        if (candidateKey) Comp = (mod as any)[candidateKey];
      }
      if (!Comp) return; // nothing to test
      const err = tryRender(path, Comp);
      if (err) failures.push({ path, error: err });
    });

    if (failures.length) {
      // Provide a helpful aggregated message
      console.error('Undefined / invalid element components found:', failures);
    }

    expect(failures).toEqual([]);
  });
});
