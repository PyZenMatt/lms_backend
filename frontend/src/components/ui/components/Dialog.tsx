import * as React from "react";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

export function Dialog({ open, onClose, children }: DialogProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card text-card-foreground rounded-lg shadow-lg p-6 min-w-[320px]">
        {children}
        <button className="mt-4 text-sm text-primary" onClick={onClose}>Chiudi</button>
      </div>
    </div>
  );
}
