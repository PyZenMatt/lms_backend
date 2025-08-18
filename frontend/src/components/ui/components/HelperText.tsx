import * as React from "react";

export interface HelperTextProps extends React.HTMLAttributes<HTMLParagraphElement> {
  error?: boolean;
}

export function HelperText({ error = false, className = "", ...props }: HelperTextProps) {
  return (
    <p
      className={`text-xs ${error ? "text-destructive" : "text-muted-foreground"} ${className}`}
      {...props}
    />
  );
}
