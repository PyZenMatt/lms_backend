// src/lib/api.ts
import { API_BASE_URL, API_REFRESH_PATH } from "./config";
import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from "./auth";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

type ApiResult<T = any> = {
  ok: boolean;
  status: number;
  data?: T;
  error?: unknown;
  response?: Response;
};

let refreshing: Promise<string | null> | null = null;

async function doFetch(input: string, init: RequestInit): Promise<Response> {
  return fetch(input, {
    credentials: "include", // CORS dev coerente col BE
    ...init,
  });
}

function withAuthHeaders(init?: RequestInit): Headers {
  const h = new Headers(init?.headers || {});
  if (!h.has("Accept")) h.set("Accept", "application/json");
  // NON forzare Content-Type se body è FormData
  const hasFormData = init?.body && typeof FormData !== "undefined" && init?.body instanceof FormData;
  if (!hasFormData && !h.has("Content-Type")) h.set("Content-Type", "application/json");
  const access = getAccessToken();
  if (access && !h.has("Authorization")) h.set("Authorization", `Bearer ${access}`);
  return h;
}

async function refreshAccessToken(): Promise<string | null> {
  if (!getRefreshToken()) return null;
  if (!refreshing) {
    refreshing = (async () => {
      try {
        const res = await doFetch(API_BASE_URL + API_REFRESH_PATH, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ refresh: getRefreshToken() }),
        });
        // SimpleJWT di solito ritorna solo "access"
        if (!res.ok) return null;
        const json = await res.json().catch(() => ({}));
        const nextAccess = json?.access as string | undefined;
        const nextRefresh = json?.refresh as string | undefined; // in alcuni back ritorna anche refresh
        if (!nextAccess) return null;
        saveTokens(nextAccess, nextRefresh || null);
        return nextAccess;
      } catch {
        return null;
      } finally {
        refreshing = null;
      }
    })();
  }
  return refreshing;
}

async function apiFetch<T = any>(
  path: string,
  init: RequestInit = {},
  retryOn401 = true
): Promise<ApiResult<T>> {
  const url = path.startsWith("http") ? path : API_BASE_URL + path.replace(/^\/+/, "/");
  const res = await doFetch(url, { ...init, headers: withAuthHeaders(init) });

  // Fast path
  if (res.status !== 401) {
    return parseResponse<T>(res);
  }

  // 401 → prova refresh una sola volta
  if (!retryOn401) {
    return parseResponse<T>(res);
  }

  const newAccess = await refreshAccessToken();
  if (!newAccess) {
    clearTokens();
    return parseResponse<T>(res);
  }

  // Retry con nuovo token
  const retryHeaders = new Headers(init.headers || {});
  retryHeaders.set("Authorization", `Bearer ${newAccess}`);
  const res2 = await doFetch(url, { ...init, headers: retryHeaders });
  return parseResponse<T>(res2);
}

async function parseResponse<T>(res: Response): Promise<ApiResult<T>> {
  const ct = res.headers.get("Content-Type") || "";
  const isJson = ct.includes("application/json");
  const data = isJson ? await res.json().catch(() => undefined) : undefined;
  return { ok: res.ok, status: res.status, data, response: res, ...(res.ok ? {} : { error: data }) };
}

// Helpers DX
function bodyOf(data?: any): BodyInit | undefined {
  if (data == null) return undefined;
  if (typeof FormData !== "undefined" && data instanceof FormData) return data;
  return JSON.stringify(data);
}

export const api = {
  get:  <T = any>(path: string, init?: RequestInit) => apiFetch<T>(path, { ...init, method: "GET" }),
  delete:<T = any>(path: string, init?: RequestInit) => apiFetch<T>(path, { ...init, method: "DELETE" }),
  post: <T = any>(path: string, data?: any, init?: RequestInit) =>
    apiFetch<T>(path, { ...init, method: "POST", body: bodyOf(data) }),
  put:  <T = any>(path: string, data?: any, init?: RequestInit) =>
    apiFetch<T>(path, { ...init, method: "PUT", body: bodyOf(data) }),
  patch:<T = any>(path: string, data?: any, init?: RequestInit) =>
    apiFetch<T>(path, { ...init, method: "PATCH", body: bodyOf(data) }),
};

export { apiFetch };
