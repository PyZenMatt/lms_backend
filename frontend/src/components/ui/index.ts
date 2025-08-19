// Barrel exports strictly DS V2 primitives (no legacy shims)
export { Button } from './button';
export { Card, CardHeader, CardContent, CardFooter } from './card';
export { Alert } from './alert';
export { Badge } from './badge';
export * from './dialog';
export * from './dropdown-menu';
export * from './tooltip';
export * from './tabs';
export * from './accordion';
export * from './checkbox';
export * from './select';
export * from './input-otp';
export * from './slider';
export * from './switch';
export * from './sonner';
export * from './sidebar';
export * from './pagination';
export * from './sheet';
export * from './popover';
export * from './separator';
export * from './radio-group';
export * from './menubar';
export * from './navigation-menu';
export * from './scroll-area';
export * from './progress';
export * from './form';
export * from './breadcrumb';
export * from './calendar';
export * from './carousel';
export * from './chart';
export * from './label';
export * from './toggle';
export * from './toggle-group';
export * from './resizable';
export * from './spinner';
export * from './table';
export { cn } from './utils';
// Layout wrapper (replacement for legacy bootstrap Container)
import React from 'react';
export const Container: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', ...p }) => (
	React.createElement('div', { className: `mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 ${className}`, ...p })
);

// TEMPORARY: re-export a small set of legacy shim names that are still
// widely imported across the codebase (Modal, Container, layout helpers,
// input-group, list-group, ProgressBar, Dropdown). This is a short-term
// compatibility layer — remove once consumers are migrated to DS V2.
export { Modal, Row, Col, ListGroup, InputGroup, ProgressBar, Dropdown } from './ui/legacy-shims'; 

// NOTE: All legacy bootstrap-like compound APIs (Card.Body, Row, Col, etc.) have been removed.
// If you need layout primitives use flex/grid utilities directly or create dedicated DS V2 components.
