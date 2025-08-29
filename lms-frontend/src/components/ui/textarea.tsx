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
            "w-full min-h-[90px] rounded-md border bg-input-background px-3 py-2 text-sm outline-none transition",
            "border-border text-foreground placeholder:text-muted-foreground",
            "focus:ring-2 focus:ring-ring focus:border-ring",
            "dark:bg-input/30 dark:text-foreground dark:border-border dark:focus:ring-ring",
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
Textarea.displayName = "Textarea";
export default Textarea;
