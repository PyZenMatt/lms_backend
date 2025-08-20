import { API_BASE_URL, API_REFRESH_PATH } from "./config";
import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from "./auth";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "OPTIONS";
type FetchOpts = { method?: HttpMethod; body?: any; headers?: Record<string, string> };

async function doFetch(path: string, opts: FetchOpts = {}, useAccess = true) {
  const url = `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(opts.headers || {}),
  };
  const token = useAccess ? getAccessToken() : null;
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(url, {
    method: opts.method || "GET",
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });

  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json().catch(() => null) : null;
  return { res, data };
}

export async function apiFetch<T = unknown>(path: string, opts: FetchOpts = {}) {
  // 1) prova con access
  let { res, data } = await doFetch(path, opts, true);
  if (res.status !== 401) return { ok: res.ok, status: res.status, data: data as T };

  // 2) se 401, tenta refresh
  const refresh = getRefreshToken();
  if (!refresh) return { ok: false, status: 401, data: null as any };

  const r = await doFetch(API_REFRESH_PATH, { method: "POST", body: { refresh } }, false);
  if (!r.res.ok || !r.data?.access) {
    clearTokens();
    return { ok: false, status: 401, data: null as any };
  }
  // salva nuovo access (mantieni refresh esistente)
  saveTokens({ access: r.data.access, refresh });

  // 3) ritenta una sola volta
  const retry = await doFetch(path, opts, true);
  return { ok: retry.res.ok, status: retry.res.status, data: retry.data as T };
}
