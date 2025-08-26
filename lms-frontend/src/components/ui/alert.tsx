// src/components/ui/alert.tsx
import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "info" | "success" | "warning" | "error";
const vmap: Record<Variant, string> = {
  info: "border-neutral-200 bg-neutral-50 text-neutral-800 dark:border-neutral-800 dark:bg-neutral-900/40 dark:text-neutral-100",
  success: "border-emerald-300/60 bg-emerald-50 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-200",
  warning: "border-amber-300/70 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-100",
  error: "border-red-300/70 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-900/20 dark:text-red-100",
};

export function Alert({
  title,
  children,
  variant = "info",
  className,
}: {
  title?: string;
  children?: React.ReactNode;
  variant?: Variant;
  className?: string;
}) {
  return (
    <div className={cn("rounded-2xl border p-4 text-sm", vmap[variant], className)} role="status">
      {title ? <div className="mb-1 font-medium">{title}</div> : null}
      {children}
    </div>
  );
}
export default Alert;
