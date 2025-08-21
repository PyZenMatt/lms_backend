import React from "react";
import { apiFetch } from "../lib/api";
import { API_LOGIN_PATH } from "../lib/config";
import { loadTokens, saveTokens, clearTokens, getRoleFromToken } from "../lib/auth";
import { fetchServerRole } from "../lib/role";

type Role = "student" | "teacher" | "admin" | null;

type AuthCtx = {
  booting: boolean;
  isAuthenticated: boolean;
  role: Role;
  isTeacher: boolean;
  isStudent: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshRole: () => Promise<void>;
};

export const AuthContext = React.createContext<AuthCtx | null>(null);
export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside provider");
  return ctx;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [{ booting, isAuthenticated, role }, setState] = React.useState(() => {
    const hasTokens = !!loadTokens();
    // Prova a leggere subito il ruolo dal JWT (potrebbe non esserci)
    const initialRole = getRoleFromToken() as Role;
    return { booting: hasTokens && !initialRole, isAuthenticated: hasTokens, role: initialRole };
  });

  // Se abbiamo token ma il ruolo non è nel JWT, chiedilo al server
  React.useEffect(() => {
    (async () => {
      if (booting) {
        const srvRole = await fetchServerRole();
        setState(s => ({ ...s, booting: false, role: srvRole ?? s.role }));
      }
    })();
  }, [booting]);

  async function refreshRole() {
    const srvRole = await fetchServerRole();
    setState(s => ({ ...s, role: srvRole ?? s.role }));
  }

  async function login(email: string, password: string) {
    const res = await apiFetch<{ access: string; refresh: string }>(API_LOGIN_PATH, {
      method: "POST",
      body: { email, password },
    });
    if (!res.ok || !res.data?.access || !res.data?.refresh) return false;

    saveTokens({ access: res.data.access, refresh: res.data.refresh });
    const jwtRole = getRoleFromToken() as Role;
    setState({ booting: !jwtRole, isAuthenticated: true, role: jwtRole });
    if (!jwtRole) await refreshRole();
    return true;
  }

  function logout() {
    clearTokens();
    setState({ booting: false, isAuthenticated: false, role: null });
  }

  const value: AuthCtx = {
    booting,
    isAuthenticated,
    role,
    isTeacher: role === "teacher",
    isStudent: role === "student",
    login, logout, refreshRole,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
