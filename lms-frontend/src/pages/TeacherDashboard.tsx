// src/pages/TeacherDashboard.tsx
import React from "react";
import { getUserFromToken, getAccessToken } from "../lib/auth";
import { Link } from "react-router-dom";
import { getTeacherDashboard, type Course, type TeacherStats } from "../services/teacher";
import DrfPager from "../components/DrfPager";

const fmtEUR = (v?: number | null) =>
  typeof v === "number"
    ? new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(v)
    : "—";
const stat = (v?: number) => (typeof v === "number" ? v : "—");

export default function TeacherDashboard() {
  const [loading, setLoading] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const [count, setCount] = React.useState(0);
  const [items, setItems] = React.useState<Course[]>([]);
  const [stats, setStats] = React.useState<TeacherStats | undefined>(undefined);

  async function load(p = page) {
    setLoading(true);
    const res = await getTeacherDashboard(p);
    if (res.ok) {
      setItems(res.data.courses);
      setCount(res.data.count);
      setStats(res.data.stats);
    } else {
      setItems([]);
      setCount(0);
      setStats(undefined);
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
      <div className="flex items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Teacher Dashboard</h1>
          <p className="text-sm text-muted-foreground">Panoramica corsi e metriche</p>
          {(() => {
            const u = getUserFromToken();
            const raw = getAccessToken();
            if (!raw) {
              return <div className="mt-1 text-sm text-muted-foreground">Non sei autenticato (nessun token)</div>;
            }
            if (!u || (!u.first_name && !u.username && !u.email)) {
              return (
                <div className="mt-1 text-sm text-muted-foreground">
                  Nessuna informazione utente trovata nel token.
                  <div className="mt-1 text-xs text-muted-foreground">Token presente: sì — payload: <code className="ml-1">{JSON.stringify(u ?? {})}</code></div>
                </div>
              );
            }
            const name = u.first_name || u.username || u.email || "Docente";
            return <div className="mt-1 text-sm text-muted-foreground">Connesso come: {name}</div>;
          })()}
        </div>
        <div className="flex gap-2">
          <Link
            to="/studio/courses"
            title="Vai alla lista dei tuoi corsi"
            aria-label="I miei corsi"
            className="rounded-md border px-3 py-2 text-sm hover:bg-accent"
          >
            I miei corsi
          </Link>
          <Link
            to="/studio/courses/new"
            title="Crea un nuovo corso"
            aria-label="Nuovo corso"
            className="rounded-lg bg-primary px-4 py-2 text-primary-foreground hover:opacity-90"
          >
            + Nuovo corso
          </Link>
        </div>
      </div>

      {/* Metriche */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">Corsi totali</div>
          <div className="mt-1 text-2xl font-semibold">{stat(stats?.total_courses)}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">Studenti totali</div>
          <div className="mt-1 text-2xl font-semibold">{stat(stats?.total_students)}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">Prezzo medio</div>
          <div className="mt-1 text-2xl font-semibold">{fmtEUR(stats?.avg_price_eur ?? null)}</div>
        </div>
        <div className="rounded-2xl border p-4">
          <div className="text-sm text-muted-foreground">Corsi in revisione</div>
          <div className="mt-1 text-2xl font-semibold">{stat(stats?.pending_courses)}</div>
        </div>
      </div>

      {/* Lista corsi */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">I miei corsi</h2>
        {loading && <div>Caricamento…</div>}
        {!loading && items.length === 0 && <div>Nessun corso trovato.</div>}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((c) => {
            const cover = c.cover_image ?? c.cover_url;
            return (
              <a key={c.id} href={`/courses/${c.id}`} className="block rounded-2xl border p-4 hover:shadow-sm">
                {cover && <img src={cover} alt="" className="mb-3 aspect-[16/9] w-full rounded-xl object-cover" />}
                <h3 className="line-clamp-2 text-lg font-semibold">{c.title}</h3>
                <div className="mt-1 text-sm text-muted-foreground">{c.description ?? "—"}</div>
                <div className="mt-2 font-medium">{fmtEUR(c.price_eur)}</div>
              </a>
            );
          })}
        </div>

        <DrfPager page={page} count={count} onPageChange={toPage} />
      </div>
    </div>
  );
}
