import * as React from "react";
export function Card({ className = "", ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={`bg-card text-card-foreground border border-border rounded-lg shadow ${className}`} {...props} />;
}
export function CardHeader(props: React.HTMLAttributes<HTMLDivElement>) {
  return <div className="p-4 border-b border-border" {...props} />;
}
export function CardContent(props: React.HTMLAttributes<HTMLDivElement>) {
  return <div className="p-4" {...props} />;
}
export function CardFooter(props: React.HTMLAttributes<HTMLDivElement>) {
  return <div className="p-4 border-t border-border" {...props} />;
}
