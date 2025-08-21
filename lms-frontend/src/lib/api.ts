// src/lib/api.ts
import { API_BASE_URL, API_REFRESH_PATH } from "./config";
import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from "./auth";

export type ApiMethodOptions = {
  headers?: Record<string, string>;
  query?: Record<string, string | number | boolean | null | undefined>;
  body?: any;
  signal?: AbortSignal;
};

type Ok<T> = { ok: true; status: number; data: T };
type Err = { ok: false; status: number; error?: any };
export type ApiResult<T> = Ok<T> | Err;

// ---- 403 handler globale ----
let onForbidden: (ctx: { status: number; url: string }) => void = () => {
  if (typeof window !== "undefined") window.location.href = "/forbidden";
};
export function setOnForbidden(handler: typeof onForbidden) { onForbidden = handler; }

// ---- Event helpers ----
function emitLoading(delta: number) {
  if (typeof window !== "undefined")
    window.dispatchEvent(new CustomEvent("api:loading", { detail: { delta } }));
}
function emitToast(message: string, variant: "error" | "success" | "info" | "warning" = "error") {
  if (typeof window !== "undefined")
    window.dispatchEvent(new CustomEvent("toast:show", { detail: { message, variant } }));
}

// ---- Utils ----
function joinUrl(base: string, path: string) {
  if (/^https?:\/\//i.test(path)) return path;
  if (path.startsWith("/")) return `${base}${path}`;
  return `${base}/${path}`;
}
function toQueryString(q?: ApiMethodOptions["query"]) {
  if (!q) return "";
  const p = Object.entries(q)
    .filter(([, v]) => v !== undefined && v !== null)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join("&");
  return p ? `?${p}` : "";
}
function isFormData(v: any): v is FormData {
  return typeof FormData !== "undefined" && v instanceof FormData;
}
async function parseResponse<T>(res: Response): Promise<{ data?: T; error?: any }> {
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    try {
      const json = await res.json();
      return res.ok ? { data: json as T } : { error: json };
    } catch {
      return res.ok ? { data: undefined as unknown as T } : { error: { message: "Invalid JSON" } };
    }
  }
  if (res.status === 204 || res.status === 205) return { data: undefined as unknown as T };
  try {
    const txt = await res.text();
    return res.ok ? { data: (txt as unknown as T) } : { error: txt };
  } catch {
    return res.ok ? { data: undefined as unknown as T } : { error: { message: "Unknown error" } };
  }
}

