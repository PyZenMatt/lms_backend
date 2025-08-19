import * as React from "react";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
  radius?: string | number;
}

export function Skeleton({ width = "100%", height = 20, radius = 6, className = "", ...props }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-muted ${className}`}
      style={{ width, height, borderRadius: radius }}
      {...props}
    />
  );
}
