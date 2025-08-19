// Intercept console.error and console.warn in production-like builds and forward
// them to a telemetry transport while preserving original behavior.
export function interceptConsole(send: (payload: any) => void) {
  if (typeof window === 'undefined') return;
  // Only wrap outside of dev to avoid DX friction
  if (import.meta.env.DEV) return;
  (['error', 'warn'] as const).forEach(level => {
    const original = console[level];
    console[level] = (...args: any[]) => {
      try {
        send({ type: 'console', level, args: args.map(a => (typeof a === 'string' ? a : JSON.stringify(a))), timestamp: Date.now() });
      } catch {}
      original(...args);
    };
  });
}
