// src/lib/api.ts
// Lightweight API client with SimpleJWT refresh and global loading events.
// - Emits window CustomEvent("api:loading", { detail: { delta: +1|-1 } }) before/after each request.
// - Returns a uniform shape: { ok, status, data?, error? }.
// - Reads base URL from VITE_API_BASE_URL (default http://127.0.0.1:8000/api).
// - Handles 401 → refresh token (once) via `${BASE}${API_REFRESH_PATH}`.

import eventBus from "./eventBus";

export type ApiResult<T = any> = {
  ok: boolean;
  status: number;
  data?: T;
  error?: any;
};

type RequestOptions = {
  params?: Record<string, any>;
  headers?: Record<string, string>;
  body?: any;
  noAuth?: boolean;
  signal?: AbortSignal;
  // internal
  _retried?: boolean;
  // allow legacy keys used across the codebase (eg. `query`) without type errors
  [k: string]: unknown;
};

const DEFAULT_BASE = "http://127.0.0.1:8000/api";
const RAW_BASE = (import.meta as any)?.env?.VITE_API_BASE_URL || DEFAULT_BASE;
const BASE = normalizeBase(RAW_BASE);

// SimpleJWT refresh endpoint path (relative to BASE)
export const API_REFRESH_PATH = "/auth/refresh/";

// ---- Token storage (localStorage) ----
const TOKENS_KEY = "auth_tokens"; // { access: string, refresh: string }
const LEGACY_ACCESS_KEY = "access_token";
const LEGACY_REFRESH_KEY = "refresh_token";

type Tokens = { access?: string | null; refresh?: string | null };

function loadTokens(): Tokens {
  try {
    const raw = localStorage.getItem(TOKENS_KEY);
    if (raw) return JSON.parse(raw);
    // Fallback to legacy keys used elsewhere in the app
    const access = localStorage.getItem(LEGACY_ACCESS_KEY);
    const refresh = localStorage.getItem(LEGACY_REFRESH_KEY);
    if (access || refresh) return { access: access ?? null, refresh: refresh ?? null };
    return {};
  } catch {
    return {};
  }
}

function saveTokens(t: Tokens) {
  const next = JSON.stringify({ access: t.access ?? null, refresh: t.refresh ?? null });
  localStorage.setItem(TOKENS_KEY, next);
  // Also write legacy keys so older helpers (src/lib/auth.ts) keep working
  try {
    if (t.access) localStorage.setItem(LEGACY_ACCESS_KEY, t.access);
    else localStorage.removeItem(LEGACY_ACCESS_KEY);
    if (t.refresh) localStorage.setItem(LEGACY_REFRESH_KEY, t.refresh);
    else localStorage.removeItem(LEGACY_REFRESH_KEY);
  } catch {
    // ignore
  }
}

function clearTokens() {
  localStorage.removeItem(TOKENS_KEY);
  try {
    localStorage.removeItem(LEGACY_ACCESS_KEY);
    localStorage.removeItem(LEGACY_REFRESH_KEY);
  } catch {}
  window.dispatchEvent(new CustomEvent("auth:logout"));
}

// ---- Helpers ----
function normalizeBase(u: string): string {
  let s = String(u || "").trim();
  if (!s) return DEFAULT_BASE;
  // remove trailing slash
  if (s.endsWith("/")) s = s.slice(0, -1);
  return s;
}

function joinUrl(base: string, path: string): string {
  let p = path.startsWith("/") ? path : `/${path}`;
  // If base already ends with '/api' and path starts with '/api', avoid duplication
  try {
    if (base.endsWith("/api") && p.startsWith("/api")) {
      p = p.replace(/^\/api/, "");
    }
  } catch {
    // fallback to naive join on any error
  }
  // Join and collapse accidental double slashes (except after protocol)
  return `${base}${p}`.replace(/([^:]\/)\/+/, "$1");
}

function buildQuery(params?: Record<string, any>): string {
  if (!params) return "";
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    if (Array.isArray(v)) v.forEach((item) => q.append(k, String(item)));
    else q.append(k, String(v));
  });
  const s = q.toString();
  return s ? `?${s}` : "";
}

function isJsonResponse(res: Response) {
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json");
}

function dispatchLoading(delta: 1 | -1, key?: string) {
  try {
    // Emit on new eventBus for internal consumers
    try {
      eventBus.emit("api:loading", { delta, key });
    } catch {
      // ignore
    }
    // Back-compat: also emit old window CustomEvent so existing listeners keep working
    try {
      window.dispatchEvent(new CustomEvent("api:loading", { detail: { delta } }));
    } catch {
      // ignore
    }
  } catch {
    // ignore
  }
}

// ---- Refresh flow ----
async function refreshAccessToken(): Promise<boolean> {
  const { refresh } = loadTokens();
  if (!refresh) return false;
  dispatchLoading(1);
  try {
    const url = joinUrl(BASE, API_REFRESH_PATH);
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json().catch(() => ({}));
    const access = data?.access || data?.access_token;
    if (typeof access === "string" && access.length > 10) {
      saveTokens({ access, refresh });
      return true;
    }
    return false;
  } catch {
    return false;
  } finally {
    dispatchLoading(-1);
  }
}

