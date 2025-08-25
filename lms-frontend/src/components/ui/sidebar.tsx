import * as React from "react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

/**
 * Sidebar semplice, desktop-first, con supporto "collapsed".
 * Usa i token --color-sidebar* definiti in globals.css.
 */

export type SidebarItem = {
  to?: string; // if absent, item may be an action (onClick)
  label: React.ReactNode;
  icon?: React.ReactNode;
  end?: boolean;
  onClick?: () => void;
};

export function Sidebar({
  items,
  footer,
  collapsed,
  onToggle,
  className,
}: {
  items: SidebarItem[];
  footer?: React.ReactNode;
  collapsed?: boolean;
  onToggle?: (v: boolean) => void;
  className?: string;
}) {
  return (
    <aside
      className={cn(
        "hidden h-screen shrink-0 border-r border-[--color-sidebar-border] bg-[--color-sidebar] text-[--color-sidebar-foreground] md:flex md:flex-col",
        collapsed ? "w-[72px]" : "w-64",
        className
      )}
    >
      <div className="flex h-14 items-center justify-between border-b border-[--color-sidebar-border] px-3">
        <span className={cn("text-sm font-semibold", collapsed && "sr-only")}>SchoolPlatform</span>
        <button
          type="button"
          onClick={() => onToggle?.(!collapsed)}
          className="rounded-md border border-[--color-sidebar-border] bg-[--color-sidebar-accent] px-2 py-1 text-xs text-[--color-sidebar-accent-foreground] hover:bg-[--color-sidebar-accent]/80"
          aria-label="Toggle sidebar"
        >
          {collapsed ? "›" : "‹"}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto p-2">
        <ul className="space-y-1">
          {items.map((it) => (
            <li key={String(it.to ?? it.label)}>
              {it.onClick && !it.to ? (
                // action button (e.g. Logout)
                <button
                  type="button"
                  onClick={it.onClick}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-left hover:bg-[--color-sidebar-accent]",
                    // actions don't have an active state
                    ""
                  )}
                >
                  {it.icon && <span className="grid h-5 w-5 place-items-center">{it.icon}</span>}
                  <span className={cn(collapsed && "sr-only")}>{it.label}</span>
                </button>
              ) : (
                <NavLink
                  to={it.to ?? "#"}
                  end={it.end}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-2 rounded-lg px-2 py-2 text-sm hover:bg-[--color-sidebar-accent]",
                      isActive && "bg-[--color-sidebar-accent] text-[--color-sidebar-primary]"
                    )
                  }
                >
                  {it.icon && <span className="grid h-5 w-5 place-items-center">{it.icon}</span>}
                  <span className={cn(collapsed && "sr-only")}>{it.label}</span>
                </NavLink>
              )}
            </li>
          ))}
        </ul>
      </nav>

      {footer && (
        <div className="border-t border-[--color-sidebar-border] p-2">
          <div className={cn(collapsed && "sr-only")}>{footer}</div>
        </div>
      )}
    </aside>
  );
}
