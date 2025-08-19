import React from 'react';

interface Props { children: React.ReactNode }
interface State { hasError: boolean; error?: Error }

export class AppErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };
  static getDerivedStateFromError(error: Error): State { return { hasError: true, error }; }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Forward to telemetry pipeline (console acts as fallback)
    // Replace with real transport (e.g., Sentry captureException)
    console.error('UI crash:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 text-sm text-destructive">
          <h1 className="text-lg font-semibold mb-2">Qualcosa è andato storto</h1>
          <p className="mb-4">Riprova più tardi o contatta il supporto.</p>
          <button onClick={() => window.location.reload()} className="inline-flex items-center justify-center rounded-md h-9 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground">Ricarica</button>
        </div>
      );
    }
    return this.props.children;
  }
}
