// src/lib/auth.ts
export type Tokens = { access: string; refresh: string };

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

export function saveTokens(t: Tokens) {
  localStorage.setItem(ACCESS_KEY, t.access);
  localStorage.setItem(REFRESH_KEY, t.refresh);
}

export function loadTokens(): Tokens | null {
  const access = localStorage.getItem(ACCESS_KEY);
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!access || !refresh) return null;
  return { access, refresh };
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

type Role = "student" | "teacher" | "admin" | null;

export function getRoleFromToken(): Role {
  const raw = getAccessToken();
  if (!raw) return null;
  try {
    const payload = JSON.parse(atob(raw.split(".")[1] || ""));
    // 1) role diretto nel JWT
    if (typeof payload.role === "string") return payload.role as Role;
    // 2) flag booleani nel JWT
    if (payload.is_admin) return "admin";
    if (payload.is_teacher) return "teacher";
    // 3) default prudente
    return "student";
  } catch {
    return null;
  }
}
