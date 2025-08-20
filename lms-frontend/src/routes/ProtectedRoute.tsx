import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function RoleRoute({ children, allow }: { children: React.ReactNode; allow: ("student"|"teacher")[] }) {
  const { isAuthenticated, role } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!role || !allow.includes(role as any)) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}
