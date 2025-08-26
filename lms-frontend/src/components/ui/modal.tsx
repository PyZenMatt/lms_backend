// src/components/ui/modal.tsx
import * as React from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";

type ModalCtx = { open: boolean; setOpen: (v: boolean) => void };
const Ctx = React.createContext<ModalCtx | null>(null);
function useModal() {
  const ctx = React.useContext(Ctx);
  if (!ctx) throw new Error("Modal.* must be used within <Modal>");
  return ctx;
}

export function Modal({ open: cOpen, defaultOpen, onOpenChange, children }:{
  open?: boolean; defaultOpen?: boolean; onOpenChange?: (o:boolean)=>void; children: React.ReactNode;
}) {
  const [open, setOpen] = React.useState(!!defaultOpen);
  React.useEffect(() => { if (cOpen !== undefined) setOpen(!!cOpen); }, [cOpen]);
  const api = React.useMemo<ModalCtx>(() => ({
    open, setOpen: (v) => { if (cOpen === undefined) setOpen(v); onOpenChange?.(v); }
  }), [open, cOpen, onOpenChange]);
  return <Ctx.Provider value={api}>{children}</Ctx.Provider>;
}

export function ModalTrigger({ children }: { children: React.ReactElement }) {
  const { setOpen } = useModal();
  return React.cloneElement(children, { onClick: () => setOpen(true) });
}

export function ModalContent({
  children,
  className,
  overlayClassName,
}: {
  children: React.ReactNode;
  className?: string;
  overlayClassName?: string;
}) {
  const { open, setOpen } = useModal();
  React.useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    if (open) window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, setOpen]);

  if (typeof document === "undefined") return null;
  return open
    ? createPortal(
        <div
          className={cn(
            "fixed inset-0 z-[10000] flex items-end sm:items-center justify-center p-4",
            overlayClassName
          )}
          onClick={() => setOpen(false)}
          aria-modal
          role="dialog"
        >
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-[1px]"
            aria-hidden
          />
          <div
            className={cn(
              "relative z-10 max-h-[85vh] w-full max-w-lg overflow-auto rounded-2xl border bg-white p-5 shadow-xl",
              "dark:border-neutral-800 dark:bg-neutral-950",
              className
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {children}
          </div>
        </div>,
        document.body
      )
    : null;
}

export function ModalHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mb-3", className)} {...props} />;
}
export function ModalFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mt-4 flex justify-end gap-2", className)} {...props} />;
}
