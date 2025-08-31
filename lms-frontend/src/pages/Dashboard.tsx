// src/pages/Dashboard.tsx — mount figma Dashboard
import React from "react";
import { useNavigate } from "react-router-dom";
import { Dashboard as FigmaDashboard } from "@/components/figma/Dashboard";

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <FigmaDashboard
        onContinueCourse={(courseId: string) => navigate(`/learn/${courseId}`)}
        onNavigateToPage={(page: string) => navigate(page.startsWith("/") ? page : `/${page}`)}
      />
    </div>
  );
}
