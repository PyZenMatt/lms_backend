import * as React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  helperText?: string;
  label?: string;
  id?: string;
}

export function Input({ label, id, error, helperText, className = "", ...props }: InputProps) {
  const inputId = id || React.useId();
  const describedBy = error ? `${inputId}-error` : helperText ? `${inputId}-help` : undefined;

  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-foreground">
          {label}
        </label>
      )}
      <input
        id={inputId}
        aria-invalid={!!error}
        aria-describedby={describedBy}
        className={`w-full rounded-md border border-border bg-input px-3 py-2 outline-none focus:ring-2 ${className}`}
        {...props}
      />
      {helperText && !error && (
        <p id={`${inputId}-help`} className="text-xs text-muted-foreground">{helperText}</p>
      )}
      {error && (
        <p id={`${inputId}-error`} className="text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
