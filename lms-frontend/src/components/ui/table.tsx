import * as React from "react";
import { cn } from "@/lib/utils";

export const Table = ({ className, ...props }: React.TableHTMLAttributes<HTMLTableElement>) => (
  <div className="w-full overflow-x-auto">
    <table
      className={cn(
        "w-full caption-bottom text-sm border-collapse",
        "rounded-2xl overflow-hidden",
        className
      )}
      {...props}
    />
  </div>
);

export const TableHeader = ({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => (
  <thead className={cn("bg-neutral-50 text-neutral-600 dark:bg-neutral-900 dark:text-neutral-300", className)} {...props} />
);

export const TableBody = ({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => (
  <tbody className={cn("divide-y divide-neutral-100 dark:divide-neutral-800", className)} {...props} />
);

export const TableRow = ({ className, ...props }: React.HTMLAttributes<HTMLTableRowElement>) => (
  <tr
    className={cn(
      "hover:bg-neutral-50/70 dark:hover:bg-neutral-900/50 transition-colors",
      className
    )}
    {...props}
  />
);

export const TableHead = ({ className, ...props }: React.ThHTMLAttributes<HTMLTableCellElement>) => (
  <th
    className={cn(
      "px-4 py-3 text-left font-medium border-b border-neutral-200 dark:border-neutral-800",
      className
    )}
    {...props}
  />
);

export const TableCell = ({ className, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) => (
  <td className={cn("px-4 py-3 align-middle", className)} {...props} />
);

export const TableCaption = ({ className, ...props }: React.HTMLAttributes<HTMLTableCaptionElement>) => (
  <caption className={cn("mt-3 text-xs text-neutral-500 dark:text-neutral-400", className)} {...props} />
);

// Back-compat aliases for older imports
export const THead = TableHeader;
export const TBody = TableBody;
export const TR = TableRow;
export const TH = TableHead;
export const TD = TableCell;

export function TableEmpty({ children }: { children?: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-accent/30 p-4 text-center text-sm text-muted-foreground">
      {children ?? "Nessun dato disponibile"}
    </div>
  );
}
