import * as React from "react";

export interface Tab {
  value: string;
  label: string;
}

export interface TabsProps {
  tabs: Tab[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function Tabs({ tabs, value, onChange, className = "" }: TabsProps) {
  return (
    <div className={`flex border-b border-border ${className}`} role="tablist">
      {tabs.map(tab => (
        <button
          key={tab.value}
          role="tab"
          aria-selected={value === tab.value}
          className={`px-4 py-2 font-medium transition-colors focus:outline-none ${value === tab.value ? "border-b-2 border-primary text-primary" : "text-muted-foreground"}`}
          onClick={() => onChange(tab.value)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
