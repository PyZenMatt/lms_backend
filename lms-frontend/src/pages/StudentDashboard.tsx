// src/pages/StudentDashboard.tsx
import React from "react";
import { getEnrolledCourses, type Course } from "../services/student";
import DrfPager from "../components/DrfPager";

const fmtEUR = (v?: number | null) =>
  typeof v === "number"
    ? new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(v)
    : "—";

export default function StudentDashboard() {
  const [loading, setLoading] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const [count, setCount] = React.useState(0);
  const [items, setItems] = React.useState<Course[]>([]);

  async function load(p = page) {
    setLoading(true);
    const res = await getEnrolledCourses(p);
    if (res.ok) {
      setItems(res.data.items);
      setCount(res.data.count);
    } else {
      setItems([]);
      setCount(0);
      console.warn("getEnrolledCourses failed", res.status, (res as any).error);
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
      </div>

      {loading && <div>Caricamento…</div>}
      {!loading && items.length === 0 && <div>Nessuna iscrizione trovata.</div>}

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
  );
}
