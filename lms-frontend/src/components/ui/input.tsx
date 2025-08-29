import * as React from "react";
import { Input as FigmaInput } from "@/components/figma/ui/input";
import { cn } from "@/components/figma/ui/utils";

export type InputProps = React.ComponentProps<typeof FigmaInput>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  function Input({ className, ...props }, ref) {
    return (
      <FigmaInput
        ref={ref}
        className={cn(
          "focus-visible:ring-ring/50 focus-visible:ring-2 border-border rounded-md bg-input-background text-foreground placeholder:text-muted-foreground",
          className,
        )}
        {...props}
      />
    );
  }
);
export default Input;
