// src/components/BuyCourseButton.tsx
import React from "react"
import { Link, useNavigate } from "react-router-dom"

type Props = {
  courseId: number | string
  className?: string
  children?: React.ReactNode
  /** Se il bottone è dentro una card cliccabile o un <Link> wrapper, abilita lo stopPropagation */
  stopPropagation?: boolean
  /** Se non vuoi usare <Link>, usa navigate programmatico */
  useNavigateMode?: boolean
}

export default function BuyCourseButton({
  courseId,
  className,
  children,
  stopPropagation = true,
  useNavigateMode = false,
}: Props) {
  const navigate = useNavigate()
  const to = `/courses/${courseId}/checkout`

  const commonProps = {
    className:
      className ||
      "inline-flex items-center rounded-xl px-4 py-2 border bg-black text-white hover:opacity-90",
    // preveniamo click bubbling quando il bottone è dentro una card/link
    onClick: (e: React.MouseEvent) => {
      if (stopPropagation) e.stopPropagation()
    },
  }

  if (useNavigateMode) {
    return (
      <button
        type="button"
        {...commonProps}
        onClick={(e) => {
          if (stopPropagation) e.stopPropagation()
          navigate(to)
        }}
      >
        {children || "Compra"}
      </button>
    )
  }

  return (
    <Link to={to} {...commonProps}>
      {children || "Compra"}
    </Link>
  )
}
