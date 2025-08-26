// src/components/ui/textarea.tsx
import * as React from "react";
import { cn } from "@/lib/utils";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement> & {
  invalid?: boolean;
  hint?: string;
};

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, invalid, hint, ...props }, ref) => {
    return (
      <div className="space-y-1">
        <textarea
          ref={ref}
          className={cn(
            "w-full min-h-[90px] rounded-xl border bg-white px-3 py-2 text-sm outline-none transition",
            "border-neutral-200 text-neutral-900 placeholder:text-neutral-400",
            "focus:ring-2 focus:ring-neutral-200 focus:border-neutral-300",
            "dark:bg-neutral-900 dark:text-neutral-100 dark:border-neutral-800 dark:focus:ring-neutral-800",
            invalid &&
              "border-red-300 focus:border-red-300 focus:ring-red-200 dark:border-red-600 dark:focus:ring-red-900",
            className
          )}
          {...props}
        />
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
Textarea.displayName = "Textarea";
export default Textarea;
