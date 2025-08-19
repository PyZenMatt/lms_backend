import * as React from 'react';
// Reuse utility from barrel to avoid deep relative import path fragility
// NOTE: Deep path due to current folder structure (ui/components/ui/utils).
// Consider flattening later.
import { cn } from './components/ui/components/ui/utils';

// Stable layout wrapper replacing legacy bootstrap Container.
// Provides centered, max-width content area with horizontal padding.
export interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Container = React.forwardRef<HTMLDivElement, ContainerProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8', className)}
      {...props}
    />
  )
);
Container.displayName = 'Container';
