import * as React from "react";

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "destructive";
  className?: string;
}

const variants = {
  default: "bg-muted text-muted-foreground border border-border",
  destructive: "bg-destructive text-destructive-foreground border border-destructive",
};

export function Alert({ variant = "default", className = "", children, ...props }: AlertProps) {
  return (
    <div
      className={`rounded-lg px-4 py-3 ${variants[variant]} ${className}`}
      role={variant === "destructive" ? "border rounded-md p-3 bg-muted text-muted-foreground" : undefined}
      {...props}
    >
      {children}
    </div>
  );
}
