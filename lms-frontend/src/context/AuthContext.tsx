// src/context/AuthContext.tsx
import React, { useContext, useEffect, useMemo, useState } from "react";
import { API } from "../lib/config";
import {
  saveTokens,
  loadTokens,
  clearTokens,
  getRoleFromToken,
  getAccessToken,
  getRefreshToken,
  type Tokens,
} from "../lib/auth";

type Role = "student" | "teacher" | "admin" | null;

type AuthCtx = {
  booting: boolean;
  isAuthenticated: boolean;
  role: Role;
  isTeacher: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshRole: () => Promise<void>;
};

const Ctx = React.createContext<AuthCtx | undefined>(undefined);
export const useAuth = () => {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth outside provider");
  return ctx;
};

async function httpJSON<T>(
  url: string,
  body: unknown,
  extraHeaders?: Record<string, string>
): Promise<{ ok: boolean; status: number; data?: T }> {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(extraHeaders || {}),
    },
    body: JSON.stringify(body ?? {}),
  });
  let data: any = undefined;
  try {
    data = await res.json();
  } catch {}
  return { ok: res.ok, status: res.status, data };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [{ booting, isAuthenticated, role }, setAuth] = useState<{
    booting: boolean;
    isAuthenticated: boolean;
    role: Role;
  }>({ booting: true, isAuthenticated: !!loadTokens(), role: getRoleFromToken() });

  // Boot: se ho token ma non ho role nel JWT, provo a leggerlo dal server
  useEffect(() => {
    (async () => {
      const tokens = loadTokens();
      if (!tokens) {
        setAuth({ booting: false, isAuthenticated: false, role: null });
        return;
      }
      let r = getRoleFromToken();
      if (!r) {
        try {
          const res = await fetch(API.role, {
            headers: { Authorization: `Bearer ${tokens.access}` },
          });
          if (res.ok) {
            const data = await res.json();
            r = (data?.role as Role) ?? r;
          }
        } catch {}
      }
      setAuth({ booting: false, isAuthenticated: true, role: r });
    })();
  }, []);

  async function login(usernameOrEmail: string, password: string): Promise<boolean> {
    // 1) tentativo: email/password (CustomTokenObtainPair)
    let r = await httpJSON<Tokens>(API.token, { email: usernameOrEmail, password });
    // 2) fallback: username/password (SimpleJWT default) se 400
    if (!r.ok && r.status === 400) {
      r = await httpJSON<Tokens>(API.token, { username: usernameOrEmail, password });
    }
    if (!r.ok || !r.data?.access || !r.data?.refresh) return false;

    saveTokens({ access: r.data.access, refresh: r.data.refresh });
    const deducedRole = getRoleFromToken();

    // Prova a perfezionare il ruolo dal server (opzionale)
    let finalRole = deducedRole;
    try {
      const res = await fetch(API.role, {
        headers: { Authorization: `Bearer ${r.data.access}` },
      });
      if (res.ok) {
        const data = await res.json();
        finalRole = (data?.role as Role) ?? finalRole;
      }
    } catch {}

    setAuth({ booting: false, isAuthenticated: true, role: finalRole });
    return true;
  }

  function logout() {
    clearTokens();
    setAuth({ booting: false, isAuthenticated: false, role: null });
  }

  async function refreshRole() {
    const token = getAccessToken();
    if (!token) return;
    try {
      const res = await fetch(API.role, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setAuth((s) => ({ ...s, role: (data?.role as Role) ?? s.role }));
      }
    } catch {}
  }

  const value = useMemo<AuthCtx>(
    () => ({
      booting,
      isAuthenticated,
      role,
      isTeacher: role === "teacher" || role === "admin",
      login,
      logout,
      refreshRole,
    }),
    [booting, isAuthenticated, role]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
