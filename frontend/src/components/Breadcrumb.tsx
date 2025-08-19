import * as React from "react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumb({ items, className = "" }: BreadcrumbProps) {
  return (
    <nav className={`flex items-center space-x-2 text-sm ${className}`} aria-label="breadcrumb">
      {items.map((item, idx) => (
        <React.Fragment key={item.label}>
          {item.href ? (
            <a href={item.href} className="text-primary hover:underline">{item.label}</a>
          ) : (
            <span className="text-muted-foreground">{item.label}</span>
          )}
          {idx < items.length - 1 && <span className="mx-1">/</span>}
        </React.Fragment>
      ))}
    </nav>
  );
}
