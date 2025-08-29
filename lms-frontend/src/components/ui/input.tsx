import * as React from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  invalid?: boolean;
  hint?: string;
};

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", prefix, suffix, invalid, hint, ...props }, ref) => {
    const base =
      "flex h-10 w-full items-center gap-2 rounded-md border bg-input-background px-3 text-sm outline-none transition " +
      "border-border text-foreground placeholder:text-muted-foreground " +
      "focus:ring-2 focus-visible:shadow-focus focus:border-ring " +
      "dark:bg-input/30 dark:text-foreground";
    const error =
      "border-red-300 focus:border-red-300 focus:ring-red-200 dark:border-red-600 dark:focus:ring-red-900";
    return (
      <div className="space-y-1">
        <div
          className={cn(
            "flex h-10 w-full items-center rounded-md border px-3",
            invalid ? error : "border-border dark:border-border",
            "bg-input-background dark:bg-input/30"
          )}
        >
          {prefix ? <span className="shrink-0">{prefix}</span> : null}
          <input
            ref={ref}
            type={type}
            className={cn(
              "peer w-full bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none",
              "dark:text-foreground",
              className
            )}
            {...props}
          />
          {suffix ? <span className="shrink-0">{suffix}</span> : null}
        </div>
        {hint ? (
          <p
            className={cn(
              "text-xs",
              invalid ? "text-red-600 dark:text-red-400" : "text-muted-foreground"
            )}
          >
            {hint}
          </p>
        ) : null}
      </div>
    );
  }
);
Input.displayName = "Input";

export default Input;
 
