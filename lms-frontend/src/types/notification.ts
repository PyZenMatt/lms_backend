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

export async function markNotificationRead(id: number | string) {
  // Tentativo 1: PATCH {is_read:true}
  const p1 = await api.patch(`/v1/notifications/${id}/`, { is_read: true });
  if (p1.ok) return p1;

  // Tentativo 2: POST /read/
  const p2 = await api.post(`/v1/notifications/${id}/read/`, {});
  return p2;
}

export async function markAllNotificationsRead() {
  // Tentativo 1:
  const r1 = await api.post("/v1/notifications/mark-all-read/", {});
  if (r1.ok) return r1;

  // Tentativo 2:
  const r2 = await api.post("/v1/notifications/mark_read_all/", {});
  return r2;
}

// Utility: dispatch evento globale per sync badge
export function notifyUpdated() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("notifications:updated"));
  }
}
