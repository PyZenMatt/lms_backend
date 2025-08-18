// Unified barrel: prefer new primitives; alias legacy components if needed
// New primitives (Radix-based, v2 design system)
export { Button } from './components/ui/button';
export { Card, CardHeader, CardContent, CardFooter } from './components/ui/card';
export { Alert } from './components/ui/alert';
export { Badge } from './components/ui/badge';
export * from './components/ui/dialog';
export * from './components/ui/dropdown-menu';
export * from './components/ui/tooltip';
export * from './components/ui/tabs';
export * from './components/ui/accordion';
export * from './components/ui/checkbox';
export * from './components/ui/select';
export * from './components/ui/input-otp';
export * from './components/ui/slider';
export * from './components/ui/switch';
export * from './components/ui/sonner';
export * from './components/ui/sidebar';
export * from './components/ui/pagination';
export * from './components/ui/sheet';
export * from './components/ui/popover';
export * from './components/ui/separator';
export * from './components/ui/radio-group';
export * from './components/ui/menubar';
export * from './components/ui/navigation-menu';
export * from './components/ui/scroll-area';
export * from './components/ui/progress';
export * from './components/ui/form';
export * from './components/ui/breadcrumb';
export * from './components/ui/calendar';
export * from './components/ui/carousel';
export * from './components/ui/chart';
export * from './components/ui/label';
export * from './components/ui/toggle';
export * from './components/ui/toggle-group';
export * from './components/ui/resizable';
export { cn } from './components/ui/utils';

// ---- Legacy runtime aliases (Bootstrap-like) ----
// Provide Card.Body / Card.Header / Card.Footer so existing JSX using Card.Body still works at runtime.
// Types are intentionally not declared to keep migration pressure (TS will flag in TSX, JSX will pass).
// @ts-ignore
if (typeof Card !== 'undefined') {
	// @ts-ignore
	(Card as any).Body = CardContent;
	// @ts-ignore
	(Card as any).Header = CardHeader;
	// @ts-ignore
	(Card as any).Footer = CardFooter;
}

// Legacy fallbacks (kept temporarily; TODO: remove once all imports migrated)
// Re-export under Legacy* names to avoid collisions
export { Button as LegacyButton } from './Button';
import React from 'react';

// Minimal ListGroup shim (structural only) to unblock remaining imports; TODO remove after refactor
interface ListGroupComponent extends React.FC<React.HTMLAttributes<HTMLUListElement>> {
	Item: React.FC<React.LiHTMLAttributes<HTMLLIElement>>;
}

const ListGroupBase: React.FC<React.HTMLAttributes<HTMLUListElement>> = (props) => React.createElement('ul', props);
const ListGroupItem: React.FC<React.LiHTMLAttributes<HTMLLIElement>> = (props) => React.createElement('li', props);
export const ListGroup: ListGroupComponent = Object.assign(ListGroupBase, { Item: ListGroupItem });

// Minimal Dropdown shim (structural only)
type DropdownComponent = any;
const DropdownBase: React.FC<{ align?: string; children: React.ReactNode }> = ({ children }) => React.createElement('div', { className: 'relative inline-block' }, children);
const DropdownToggle: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement>> = ({ children, className = '', ...rest }) =>
	React.createElement('button', { className: `btn btn-sm ${className}`.trim(), type: 'button', ...rest }, children);
const DropdownMenu: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...rest }) =>
	React.createElement('div', { className: `dropdown-menu show ${className}`.trim(), ...rest }, children);
export const Dropdown: DropdownComponent = Object.assign(DropdownBase, { Toggle: DropdownToggle, Menu: DropdownMenu });

