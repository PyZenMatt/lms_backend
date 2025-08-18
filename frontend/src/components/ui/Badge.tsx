import * as React from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "light";
  className?: string;
}

const variants = {
  default: "bg-muted text-muted-foreground border border-border",
  success: "bg-success text-success-foreground border border-success",
  warning: "bg-warning text-warning-foreground border border-warning",
  light: "bg-card text-card-foreground border border-border",
};

export function Badge({ variant = "default", className = "", children, ...props }: BadgeProps) {
  return (
    <span
      className={`inline-block px-2 py-1 rounded text-xs font-medium ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
