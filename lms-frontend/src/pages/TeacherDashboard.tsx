// src/pages/TeacherDashboard.tsx
import React from "react";
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
      <div>
        <h1 className="text-2xl font-semibold">Teacher Dashboard</h1>
        <p className="text-sm text-muted-foreground">Panoramica corsi e metriche</p>
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