// Other minimal shims (structural wrappers) pending full refactor
export const InputGroup: React.FC<React.HTMLAttributes<HTMLDivElement>> = (p) => React.createElement('div', { className: `input-group ${p.className || ''}`.trim(), ...p });
export const FormControl: React.FC<React.InputHTMLAttributes<HTMLInputElement>> = (p) => React.createElement('input', p);
export const ProgressBar: React.FC<{ now?: number; label?: string } & React.HTMLAttributes<HTMLDivElement>> = ({ now, label, className = '', ...rest }) =>
	React.createElement('div', { className: `progress ${className}`.trim(), ...rest },
		React.createElement('div', { className: 'progress-bar', style: { width: `${now || 0}%` } }, label || null)
	);
export const Row: React.FC<React.HTMLAttributes<HTMLDivElement>> = (p) => React.createElement('div', { className: `row ${p.className || ''}`.trim(), ...p });
export const Col: React.FC<React.HTMLAttributes<HTMLDivElement>> = (p) => React.createElement('div', { className: `col ${p.className || ''}`.trim(), ...p });
export const Container: React.FC<React.HTMLAttributes<HTMLDivElement>> = (p) => React.createElement('div', { className: `container ${p.className || ''}`.trim(), ...p });
export const Table: React.FC<React.TableHTMLAttributes<HTMLTableElement>> = (p) => React.createElement('table', p);
export const Modal: any = ({ children, show }: { children: React.ReactNode; show?: boolean }) => show ? React.createElement('div', { className: 'modal d-block' }, children) : null;
Modal.Header = (p: any) => React.createElement('div', { className: 'modal-header' }, p.children);
Modal.Body = (p: any) => React.createElement('div', { className: 'modal-body' }, p.children);
Modal.Footer = (p: any) => React.createElement('div', { className: 'modal-footer' }, p.children);
export const Form: any = (p: any) => React.createElement('form', p);
Form.Group = (p: any) => React.createElement('div', { className: 'mb-3' }, p.children);
Form.Label = (p: any) => React.createElement('label', p);
Form.Control = (p: any) => React.createElement('input', { className: 'form-control', ...p });

// Spinner shim
export const Spinner: any = ({ animation = 'border', className = '', ...rest }: any) =>
	React.createElement(
		'div',
		{ className: `spinner-${animation} ${className}`.trim(), role: 'status', ...rest },
		React.createElement('span', { className: 'visually-hidden' }, 'Loading...')
	);

// Nav shim
export const Nav: any = (p: any) => React.createElement('div', { className: `nav ${p.className || ''}`.trim(), ...p });
Nav.Item = (p: any) => React.createElement('div', { className: 'nav-item' }, p.children);
Nav.Link = ({ children, className = '', ...rest }: any) => React.createElement('button', { className: `nav-link ${className}`.trim(), type: 'button', ...rest }, children);

// Tab shim
export const Tab: any = {};
Tab.Container = (p: any) => React.createElement('div', { className: `tab-container ${p.className || ''}`.trim() }, p.children);
Tab.Content = (p: any) => React.createElement('div', { className: 'tab-content' }, p.children);
Tab.Pane = (p: any) => React.createElement('div', { className: 'tab-pane active' }, p.children);

// Collapse shim
export const Collapse: React.FC<{ in?: boolean; show?: boolean; children?: React.ReactNode } & React.HTMLAttributes<HTMLDivElement>> = ({ in: inProp, show, children, className = '', ...rest }) => {
	const visible = inProp ?? show ?? false;
	if (!visible) return null;
	return React.createElement('div', { className: `collapse show ${className}`.trim(), ...rest }, children);
};

// Toast shims
export const ToastContainer: React.FC<React.HTMLAttributes<HTMLDivElement>> = (p) => React.createElement('div', { className: `toast-container ${p.className || ''}`.trim(), ...p });
export const Toast: any = ({ show = true, className = '', children, ...rest }: any) =>
	show ? React.createElement('div', { className: `toast show ${className}`.trim(), role: 'alert', ...rest }, children) : null;
Toast.Header = (p: any) => React.createElement('div', { className: 'toast-header' }, p.children);
Toast.Body = (p: any) => React.createElement('div', { className: 'toast-body' }, p.children);