// ---- Core fetch con auto-refresh + eventi ----
export async function apiFetch<T = any>(path: string, opts: ApiMethodOptions & { method?: string } = {}): Promise<ApiResult<T>> {
  const url = joinUrl(API_BASE_URL, path) + toQueryString(opts.query);
  const headers: Record<string, string> = { ...(opts.headers || {}) };
  const hasBody = typeof opts.body !== "undefined" && opts.body !== null;
  const useForm = hasBody && isFormData(opts.body);
  if (hasBody && !useForm) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }
  const access = getAccessToken();
  if (access) headers["Authorization"] = `Bearer ${access}`;

  emitLoading(+1);
  let res1: Response;
  try {
    res1 = await fetch(url, {
      method: opts.method || (hasBody ? "POST" : "GET"),
      headers,
      body: useForm ? (opts.body as BodyInit) : hasBody ? JSON.stringify(opts.body) : undefined,
      signal: opts.signal,
      credentials: "include",
    });
  } catch (e: any) {
    emitLoading(-1);
    emitToast("Errore di rete. Controlla la connessione.", "error");
    return { ok: false, status: 0, error: e?.message || "network" };
  }
  emitLoading(-1);

  if (res1.status === 403) {
    onForbidden({ status: 403, url });
    const parsed = await parseResponse<T>(res1);
    return { ok: false, status: 403, error: parsed.error };
  }

  if (res1.status === 401) {
    const refresh = getRefreshToken();
    if (!refresh) {
      clearTokens();
      emitToast("Sessione scaduta. Effettua di nuovo l’accesso.", "warning");
      const parsed = await parseResponse<T>(res1);
      return { ok: false, status: 401, error: parsed.error };
    }

    // refresh
    emitLoading(+1);
    let refreshRes: Response;
    try {
      refreshRes = await fetch(joinUrl(API_BASE_URL, API_REFRESH_PATH), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
        credentials: "include",
      });
    } catch (e: any) {
      emitLoading(-1);
      clearTokens();
      emitToast("Impossibile rinnovare la sessione.", "warning");
      const parsed = await parseResponse<T>(res1);
      return { ok: false, status: 401, error: parsed.error };
    }
    emitLoading(-1);

    if (!refreshRes.ok) {
      clearTokens();
      emitToast("Sessione scaduta. Effettua di nuovo l’accesso.", "warning");
      const parsed = await parseResponse<T>(res1);
      return { ok: false, status: 401, error: parsed.error };
    }

    try {
      const rj = (await refreshRes.json()) as { access: string; refresh?: string };
      if (rj?.access) {
        saveTokens({ access: rj.access, refresh: rj.refresh ?? refresh });
      } else {
        clearTokens();
        emitToast("Sessione scaduta. Effettua di nuovo l’accesso.", "warning");
        const parsed = await parseResponse<T>(res1);
        return { ok: false, status: 401, error: parsed.error };
      }
    } catch {
      clearTokens();
      emitToast("Sessione scaduta. Effettua di nuovo l’accesso.", "warning");
      const parsed = await parseResponse<T>(res1);
      return { ok: false, status: 401, error: parsed.error };
    }

    // retry singolo
    const headers2: Record<string, string> = { ...(opts.headers || {}) };
    if (hasBody && !useForm) headers2["Content-Type"] = headers2["Content-Type"] || "application/json";
    const newAccess = getAccessToken();
    if (newAccess) headers2["Authorization"] = `Bearer ${newAccess}`;

    emitLoading(+1);
    let res2: Response;
    try {
      res2 = await fetch(url, {
        method: opts.method || (hasBody ? "POST" : "GET"),
        headers: headers2,
        body: useForm ? (opts.body as BodyInit) : hasBody ? JSON.stringify(opts.body) : undefined,
        signal: opts.signal,
        credentials: "include",
      });
    } catch (e: any) {
      emitLoading(-1);
      emitToast("Errore di rete. Controlla la connessione.", "error");
      return { ok: false, status: 0, error: e?.message || "network" };
    }
    emitLoading(-1);

    if (res2.status === 403) {
      onForbidden({ status: 403, url });
      const parsed = await parseResponse<T>(res2);
      return { ok: false, status: 403, error: parsed.error };
    }

    const parsed2 = await parseResponse<T>(res2);
    if (res2.ok) return { ok: true, status: res2.status, data: parsed2.data as T };
    if (res2.status === 401) {
      clearTokens();
      emitToast("Sessione scaduta. Effettua di nuovo l’accesso.", "warning");
    }
    if (res2.status >= 500) emitToast("Errore del server. Riprova più tardi.", "error");
    return { ok: false, status: res2.status, error: parsed2.error };
  }

  const parsed1 = await parseResponse<T>(res1);
  if (res1.ok) return { ok: true, status: res1.status, data: parsed1.data as T };
  if (res1.status >= 500) emitToast("Errore del server. Riprova più tardi.", "error");
  return { ok: false, status: res1.status, error: parsed1.error };
}

// ---- Helper DX ----
async function handle<T>(method: string, path: string, opts: ApiMethodOptions = {}): Promise<ApiResult<T>> {
  return apiFetch<T>(path, { ...opts, method });
}
export const api = {
  get:   <T = any>(path: string, opts?: ApiMethodOptions) => handle<T>("GET", path, opts),
  post:  <T = any>(path: string, body?: any, opts?: ApiMethodOptions) => handle<T>("POST",  path, { ...(opts || {}), body }),
  put:   <T = any>(path: string, body?: any, opts?: ApiMethodOptions) => handle<T>("PUT",   path, { ...(opts || {}), body }),
  patch: <T = any>(path: string, body?: any, opts?: ApiMethodOptions) => handle<T>("PATCH", path, { ...(opts || {}), body }),
  delete:<T = any>(path: string, opts?: ApiMethodOptions) => handle<T>("DELETE", path, opts),
};
