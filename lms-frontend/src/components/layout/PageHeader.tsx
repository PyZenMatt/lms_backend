import React from "react"

type Props = { title: string; subtitle?: string; right?: React.ReactNode }
export default function PageHeader({ title, subtitle, right }: Props) {
  return (
    <div className="container flex items-end justify-between gap-4 py-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
        {subtitle && (
          <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
        )}
      </div>
      {right}
    </div>
  )
}
