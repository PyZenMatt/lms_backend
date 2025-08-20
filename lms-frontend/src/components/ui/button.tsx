import React from "react"
import { cn } from "@/lib/utils"

type Variant = "default" | "secondary" | "destructive" | "ghost"

const variantMap: Record<Variant, string> = {
  default: "bg-primary text-primary-foreground hover:opacity-90",
  secondary: "bg-secondary text-secondary-foreground hover:opacity-90",
  destructive: "bg-destructive text-destructive-foreground hover:opacity-90",
  ghost: "bg-transparent hover:bg-accent text-foreground",
}

export function Button({
  className,
  variant = "default",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center px-4 py-2 rounded-md border border-border",
        "text-sm font-medium ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        variantMap[variant],
        className
      )}
      {...props}
    />
  )
}
