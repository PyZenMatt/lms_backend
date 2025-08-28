// src/pages/Notifications.tsx
import React from "react";
import NotificationItem from "../components/NotificationItem";
import { Alert } from "../components/ui/alert";
import { Spinner } from "../components/ui/spinner";
import EmptyState from "../components/ui/empty-state";
// Local notification shape used in the UI
type N = {
  id: number | string;
  title?: string | null;
  message?: string | null;
  is_read?: boolean;
  created_at?: string | null;
  notification_type?: string;
  decision_id?: number | null;
  related_object_id?: number | null;
  offered_teacher_teo?: string | null;
};
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
  const pageRef = React.useRef(page);
  React.useEffect(() => { pageRef.current = page; }, [page]);
  // Backfill via rewards missing-for-teacher is deprecated; rely solely on notifications feed

  async function load(p = page) {
    setLoading(true);
    setError(null);
    const res = await getNotifications({ page: p, page_size: pageSize });
    if (!res.ok) {
      setError(`Impossibile caricare le notifiche (status ${res.status}).`);
      setItems([]);
      setCount(undefined);
    } else {
      // Map decision_id fallback if backend sent only related_object_id
      const mapped = (res.data as any[]).map((it) => {
        if (
          it &&
          it.notification_type === "teocoin_discount_pending" &&
          (it.decision_id === undefined || it.decision_id === null) &&
          (typeof it.related_object_id === "number")
        ) {
          return { ...it, decision_id: it.related_object_id };
        }
        return it;
      });
      console.debug("[Notifications] loaded", { count: mapped.length, sample: mapped[0] });
      setItems(mapped as N[]);
      setCount(res.count);
    }
    setLoading(false);
  }

  React.useEffect(() => {
    load(1);
    // Stable listener across mounts; uses pageRef to get latest page
    const onUpdated = () => load(pageRef.current);
    window.addEventListener("notifications:updated", onUpdated as EventListener);
    return () => {
      window.removeEventListener("notifications:updated", onUpdated as EventListener);
    };
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

      {error && <Alert variant="error" title="Errore">{error}</Alert>}
      {loading && !items.length && (
        <div className="flex items-center justify-center py-8">
          <Spinner />
          <span className="ml-3 text-sm text-muted-foreground">Caricamento in corso…</span>
        </div>
      )}

      {!loading && items.length === 0 && !error && (
        <EmptyState title="Nessuna notifica" description="Non hai ancora ricevuto notifiche." />
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
