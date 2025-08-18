import * as React from "react";

import { cn } from "./utils";

function Card({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="bg-card text-card-foreground rounded-lg border border-border shadow-sm"
      className={cn(
        "bg-bg-card text-card-foreground rounded-lg border border-border shadow-sm text-bg-card text-card-foreground rounded-lg border border-border shadow-sm-foreground border border-border rounded-lg shadow-sm flex flex-col gap-6 rounded-xl",
        className,
      )}
      {...props}
    />
  );
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="p-4 border-b border-border"
      className={cn(
        "px-6 pt-6 pb-0 border-b border-border grid auto-rows-min grid-rows-[auto_auto] items-start gap-1.5",
        className,
      )}
      {...props}
    />
  );
}

function CardTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
  <h4 data-slot="text-base font-semibold" className={cn("leading-none", className)} {...props} />
  );
}

function CardDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
  <p data-slot="bg-card text-card-foreground rounded-lg border border-border shadow-sm-description" className={cn("text-muted-foreground", className)} {...props} />
  );
}

function CardAction({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="bg-card text-card-foreground rounded-lg border border-border shadow-sm-action"
      className={cn("col-start-2 row-span-2 row-start-1 self-start justify-self-end", className)}
      {...props}
    />
  );
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
  <div data-slot="bg-card text-card-foreground rounded-lg border border-border shadow-sm-content" className={cn("px-6 [&:last-child]:pb-6", className)} {...props} />
  );
}

function CardFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="px-4 py-2 border-t border-border"
      className={cn("flex items-center px-6 pb-6 [.border-t]:pt-6", className)}
      {...props}
    />
  );
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
};
