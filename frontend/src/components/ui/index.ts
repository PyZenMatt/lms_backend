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

// Legacy fallbacks (kept temporarily; TODO: remove once all imports migrated)
// Re-export under Legacy* names to avoid collisions
export { Button as LegacyButton } from './Button';
