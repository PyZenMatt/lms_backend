import * as React from "react";

export interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  error?: boolean;
}

export function Label({ error = false, className = "", ...props }: LabelProps) {
  return (
    <label
      className={`block text-sm font-medium ${error ? "text-destructive" : "text-foreground"} ${className}`}
      {...props}
    />
  );
}
