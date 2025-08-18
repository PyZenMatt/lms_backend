import * as React from "react";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[];
  error?: string;
  helperText?: string;
  label?: string;
  id?: string;
}

export function Select({ options, label, id, error, helperText, className = "", ...props }: SelectProps) {
  const selectId = id || React.useId();
  const describedBy = error ? `${selectId}-error` : helperText ? `${selectId}-help` : undefined;

  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={selectId} className="block text-sm font-medium text-foreground">
          {label}
        </label>
      )}
      <select
        id={selectId}
        aria-invalid={!!error}
        aria-describedby={describedBy}
        className={`w-full rounded-md border border-border bg-input px-3 py-2 outline-none focus:ring-2 ${className}`}
        {...props}
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {helperText && !error && (
        <p id={`${selectId}-help`} className="text-xs text-muted-foreground">{helperText}</p>
      )}
      {error && (
        <p id={`${selectId}-error`} className="text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
