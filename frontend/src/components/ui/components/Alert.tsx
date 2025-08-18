import * as React from "react";
type Tone = "info" | "success" | "warning" | "destructive";
const tones: Record<Tone, string> = {
  info: "bg-accent text-accent-foreground",
  success: "bg-secondary text-secondary-foreground",
  warning: "bg-muted text-foreground",
  destructive: "bg-destructive text-destructive-foreground",
};
export function Alert({ tone = "info", className = "", ...props }: React.HTMLAttributes<HTMLDivElement> & { tone?: Tone }) {
  return <div role="status" className={`rounded-md px-3 py-2 ${tones[tone]} ${className}`} {...props} />;
}
