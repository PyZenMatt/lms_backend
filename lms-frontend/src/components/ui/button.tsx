import * as React from "react";

type Variant = "primary" | "secondary" | "outline" | "ghost" | "destructive" | "link";
type Size = "sm" | "md" | "lg" | "icon";

function cx(...classes: Array<string | undefined | false | null>) {
  return classes.filter(Boolean).join(" ");
}

const variantClass: Record<Variant, string> = {
  primary:    "bg-primary text-primary-foreground hover:bg-primary/90",
  secondary:  "bg-secondary text-secondary-foreground hover:bg-secondary/80",
  outline:    "border border-input bg-background text-foreground hover:bg-accent",
  ghost:      "bg-transparent hover:bg-accent",
  destructive:"bg-destructive text-destructive-foreground hover:bg-destructive/90",
  link:       "bg-transparent underline-offset-4 text-primary hover:underline"
};

const sizeClass: Record<Size, string> = {
  sm:   "h-8 px-3 text-sm",
  md:   "h-9 px-4",
  lg:   "h-10 px-6 text-base",
  icon: "h-9 w-9 p-0"
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cx(
          "inline-flex items-center justify-center rounded-md font-medium transition",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          sizeClass[size],
          variantClass[variant],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export default Button;
