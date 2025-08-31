// src/pages/StudentDashboard.tsx
import React from "react";
import { getUserFromToken, getAccessToken } from "../lib/auth";
import { getEnrolledCourses, type Course } from "../services/student";
import { Alert } from "../components/ui/alert";
import { Spinner } from "../components/ui/spinner";
import EmptyState from "../components/ui/empty-state";
import DrfPager from "../components/DrfPager";

const fmtEUR = (v?: number | null) =>
  typeof v === "number"
    ? new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(v)
    : "—";

export default function StudentDashboard() {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [page, setPage] = React.useState(1);
  const [count, setCount] = React.useState(0);
  const [items, setItems] = React.useState<Course[]>([]);

  async function load(p = page) {
    setLoading(true);
    setError(null);
    const res = await getEnrolledCourses(p);
    if (res.ok) {
      setItems(res.data.items);
      setCount(res.data.count);
    } else {
      setItems([]);
      setCount(0);
  setError(`Impossibile caricare i corsi (HTTP ${res.status})`);
  console.warn("getEnrolledCourses failed", res.status, res);
    }
    setLoading(false);
  }

  React.useEffect(() => {
    load(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function toPage(p: number) {
    const nx = Math.max(1, p);
    setPage(nx);
    load(nx);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">I miei corsi</h1>
        <p className="text-sm text-muted-foreground">Corsi a cui sei iscritto</p>
        {(() => {
          const u = getUserFromToken();
          const raw = getAccessToken();
          if (!raw) {
            return <div className="mt-2 text-sm text-muted-foreground">Non sei autenticato (nessun token)</div>;
          }
          if (!u || (!u.first_name && !u.username && !u.email)) {
            return (
              <div className="mt-2 text-sm text-muted-foreground">
                Nessuna informazione utente trovata nel token.
                <div className="mt-1 text-xs text-muted-foreground">Token presente: sì — payload: <code className="ml-1">{JSON.stringify(u ?? {})}</code></div>
              </div>
            );
          }
          const name = u.first_name || u.username || u.email || "Utente";
          return <div className="mt-2 text-sm text-muted-foreground">Connesso come: {name}</div>;
        })()}
      </div>

      {loading && (
        <div className="flex items-center gap-3">
          <Spinner />
          <span className="text-sm text-muted-foreground">Caricamento…</span>
        </div>
      )}
      {error && <Alert variant="error" title="Errore">{error}</Alert>}
      {!loading && !error && items.length === 0 && (
        <EmptyState title="Nessuna iscrizione trovata" description="Non sei iscritto a nessun corso." />
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {items.map((c) => {
          const cover = c.cover_image ?? c.cover_url;
          return (
            <a key={c.id} href={`/courses/${c.id}`} className="block rounded-lg border p-4 hover:shadow-card">
              {cover && <img src={cover} alt="" className="mb-3 aspect-[16/9] w-full rounded-lg object-cover" />}
              <h3 className="line-clamp-2 text-lg font-semibold">{c.title}</h3>
              <div className="mt-1 text-sm text-muted-foreground">{c.description ?? "—"}</div>
              <div className="mt-2 font-medium">{fmtEUR(c.price_eur)}</div>
            </a>
          );
        })}
      </div>

      <DrfPager page={page} count={count} onPageChange={toPage} />
    </div>
  );
}
