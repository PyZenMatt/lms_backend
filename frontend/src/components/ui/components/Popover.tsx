import * as React from "react";

export interface PopoverProps {
  open: boolean;
  anchor: React.RefObject<HTMLButtonElement | null>;
  children: React.ReactNode;
}

export function Popover({ open, anchor, children }: PopoverProps) {
  if (!open || !anchor.current) return null;
  const rect = anchor.current.getBoundingClientRect();
  return (
    <div
      className="absolute z-50 bg-popover text-popover-foreground border border-border rounded shadow p-2"
      style={{ top: rect.bottom + window.scrollY, left: rect.left + window.scrollX }}
    >
      {children}
    </div>
  );
}
