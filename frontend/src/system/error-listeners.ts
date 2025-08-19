export function installGlobalErrorListeners(send: (payload: any) => void) {
  if (typeof window === 'undefined') return;
  window.addEventListener('error', (e) => {
    send({ type: 'error', message: e.message, stack: (e as any).error?.stack || null, timestamp: Date.now() });
  });
  window.addEventListener('unhandledrejection', (e: PromiseRejectionEvent) => {
    send({ type: 'unhandledrejection', reason: String(e.reason), timestamp: Date.now() });
  });
}
