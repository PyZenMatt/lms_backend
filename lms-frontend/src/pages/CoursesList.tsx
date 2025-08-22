// src/pages/CoursesList.tsx
import React from "react";
import { listCourses, type ListParams } from "../services/courses";
import type { Course } from "../services/courses";
import Pagination from "../components/Pagination";
import { useQueryState } from "../lib/useQueryState";
import CourseCard from "../components/CourseCard";
import CategoryFilter from "../components/CategoryFilter";
import BuyCourseButton from "../components/BuyCourseButton";

const PAGE_SIZE = 9;

// --- helpers prezzo (robusto) ---
function priceValue(c: Course): number | null {
  const raw: any =
    (c as any).price ??
    (c as any).price_amount ??
    (typeof (c as any).price === "object" ? (c as any).price?.value : null);

  if (typeof raw === "number") return raw;
  if (typeof raw === "string") {
    const p = parseFloat(raw.replace(",", "."));
    return Number.isFinite(p) ? p : null;
  }
  return null;
}

// --- enrolled helper (robusto) ---
function isEnrolled(c: Course): boolean {
  const v: any = (c as any).is_enrolled;
  return v === true || v === "true" || v === 1;
}

// --- category helpers ---
function slugify(x: string) {
  return x.trim().toLowerCase().replace(/\s+/g, "-");
}
function courseCategorySlug(c: Course): string | null {
  const cat: any = (c as any).category;
  if (!cat) return null;
  if (typeof cat === "string") return slugify(cat);
  if (typeof cat === "object") {
    if (typeof cat.slug === "string") return slugify(cat.slug);
    if (typeof cat.name === "string") return slugify(cat.name);
  }
  return null;
}

// ---- Ordinamento locale (fallback se BE ignora ordering) ----
type Comparator = (a: Course, b: Course) => number;
const byString = (sel: (c: Course) => string | undefined | null, dir: 1 | -1 = 1): Comparator =>
  (a, b) => (sel(a) ?? "").toString().toLocaleLowerCase()
    .localeCompare((sel(b) ?? "").toString().toLocaleLowerCase()) * dir;

const byNumber = (sel: (c: Course) => number | null | undefined, dir: 1 | -1 = 1): Comparator =>
  (a, b) => {
    const A = sel(a), B = sel(b);
    const aNa = A === null || A === undefined || Number.isNaN(A as number);
    const bNa = B === null || B === undefined || Number.isNaN(B as number);
    if (aNa && bNa) return 0;
    if (aNa) return 1;
    if (bNa) return -1;
    return ((A as number) - (B as number)) * dir;
  };

const byDate = (sel: (c: Course) => string | undefined, dir: 1 | -1 = 1): Comparator =>
  (a, b) => {
    const aT = (sel(a) ? Date.parse(sel(a) as string) : NaN);
    const bT = (sel(b) ? Date.parse(sel(b) as string) : NaN);
    const aNa = Number.isNaN(aT), bNa = Number.isNaN(bT);
    if (aNa && bNa) return 0;
    if (aNa) return 1;
    if (bNa) return -1;
    return (aT - bT) * dir;
  };

const LOCAL_ORDERING: Record<string, Comparator> = {
  "title": byString((c) => (c as any).title, +1),
  "-title": byString((c) => (c as any).title, -1),
  "price": byNumber((c) => priceValue(c), +1),
  "-price": byNumber((c) => priceValue(c), -1),
  "created_at": byDate((c) => (c as any).created_at, +1),
  "-created_at": byDate((c) => (c as any).created_at, -1),
};

const ORDERING_OPTIONS = [
  { label: "Più recenti", value: "-created_at" },
  { label: "Titolo (A→Z)", value: "title" },
  { label: "Titolo (Z→A)", value: "-title" },
  { label: "Prezzo ↑", value: "price" },
  { label: "Prezzo ↓", value: "-price" },
];

