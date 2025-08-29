// src/components/ui/badge.tsx
import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "default" | "success" | "warning" | "destructive" | "muted" | "outline";
const map: Record<Variant, string> = {
  default: "bg-card text-foreground dark:bg-card dark:text-foreground",
  success: "bg-success text-success-foreground",
  warning: "bg-warning text-warning-foreground",
  destructive: "bg-destructive text-destructive-foreground",
  muted: "bg-muted text-muted-foreground dark:bg-muted dark:text-muted-foreground",
  outline: "border border-border text-foreground dark:border-border dark:text-foreground",
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
