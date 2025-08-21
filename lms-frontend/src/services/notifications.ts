// src/services/notifications.ts
import { api } from "../lib/api";
import type { NotificationItem, DrfPaginated } from "../types/notification";

export type ListResponse = {
  ok: boolean;
  status: number;
  data: NotificationItem[];
  next?: string | null;
  previous?: string | null;
  count?: number;
};

type AnyList =
  | NotificationItem[]
  | DrfPaginated<NotificationItem>
  | { data?: NotificationItem[] | DrfPaginated<NotificationItem> }
  | Record<string, any>;

function normalizeList(payload: AnyList): ListResponse {
  // array semplice
  if (Array.isArray(payload)) {
    return { ok: true, status: 200, data: payload, next: null, previous: null, count: payload.length };
  }
  // oggetto
  if (payload && typeof payload === "object") {
    const data = (payload as any).data ?? payload;
    if (Array.isArray(data)) {
      return { ok: true, status: 200, data, next: null, previous: null, count: data.length };
    }
    if (Array.isArray(data?.results)) {
      return {
        ok: true,
        status: 200,
        data: data.results,
        next: data.next ?? null,
        previous: data.previous ?? null,
        count: data.count ?? data.results.length,
      };
    }
    if (Array.isArray((payload as any).results)) {
      return {
        ok: true,
        status: 200,
        data: (payload as any).results,
        next: (payload as any).next ?? null,
        previous: (payload as any).previous ?? null,
        count: (payload as any).count ?? (payload as any).results.length,
      };
    }
  }
  return { ok: true, status: 200, data: [], next: null, previous: null, count: 0 };
}

export async function getUnreadCount(): Promise<number> {
  const res = await api.get<number | { count?: number; unread_count?: number }>("/v1/notifications/unread-count/");
  if (!res.ok) return 0;
  const d: any = res.data;
  if (typeof d === "number") return d;
  if (typeof d?.count === "number") return d.count;
  if (typeof d?.unread_count === "number") return d.unread_count;
  return 0;
}

export async function getNotifications(query?: { page?: number; page_size?: number }) {
  const res = await api.get<AnyList>("/v1/notifications/", { query });
  if (!res.ok) return { ok: false as const, status: res.status, data: [] as NotificationItem[] } as ListResponse;
  return normalizeList(res.data);
}

/**
 * Backend: PATCH /notifications/{id}/read/
 * Frontend (con API_BASE_URL=http://127.0.0.1:8000/api): PATCH /v1/notifications/{id}/read/
 */
export async function markNotificationRead(id: number | string) {
  // Corpo come da tua implementazione: { read: true }
  const res = await api.patch(`/v1/notifications/${id}/read/`, { read: true });
  return res;
}

/**
 * (Opzionale) Se esiste un endpoint per "tutte lette", puoi adattarlo qui.
 * In assenza di specifica certa lo lasciamo disabilitato.
 */
export async function markAllNotificationsRead() {
  // Placeholder conservativo: restituisce ok=false per evitare false positive in UI
  return { ok: false as const, status: 405, error: { detail: "Not implemented on backend" } };
}

// Notifica globale per aggiornare il badge nella navbar
export function notifyUpdated() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("notifications:updated"));
  }
}
