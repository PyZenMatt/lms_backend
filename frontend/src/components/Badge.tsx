import * as React from "react";
type Variant = "default" | "secondary" | "accent" | "destructive" | "outline";
const map: Record<Variant, string> = {
  default: "bg-primary text-primary-foreground",
  secondary: "bg-secondary text-secondary-foreground",
  accent: "bg-accent text-accent-foreground",
  destructive: "bg-destructive text-destructive-foreground",
  outline: "border border-border",
};
export function Badge({ variant = "default", className = "", ...props }: React.HTMLAttributes<HTMLSpanElement> & { variant?: Variant }) {
  return <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs ${map[variant]} ${className}`} {...props} />;
}
