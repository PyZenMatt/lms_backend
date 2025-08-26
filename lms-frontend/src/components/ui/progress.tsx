import * as React from "react";
import { cn } from "@/lib/utils";

export function Progress({ value = 0, max = 100, className }:{
  value?: number; max?: number; className?: string;
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className={cn("h-2 w-full rounded-full bg-neutral-200 dark:bg-neutral-800", className)}>
      <div
        className="h-full rounded-full bg-neutral-900 dark:bg-neutral-100 transition-all"
        style={{ width: `${pct}%` }}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={Math.round(pct)}
        role="progressbar"
      />
    </div>
  );
}