// ---- Core request ----
async function coreRequest<T>(
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
  path: string,
  options: RequestOptions = {}
): Promise<ApiResult<T>> {
  const controller = new AbortController();
  const signals = options.signal
    ? [options.signal, controller.signal]
    : [controller.signal];

  // Merge headers
  const headers: Record<string, string> = {
    "accept": "application/json",
    ...options.headers,
  };

  // Auth header
  const { access } = loadTokens();
  if (!options.noAuth && access) {
    headers["authorization"] = `Bearer ${access}`;
  }

  // Body
  let body: BodyInit | undefined;
  if (options.body !== undefined && options.body !== null && method !== "GET") {
    if (options.body instanceof FormData) {
      body = options.body; // let browser set multipart boundary
    } else {
      headers["content-type"] = headers["content-type"] || "application/json";
      body = headers["content-type"].includes("application/json")
        ? JSON.stringify(options.body)
        : (options.body as any);
    }
  }

  // URL
  const url = joinUrl(BASE, path) + buildQuery(options.params);

  // Fire request
  dispatchLoading(1);
  let res: Response | null = null;
  try {
    res = await fetch(url, {
      method,
      headers,
      body,
      credentials: "include",
      signal: signals[signals.length - 1],
    });

    // 401 → try refresh once
    if (res.status === 401 && !options._retried) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return coreRequest<T>(method, path, { ...options, _retried: true });
      }
    }

    // No content
    if (res.status === 204) {
      return { ok: true, status: res.status, data: undefined as any };
    }

    // Parse
    let data: any = undefined;
    if (isJsonResponse(res)) {
      data = await res.json().catch(() => undefined);
    } else {
      const txt = await res.text().catch(() => "");
      data = txt;
    }

    if (!res.ok) {
      // 403/401 cleanup if needed
      if (res.status === 401 || res.status === 403) {
        // optionally clear tokens only on explicit instruction
        // clearTokens();
      }
      const detail = { status: res.status, url, method, data };
      try {
        eventBus.emit("api:error", detail);
      } catch {
        // ignore
      }
      try {
        window.dispatchEvent(new CustomEvent("api:error", { detail }));
      } catch {
        // ignore
      }
      return { ok: false, status: res.status, error: data ?? { message: "Request failed" } };
    }

    return { ok: true, status: res.status, data: data as T };
  } catch (error: any) {
    const message = error?.message || String(error);
    const detail = { status: 0, url, method, message };
    try {
      eventBus.emit("api:error", detail);
    } catch {
      // ignore
    }
    try {
      window.dispatchEvent(new CustomEvent("api:error", { detail }));
    } catch {
      // ignore
    }
    return { ok: false, status: 0, error: message };
  } finally {
    dispatchLoading(-1);
    // abort controller cleanup (no op)
  }
}

// ---- Public API wrapper ----
class ApiClient {
  get<T>(path: string, opts: Omit<RequestOptions, "body"> = {}) {
    return coreRequest<T>("GET", path, opts);
  }
  post<T>(path: string, body?: any, opts: Omit<RequestOptions, "body"> = {}) {
    return coreRequest<T>("POST", path, { ...opts, body });
  }
  put<T>(path: string, body?: any, opts: Omit<RequestOptions, "body"> = {}) {
    return coreRequest<T>("PUT", path, { ...opts, body });
  }
  patch<T>(path: string, body?: any, opts: Omit<RequestOptions, "body"> = {}) {
    return coreRequest<T>("PATCH", path, { ...opts, body });
  }
  delete<T>(path: string, opts: Omit<RequestOptions, "body"> = {}) {
    return coreRequest<T>("DELETE", path, opts);
  }
}

export const api = new ApiClient();

// Back-compat wrapper for older callers that use `apiFetch(path, init)`
export async function apiFetch<T = any>(path: string, init: any = {}, retryOn401 = true): Promise<ApiResult<T>> {
  const method = (String(init?.method || "GET").toUpperCase() as "GET" | "POST" | "PUT" | "PATCH" | "DELETE");
  const options: RequestOptions = {
    headers: init?.headers,
    body: init?.body,
    noAuth: init?.noAuth,
    signal: init?.signal,
    params: init?.params,
    _retried: init?._retried,
  };
  // Note: coreRequest handles retry-on-401 internally via options._retried; we respect retryOn401 by
  // skipping refresh if retryOn401 is false (pass _retried = true to avoid a retry).
  if (!retryOn401) options._retried = true;
  return coreRequest<T>(method, path, options);
}

// ---- Auth helpers (optional) ----
export function setTokens(tokens: Tokens) {
  saveTokens(tokens);
}
export function getTokens(): Tokens {
  return loadTokens();
}
export function logout() {
  clearTokens();
}
export function getApiBase() {
  return BASE;
}

// Convenience: attach to window for debugging (dev only)
// @ts-ignore
if (typeof window !== "undefined") (window as any).__api_base__ = BASE;

// Back-compat: if ToastHost exists at runtime, pick its showToast function via dynamic import.
// Use a module-scoped variable so browser ESM environments don't rely on CommonJS `exports`.
export type ToastOptions = { variant: "success" | "error" | "info"; message: string; title?: string };

let runtimeShowToast: ((opts: ToastOptions) => void) | undefined;
if (typeof window !== "undefined") {
  // Dynamic import avoids circular deps at module evaluation time and works in ESM.
  import("@/components/ToastHost")
    .then((m: any) => {
      const candidate = m?.showToast;
      if (typeof candidate === "function") runtimeShowToast = candidate;
    })
    .catch(() => {
      // ignore missing ToastHost
    });
}

export function showToast(opts: ToastOptions) {
  try {
    if (typeof runtimeShowToast === "function") runtimeShowToast(opts);
  } catch {
    // swallow errors in environments without a ToastHost
  }
}
