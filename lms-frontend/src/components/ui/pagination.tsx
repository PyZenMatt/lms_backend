// src/components/ui/pagination.tsx
import * as React from "react";
import { cn } from "@/lib/utils";

export function Pagination({
  page,
  pageCount,
  onPageChange,
  className,
}: {
  page: number; pageCount: number; onPageChange: (p:number)=>void; className?: string;
}) {
  const prev = () => onPageChange(Math.max(1, page - 1));
  const next = () => onPageChange(Math.min(pageCount, page + 1));
  const pages = React.useMemo(() => {
    const arr = new Set<number>([1, page, pageCount, page-1, page+1]);
    return [...arr].filter(n => n>=1 && n<=pageCount).sort((a,b)=>a-b);
  }, [page, pageCount]);

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <button className="rounded-xl px-3 py-1.5 text-sm border dark:border-neutral-800" onClick={prev} disabled={page<=1}>Prev</button>
      {pages.map((n, i) => {
        const sepNeeded = i>0 && n !== pages[i-1]+1;
        return (
          <React.Fragment key={n}>
            {sepNeeded ? <span className="px-1 text-neutral-400">…</span> : null}
            <button
              onClick={() => onPageChange(n)}
              className={cn(
                "rounded-xl px-3 py-1.5 text-sm border dark:border-neutral-800",
                n === page && "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900"
              )}
            >
              {n}
            </button>
          </React.Fragment>
        );
      })}
      <button className="rounded-xl px-3 py-1.5 text-sm border dark:border-neutral-800" onClick={next} disabled={page>=pageCount}>Next</button>
    </div>
  );
}
export default Pagination;
