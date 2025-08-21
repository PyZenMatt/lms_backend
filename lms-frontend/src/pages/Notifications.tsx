// src/pages/Notifications.tsx
import React from "react";
import NotificationItem from "../components/NotificationItem";
import type { NotificationItem as N } from "../types/notification";
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  notifyUpdated,
} from "../services/notifications";
import DrfPager from "../components/DrfPager";

export default function Notifications() {
  const [items, setItems] = React.useState<N[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [page, setPage] = React.useState(1);
  const [pageSize] = React.useState(10);
  const [count, setCount] = React.useState<number | undefined>(undefined);

  async function load(p = page) {
    setLoading(true);
    setError(null);
    const res = await getNotifications({ page: p, page_size: pageSize });
    if (!res.ok) {
      setError(`Impossibile caricare le notifiche (status ${res.status}).`);
      setItems([]);
      setCount(undefined);
    } else {
      setItems(res.data);
      setCount(res.count);
    }
    setLoading(false);
  }

  React.useEffect(() => {
    load(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onMarkRead(id: N["id"]) {
    const r = await markNotificationRead(id);
    if (r.ok) {
      notifyUpdated();
      await load(page);
    } else {
      console.warn("mark read failed", r.status, r.error);
    }
  }

  async function onMarkAll() {
    const r = await markAllNotificationsRead();
    if (r.ok) {
      notifyUpdated();
      await load(page);
    } else {
      console.warn("mark all failed", r.status, r.error);
    }
  }

  function toPage(p: number) {
    const nx = Math.max(1, p);
    setPage(nx);
    load(nx);
  }

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Notifiche</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => load(page)}
            className="inline-flex h-9 items-center rounded-md border px-3 hover:bg-accent"
            disabled={loading}
          >
            {loading ? "Aggiorno..." : "Ricarica"}
          </button>
          <button
            onClick={onMarkAll}
            className="inline-flex h-9 items-center rounded-md bg-primary px-3 text-primary-foreground hover:opacity-90"
            disabled={loading || items.length === 0}
          >
            Segna tutte come lette
          </button>
        </div>
      </header>

      {error && <div className="text-sm text-red-600">{error}</div>}
      {loading && !items.length && (
        <div className="text-sm text-muted-foreground">Caricamento in corso…</div>
      )}

      {!loading && items.length === 0 && !error && (
        <div className="rounded-lg border p-8 text-center">
          <p className="text-sm text-muted-foreground">Nessuna notifica</p>
        </div>
      )}

      <div className="space-y-3">
        {items.map((it) => (
          <NotificationItem key={it.id} item={it} onMarkRead={onMarkRead} />
        ))}
      </div>

      <DrfPager
        page={page}
        count={count}
        pageSize={pageSize}
        onPageChange={toPage}
        className="pt-4"
      />
    </section>
  );
}
