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
      "flex h-10 w-full items-center gap-2 rounded-xl border bg-white px-3 text-sm outline-none transition " +
      "border-neutral-200 text-neutral-900 placeholder:text-neutral-400 " +
      "focus:ring-2 focus:ring-neutral-200 focus:border-neutral-300 " +
      "dark:bg-neutral-900 dark:text-neutral-100 dark:border-neutral-800 dark:focus:ring-neutral-800";
    const error =
      "border-red-300 focus:border-red-300 focus:ring-red-200 dark:border-red-600 dark:focus:ring-red-900";
    return (
      <div className="space-y-1">
        <div
          className={cn(
            "flex h-10 w-full items-center rounded-xl border px-3",
            invalid ? error : "border-neutral-200 dark:border-neutral-800",
            "bg-white dark:bg-neutral-900"
          )}
        >
          {prefix ? <span className="shrink-0">{prefix}</span> : null}
          <input
            ref={ref}
            type={type}
            className={cn(
              "peer w-full bg-transparent text-sm text-neutral-900 placeholder:text-neutral-400 outline-none",
              "dark:text-neutral-100",
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
              invalid ? "text-red-600 dark:text-red-400" : "text-neutral-500 dark:text-neutral-400"
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
 
