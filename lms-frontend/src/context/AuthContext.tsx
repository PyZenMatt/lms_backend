import React from "react";
import { apiFetch } from "../lib/api";
import { API_LOGIN_PATH } from "../lib/config";
import { loadTokens, saveTokens, clearTokens, getRoleFromToken } from "../lib/auth";

type AuthCtx = {
  isAuthenticated: boolean;
  role: string | null;
  isTeacher: boolean;
  isStudent: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
};

export const AuthContext = React.createContext<AuthCtx | null>(null);
export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside provider");
  return ctx;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [{ isAuthenticated, role }, setAuth] = React.useState(() => {
    const t = loadTokens();
    const r = getRoleFromToken();
    return { isAuthenticated: !!t, role: r };
  });

  async function login(username: string, password: string) {
    // Usa "email" perché lo schema di /v1/token/ richiede email+password
    const body = { email: username, password };
    const res = await apiFetch<{ access: string; refresh: string }>(API_LOGIN_PATH, {
      method: "POST", body,
    });
    if (!res.ok || !res.data?.access || !res.data?.refresh) return false;

    saveTokens({ access: res.data.access, refresh: res.data.refresh });
    setAuth({ isAuthenticated: true, role: getRoleFromToken() });
    return true;
  }

  function logout() {
    clearTokens();
    setAuth({ isAuthenticated: false, role: null });
  }

  const value: AuthCtx = {
    isAuthenticated,
    role,
    isTeacher: role === "teacher",
    isStudent: role === "student",
    login, logout,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
