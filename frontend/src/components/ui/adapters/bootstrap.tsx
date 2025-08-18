"use client";

import * as React from "react";
import { cn } from "@/components/ui";
import {
  Button,
  Dialog,
  Tooltip,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  Tabs,
} from "@/components/ui";
import { Loader2 } from "lucide-react";

/* ----------------------------- Layout: Container/Row/Col ----------------------------- */

export function Container({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8", className)} {...props} />;
}
export function Row({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("grid grid-cols-12 gap-4", className)} {...props} />;
}
type ColProps = React.HTMLAttributes<HTMLDivElement> & { xs?: number; sm?: number; md?: number; lg?: number };
export function Col({ xs = 12, sm, md, lg, className, ...props }: ColProps) {
  const cls = cn(
    `col-span-${xs}`,
    sm && `sm:col-span-${sm}`,
    md && `md:col-span-${md}`,
    lg && `lg:col-span-${lg}`,
    className,
  );
  return <div className={cls} {...props} />;
}

/* -------------------------------------- Table --------------------------------------- */

type TableProps = React.TableHTMLAttributes<HTMLTableElement> & {
  striped?: boolean; bordered?: boolean; hover?: boolean; size?: "sm" | "lg";
};
export function Table({ striped, bordered, hover, size, className, ...props }: TableProps) {
  return (
    <table
      className={cn(
        "min-w-full border-collapse text-sm",
        bordered && "border border-border",
        className,
      )}
      {...props}
    />
  );
}
export const Thead = (p: React.HTMLAttributes<HTMLTableSectionElement>) =>
  <thead className={cn("[&_th]:text-muted-foreground", p.className)} {...p} />;
export const Tbody = (p: React.HTMLAttributes<HTMLTableSectionElement>) => <tbody {...p} />;
export const Tr = (p: React.HTMLAttributes<HTMLTableRowElement>) =>
  <tr className={cn("hover:bg-muted/40", p.className)} {...p} />;
export const Th = (p: React.ThHTMLAttributes<HTMLTableHeaderCellElement>) =>
  <th className={cn("border-b border-border px-3 py-2 text-left font-medium", p.className)} {...p} />;
export const Td = (p: React.TdHTMLAttributes<HTMLTableCellElement>) =>
  <td className={cn("border-b border-border px-3 py-2", p.className)} {...p} />;

/* ----------------------------------- ProgressBar ------------------------------------ */

type ProgressBarProps = { now?: number; label?: React.ReactNode } & React.HTMLAttributes<HTMLDivElement>;
export function ProgressBar({ now = 0, label, className, ...props }: ProgressBarProps) {
  const pct = Math.max(0, Math.min(100, now));
  return (
    <div className={cn("bg-muted relative h-2 w-full overflow-hidden rounded", className)} {...props}>
      <div className="bg-primary absolute left-0 top-0 h-full rounded" style={{ width: `${pct}%` }} />
      {label && <span className="sr-only">{label}</span>}
    </div>
  );
}

/* -------------------------------------- Spinner ------------------------------------- */

export function Spinner({ className, ...props }: React.HTMLAttributes<SVGSVGElement>) {
  return <Loader2 className={cn("animate-spin", className)} {...props} />;
}

/* ------------------------------------- ListGroup ------------------------------------ */

export function ListGroup({ className, ...props }: React.HTMLAttributes<HTMLUListElement>) {
  return <ul className={cn("divide-y divide-border rounded border border-border bg-card", className)} {...props} />;
}
export function ListGroupItem({ className, ...props }: React.LiHTMLAttributes<HTMLLIElement>) {
  return <li className={cn("bg-card px-4 py-2 text-card-foreground", className)} {...props} />;
}

/* -------------------------------------- Dropdown ------------------------------------ */

type DropdownProps = { label?: React.ReactNode; children?: React.ReactNode } & React.HTMLAttributes<HTMLDivElement>;
export function Dropdown({ label, children, className }: DropdownProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className={className}>{label}</Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">{children}</DropdownMenuContent>
    </DropdownMenu>
  );
}
export function DropdownItem(
  { onSelect, children, className }: { onSelect?: () => void } & React.HTMLAttributes<HTMLDivElement>,
) {
  return (
    <DropdownMenuItem className={className} onSelect={(e) => { e.preventDefault(); onSelect?.(); }}>
      {children}
    </DropdownMenuItem>
  );
}

/* -------------------------------------- InputGroup ---------------------------------- */

export function InputGroup({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex items-stretch gap-2", className)} {...props} />;
}
export const FormControl = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "bg-background text-foreground ring-offset-background placeholder:text-muted-foreground",
        "border-input focus-visible:ring-ring h-9 w-full rounded-md border px-3 py-1 text-sm",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        className,
      )}
      {...props}
    />
  ),
);
FormControl.displayName = "FormControl";

/* ---------------------------------------- Modal ------------------------------------- */
// API compat: <Modal show onHide> + children: <ModalHeader><ModalTitle/></ModalHeader><ModalBody/><ModalFooter/>

type ModalProps = { show?: boolean; onHide?: (open: boolean) => void } & React.HTMLAttributes<HTMLDivElement>;
export function Modal({ show, onHide, children }: ModalProps) {
  return (
    <Dialog open={!!show} onOpenChange={(open) => onHide?.(open)}>
      {children}
    </Dialog>
  );
}
export const ModalHeader = ({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) =>
  <div className={cn("mb-2", className)} {...p} />;
export const ModalTitle = ({ className, ...p }: React.HTMLAttributes<HTMLHeadingElement>) =>
  <h3 className={cn("text-lg font-semibold", className)} {...p} />;
export const ModalBody = ({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) =>
  <div className={cn("text-sm", className)} {...p} />;
export const ModalFooter = ({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) =>
  <div className={cn("mt-4 flex justify-end gap-2", className)} {...p} />;

/* ---------------------------------------- Tabs/Nav ---------------------------------- */
// mapping minimo: <Tabs defaultValue="key"><TabsList><TabsTrigger value="key"/>...</TabsList><TabsContent value="key"/></Tabs>

export const Nav = ({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) =>
  <div className={cn("border-b border-border", className)} {...p} />;
export const Tab = { // placeholder: usa Tabs primitive direttamente nelle nuove pagine
  Container: ({ defaultActiveKey, children }: { defaultActiveKey?: string; children: React.ReactNode }) => (
    <Tabs defaultValue={defaultActiveKey || undefined}>{children}</Tabs>
  ),
};
