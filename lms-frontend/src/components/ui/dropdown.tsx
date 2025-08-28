// src/components/ui/dropdown.tsx
import * as React from "react";
import { cn } from "@/lib/utils";

type Ctx = { open: boolean; setOpen: React.Dispatch<React.SetStateAction<boolean>> };
const DropdownCtx = React.createContext<Ctx | null>(null);
function useD() {
  const c = React.useContext(DropdownCtx);
  if (!c) throw new Error("Dropdown.* must be used within <Dropdown>");
  return c;
}

export function Dropdown({ children }:{ children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);
  React.useEffect(() => {
    function onDoc(e: MouseEvent) {
      const target = e.target as HTMLElement | null;
      if (!target?.closest?.("[data-dd-root]")) setOpen(false);
    }
    document.addEventListener("click", onDoc);
    return () => document.removeEventListener("click", onDoc);
  }, []);
  return (
    <DropdownCtx.Provider value={{ open, setOpen }}>
      <div data-dd-root className="relative inline-block">{children}</div>
    </DropdownCtx.Provider>
  );
}

export function DropdownTrigger({ children }:{ children: React.ReactNode }) {
  const { setOpen } = useD();
  // Ensure child is a valid React element before cloning
  if (!React.isValidElement(children)) return null;
  const el = children as React.ReactElement;
  return React.cloneElement(el as React.ReactElement<any>, ({
    onClick: (e: React.MouseEvent) => {
      e.stopPropagation();
      setOpen((v: boolean) => !v);
    },
  } as any));
}

export function DropdownContent({ className, children }:{ className?: string; children: React.ReactNode }) {
  const { open } = useD();
  if (!open) return null;
  return (
    <div
      role="menu"
      className={cn(
        "absolute right-0 mt-2 w-56 rounded-2xl border bg-white p-1.5 shadow-xl",
        "dark:border-neutral-800 dark:bg-neutral-950",
        className
      )}
    >
      {children}
    </div>
  );
}

export function DropdownItem({
  children,
  onSelect,
  className,
}: {
  children: React.ReactNode;
  onSelect?: () => void;
  className?: string;
}) {
  const { setOpen } = useD();
  return (
    <button
      type="button"
      role="menuitem"
      onClick={() => { onSelect?.(); setOpen(false); }}
      className={cn(
        "w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-neutral-100",
        "dark:hover:bg-neutral-900",
        className
      )}
    >
      {children}
    </button>
  );
}