export default function CoursesList() {
  const { getQuery, setQuery } = useQueryState<{ page?: number; search?: string; ordering?: string; category?: string }>({
    page: 1,
    search: "",
    ordering: "",
    category: "",
  });

  // Query dall’URL
  const q = getQuery();
  const page = typeof q.page === "number" && q.page > 0 ? q.page : 1;
  const search = (q.search ?? "") as string;
  const ordering = (q.ordering ?? "") as string;
  const category = (q.category ?? "") as string | undefined;

  // Stato locale controllato per l’input di ricerca
  const [searchInput, setSearchInput] = React.useState<string>(search);
  React.useEffect(() => { setSearchInput(search); }, [search]);

  const [items, setItems] = React.useState<Course[]>([]);
  const [count, setCount] = React.useState<number | undefined>(undefined);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);

  async function load(p = page, s = search, o = ordering, cat = category) {
    setLoading(true);
    setError(null);

    const params: ListParams = { page: p, page_size: PAGE_SIZE };
    if (s) params.search = s;
    if (o) params.ordering = o;
    if (cat) params.category = cat;

    const res = await listCourses(params);
    if (!res.ok) {
      setError(`Impossibile caricare i corsi (status ${res.status}).`);
      setItems([]);
      setCount(undefined);
      setLoading(false);
      return;
    }

    // Fallback client-side: filtro categoria se il BE lo ignorasse
    let list = res.data.slice();
    if (cat) {
      list = list.filter((c) => courseCategorySlug(c) === slugify(cat));
    }

    // Ordinamento locale (sulla pagina)
    const cmp = LOCAL_ORDERING[o];
    if (cmp) list.sort(cmp);

    setItems(list);
    setCount((res as any).count);
    setLoading(false);
  }

  React.useEffect(() => {
    load(page, search, ordering, category);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, search, ordering, category]);

  function onSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    const value = searchInput.trim();
    setQuery({ page: 1, search: value || undefined });
  }

  function onOrderingChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = e.target.value;
    setQuery({ page: 1, ordering: value || undefined });
  }

  function onCategoryChange(value?: string) {
    setQuery({ page: 1, category: value || undefined });
  }

  function toPage(p: number) { setQuery({ page: p }); }

  return (
    <section className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <h1 className="text-xl font-semibold">Catalogo corsi</h1>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <form onSubmit={onSearchSubmit} className="flex items-center gap-2">
            <input
              type="search"
              name="q"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Cerca corso…"
              className="h-9 rounded-md border bg-background px-3 outline-none focus:ring-2 focus:ring-primary"
            />
            <button type="submit" className="inline-flex h-9 items-center rounded-md border px-3 hover:bg-accent" disabled={loading}>
              Cerca
            </button>
          </form>

          <CategoryFilter value={category} onChange={onCategoryChange} />

          <select
            value={ordering}
            onChange={onOrderingChange}
            className="h-9 rounded-md border bg-background px-2 text-sm"
            title="Ordina"
          >
            <option value="">Ordina…</option>
            {ORDERING_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
      </header>

      {loading && !items.length && <div className="text-sm text-muted-foreground">Caricamento in corso…</div>}
      {error && <div className="text-sm text-red-600">{error}</div>}

      {!loading && !error && items.length === 0 && (
        <div className="rounded-lg border p-8 text-center">
          <p className="text-sm text-muted-foreground">Nessun corso trovato.</p>
        </div>
      )}

      {!error && items.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((c) => (
              <div key={c.id} className="space-y-2">
                <CourseCard course={c} />
                {!isEnrolled(c) && (
                  <div onClick={(e) => e.stopPropagation()}>
                    <BuyCourseButton
                      courseId={c.id}
                      className="inline-flex items-center rounded-lg bg-primary px-3 py-2 text-primary-foreground hover:opacity-90"
                      stopPropagation
                      useNavigateMode
                    >
                      Compra
                    </BuyCourseButton>
                  </div>
                )}
              </div>
            ))}
          </div>

          <Pagination className="pt-4" page={page} pageSize={PAGE_SIZE} total={count} onPageChange={toPage} />
        </>
      )}
    </section>
  );
}
