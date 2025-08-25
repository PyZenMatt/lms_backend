import * as React from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  invalid?: boolean;
};

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, prefix, suffix, invalid, disabled, ...props }, ref) => {
    return (
      <div
        className={cn(
          "group relative flex items-center rounded-lg border bg-[--color-input-background] text-foreground",
          "focus-within:ring-2 focus-within:ring-ring/50",
          disabled && "opacity-60 cursor-not-allowed",
          invalid && "border-destructive/60",
          !invalid && "border-border",
          className
        )}
      >
        {prefix && <span className="pl-3 text-muted-foreground">{prefix}</span>}
        <input
          ref={ref}
          disabled={disabled}
          className={cn(
            "w-full bg-transparent px-3 py-2 outline-none placeholder:text-muted-foreground",
            prefix ? "pl-2" : undefined,
            suffix ? "pr-2" : undefined
          )}
          {...props}
        />
        {suffix && <span className="pr-3 text-muted-foreground">{suffix}</span>}
      </div>
    );
  }
);
Input.displayName = "Input";
