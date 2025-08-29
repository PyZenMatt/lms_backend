import * as React from "react";
import { Button as FigmaButton } from "@/components/figma/ui/button";
import { cn } from "@/components/figma/ui/utils";

export type ButtonProps = React.ComponentProps<typeof FigmaButton>;

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button({ className, ...props }, ref) {
  // Ensure a consistent focus ring and allow call-site className to extend/override
  return <FigmaButton ref={ref} className={cn("focus-visible:ring-ring/50 focus-visible:ring-2", className)} {...props} />;
});

export default Button;
