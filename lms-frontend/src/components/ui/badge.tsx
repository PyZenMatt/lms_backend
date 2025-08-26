// src/components/ui/badge.tsx
import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "default" | "success" | "warning" | "destructive" | "muted" | "outline";
const map: Record<Variant, string> = {
  default: "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900",
  success: "bg-emerald-600 text-white",
  warning: "bg-amber-500 text-black",
  destructive: "bg-red-600 text-white",
  muted: "bg-neutral-200 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200",
  outline: "border border-neutral-300 text-neutral-700 dark:border-neutral-700 dark:text-neutral-200",
};

export function Badge({
  children,
  className,
  variant = "muted",
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: Variant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        map[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
export default Badge;
