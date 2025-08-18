import React from 'react';
import { Button as NewButton } from './components/ui/button';
import { Card as NewCard, CardHeader, CardContent, CardFooter } from './components/ui/bg-card text-card-foreground rounded-lg border border-border shadow-sm';
import { Alert as NewAlert } from './components/ui/border rounded-md p-3 bg-muted text-muted-foreground';
import { Badge as NewBadge } from './components/ui/inline-flex items-center rounded-md px-2 py-0.5 text-xs bg-accent text-accent-foreground';
import { Tabs as NewTabs } from './components/ui/tabs';
import { Table as NewTable, TableBody, TableHeader, TableRow, TableHead, TableCell } from './components/ui/table';

export const Spinner: React.FC<{ size?: number; className?: string }> = ({ size = 20, className = '' }) => (
  <span
    className={`inline-block animate-spin rounded-full border-2 border-muted-foreground/30 border-t-muted-foreground ${className}`}
    style={{ width: size, height: size }}
  />
);

// Simple progress bar (striped & animated variants ignored for now)
export const ProgressBar: React.FC<{ now: number; className?: string; label?: string; variant?: string }> = ({ now, className = '', label }) => (
  <div className={`w-full h-3 rounded-md bg-muted overflow-hidden ${className}`} aria-valuenow={now} aria-valuemin={0} aria-valuemax={100} role="progressbar">
    <div className="h-full bg-primary transition-all" style={{ width: `${Math.min(100, Math.max(0, now))}%` }}>
      {label && <span className="sr-only">{label}</span>}
    </div>
  </div>
);

export const Button = NewButton;
export const Alert = NewAlert;
export const Badge = NewBadge;
export const Card: any = Object.assign(NewCard, { Header: CardHeader, Body: CardContent, Footer: CardFooter });

export const Container: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', ...p }) => (
  <div className={`mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 ${className}`} {...p} />
);

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

export const Nav: any = ({ className = '', variant, children, ...p }: any) => (
  <div className={`flex gap-2 ${className}`} {...p}>{children}</div>
);
Nav.Item = ({ className = '', children, ...p }: any) => <div className={className} {...p}>{children}</div>;
Nav.Link = ({ className = '', active, disabled, onClick, children, ...p }: any) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    className={`px-3 py-1.5 text-sm rounded-md border transition-colors ${active ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-accent'} ${className}`}
    {...p}
  >{children}</button>
);

export const Tab: any = {};
Tab.Container = ({ activeKey, onSelect, children }: any) => {
  return React.Children.map(children, (child: any) => {
    if (!React.isValidElement(child)) return child;
    return React.cloneElement(child as any, { activeKey, onSelect } as any);
  });
};
Tab.Content = ({ activeKey, children }: any) => (
  <div>{React.Children.map(children, (child: any) => child?.props?.eventKey === activeKey ? child : null)}</div>
);
Tab.Pane = ({ eventKey, activeKey, children }: any) => (eventKey === activeKey ? <div>{children}</div> : null);

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

export const Table: any = Object.assign(NewTable, { Body: TableBody, Header: TableHeader, Row: TableRow, Head: TableHead, Cell: TableCell });

export const Form: any = ({ children, ...p }: React.FormHTMLAttributes<HTMLFormElement>) => <form {...p}>{children}</form>;
Form.Group = ({ className = '', children, ...p }: any) => <div className={`space-y-1 ${className}`} {...p}>{children}</div>;
Form.Label = ({ className = '', children, ...p }: any) => <label className={`text-sm font-medium ${className}`} {...p}>{children}</label>;
export const FormControl = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(function FC(props, ref) {
  return <input ref={ref} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50" {...props} />;
});

// Modal accepts both `open` and bootstrap-style `show` props.
export const Modal: any = ({ open, show, onHide, children }: any) => (open ?? show) ? <div role="dialog">{children}<button onClick={onHide} className="sr-only">close</button></div> : null;
Modal.Header = ({ children }: any) => <div className="mb-2 font-medium">{children}</div>;
Modal.Title = ({ children }: any) => <h3 className="text-lg font-semibold">{children}</h3>;
Modal.Body = ({ children }: any) => <div className="space-y-3">{children}</div>;
Modal.Footer = ({ children }: any) => <div className="mt-4 flex justify-end gap-2">{children}</div>;

export const Tabs = NewTabs;
export const OverlayTrigger = ({ children }: any) => children;
export const Tooltip = ({ children }: any) => <span>{children}</span>;
export const Collapse: React.FC<{ in: boolean; children: React.ReactNode } & React.HTMLAttributes<HTMLDivElement>> = ({ in: show, children, className = '', ...p }) => (
  <div className={`${show ? 'block' : 'hidden'} ${className}`} {...p}>{children}</div>
);
export const ToastContainer: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', children, ...p }) => (
  <div className={`fixed z-50 top-4 right-4 flex flex-col gap-2 ${className}`} {...p}>{children}</div>
);

export const Toast: React.FC<{ show?: boolean; onClose?: () => void; bg?: string; variant?: string; delay?: number; autohide?: boolean; title?: string } & React.HTMLAttributes<HTMLDivElement>> = ({ show = true, onClose, variant = 'success', title, children, className = '', ...p }) => {
  if (!show) return null;
  const tone = variant === 'danger' || variant === 'error' ? 'destructive' : variant === 'warning' ? 'warning' : variant === 'info' ? 'accent' : 'success';
  const toneClass: Record<string,string> = {
    destructive: 'bg-destructive text-destructive-foreground',
    warning: 'bg-warning text-warning-foreground',
    accent: 'bg-accent text-accent-foreground',
    success: 'bg-secondary text-secondary-foreground'
  };
  return (
    <div className={`rounded-md shadow border border-border px-3 py-2 min-w-[220px] ${toneClass[tone]} ${className}`} role="status" {...p}>
      <div className="flex items-start gap-2">
        <div className="flex-1">
          {title && <div className="font-medium text-sm mb-0.5">{title}</div>}
          <div className="text-xs leading-snug">{children}</div>
        </div>
        {onClose && (
          <button onClick={onClose} className="ml-1 rounded p-1 text-xs hover:bg-background/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50">×</button>
        )}
      </div>
    </div>
  );
};
