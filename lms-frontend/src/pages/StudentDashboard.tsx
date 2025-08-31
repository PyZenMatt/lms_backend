// src/pages/StudentDashboard.tsx
import React from "react";
import { useNavigate } from "react-router-dom";
import { Dashboard as FigmaDashboard } from "@/components/figma/Dashboard";

const fmtEUR = (v?: number | null) =>
  typeof v === "number"
    ? new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(v)
    : "—";

export default function StudentDashboard() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <FigmaDashboard
        onContinueCourse={(courseId: string) => navigate(`/courses/${courseId}`)}
        onNavigateToPage={(page: string) => navigate(page.startsWith("/") ? page : `/${page}`)}
      />
    </div>
  );
}
