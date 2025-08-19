import React from 'react';
import { Button as NewButton } from './ui/button';

// Minimal compatibility shims (temporary)
export const ProgressBar: React.FC<{ now: number; className?: string; label?: string }> = ({ now, className = '', label }) => (
  <div className={`w-full h-3 rounded-md bg-muted overflow-hidden ${className}`} aria-valuenow={now} aria-valuemin={0} aria-valuemax={100} role="progressbar">
    <div className="h-full bg-primary transition-all" style={{ width: `${Math.min(100, Math.max(0, now))}%` }}>
      {label && <span className="sr-only">{label}</span>}
    </div>
  </div>
);

export const Button = NewButton;

// Container shim removed – use the new exported Container component from 'container.tsx'.

export const Row: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', ...p }) => (
  <div className={`flex flex-wrap -mx-2 ${className}`} {...p} />
);
export const Col: React.FC<React.HTMLAttributes<HTMLDivElement> & { md?: number; lg?: number; sm?: number } > = ({ className = '', md, lg, sm, ...p }) => {
  const toWidth = (n?: number) => (n ? `md:w-${Math.min(12, n)}/12` : '');
  return <div className={`px-2 w-full ${toWidth(md)} ${className}`} {...p} />;
};

export const ListGroup: React.FC<React.HTMLAttributes<HTMLUListElement>> & { Item: React.FC<React.LiHTMLAttributes<HTMLLIElement>> } =
  Object.assign(
    ({ className = '', ...p }) => <ul className={`divide-y divide-border rounded-md border ${className}`} {...p} />,
    {
      Item: ({ className = '', ...p }) => <li className={`px-3 py-2 hover:bg-accent/50 ${className}`} {...p} />
    }
  );

export const InputGroup: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', ...p }) => (
  <div className={`flex items-stretch ${className}`} {...p} />
);

export const Dropdown: any = ({ children }: { children: React.ReactNode }) => <div className="relative inline-block">{children}</div>;
Dropdown.Toggle = ({ className = '', children, ...p }: any) => (
  <NewButton variant="outline" className={className} {...p}>{children}</NewButton>
);
Dropdown.Menu = ({ className = '', children, ...p }: any) => (
  <div className={`absolute z-50 mt-1 min-w-[8rem] rounded-md border bg-popover p-1 shadow focus:outline-none ${className}`} {...p}>{children}</div>
);
Dropdown.Item = ({ className = '', children, ...p }: any) => (
  <button className={`w-full cursor-pointer rounded-sm px-2 py-1 text-left text-sm hover:bg-accent hover:text-accent-foreground ${className}`} {...p}>{children}</button>
);

export const Modal: any = ({ open, show, onHide, children }: any) => (open ?? show) ? <div role="dialog">{children}<button onClick={onHide} className="sr-only">close</button></div> : null;
Modal.Header = ({ children }: any) => <div className="mb-2 font-medium">{children}</div>;
Modal.Title = ({ children }: any) => <h3 className="text-lg font-semibold">{children}</h3>;
Modal.Body = ({ children }: any) => <div className="space-y-3">{children}</div>;
Modal.Footer = ({ children }: any) => <div className="mt-4 flex justify-end gap-2">{children}</div>;

export default {};
