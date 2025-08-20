// Token storage + decode role dal JWT
type Tokens = { access: string; refresh: string };

const LS_ACCESS = "access_token";
const LS_REFRESH = "refresh_token";

let accessMem: string | null = null;
let refreshMem: string | null = null;

export function loadTokens(): Tokens | null {
  const a = localStorage.getItem(LS_ACCESS);
  const r = localStorage.getItem(LS_REFRESH);
  accessMem = a;
  refreshMem = r;
  return a && r ? { access: a, refresh: r } : null;
}
export function saveTokens(t: Tokens) {
  accessMem = t.access; refreshMem = t.refresh;
  localStorage.setItem(LS_ACCESS, t.access);
  localStorage.setItem(LS_REFRESH, t.refresh);
}
export function clearTokens() {
  accessMem = null; refreshMem = null;
  localStorage.removeItem(LS_ACCESS);
  localStorage.removeItem(LS_REFRESH);
}
export function getAccessToken() { return accessMem; }
export function getRefreshToken() { return refreshMem; }

export function decodeJwt<T = any>(token: string | null): T | null {
  if (!token) return null;
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const json = decodeURIComponent(atob(base64).split("").map(c =>
      "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2)
    ).join(""));
    return JSON.parse(json);
  } catch { return null; }
}

export function getRoleFromToken(): string | null {
  const payload = decodeJwt(getAccessToken());
  // Adegua la chiave se diversa (es. 'user_role', 'groups'…)
  return payload?.role ?? null;
}
