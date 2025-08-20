export const API_BASE_URL =
  (import.meta as any).env.VITE_API_BASE_URL?.replace(/\/+$/, "") || "http://localhost:8000/api/v1";

export const API_LOGIN_PATH =
  (import.meta as any).env.VITE_API_LOGIN_PATH || "/auth/token/";

export const API_REFRESH_PATH =
  (import.meta as any).env.VITE_API_REFRESH_PATH || "/auth/token/refresh/";
