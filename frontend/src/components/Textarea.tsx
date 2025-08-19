import * as React from "react";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
  helperText?: string;
  label?: string;
  id?: string;
}

export function Textarea({ label, id, error, helperText, className = "", ...props }: TextareaProps) {
  const textareaId = id || React.useId();
  const describedBy = error ? `${textareaId}-error` : helperText ? `${textareaId}-help` : undefined;

  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={textareaId} className="block text-sm font-medium text-foreground">
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        aria-invalid={!!error}
        aria-describedby={describedBy}
        className={`w-full rounded-md border border-border bg-input px-3 py-2 outline-none focus:ring-2 resize-none ${className}`}
        {...props}
      />
      {helperText && !error && (
        <p id={`${textareaId}-help`} className="text-xs text-muted-foreground">{helperText}</p>
      )}
      {error && (
        <p id={`${textareaId}-error`} className="text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
