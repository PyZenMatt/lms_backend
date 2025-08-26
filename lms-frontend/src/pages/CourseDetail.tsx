// src/pages/CourseDetail.tsx
import React from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import BuyCourseButton from "../components/BuyCourseButton";
import { Spinner } from "../components/ui/spinner";
import EmptyState from "../components/EmptyState";

type Course = {
  id: number;
  title: string;
  description?: string;
  cover_image?: string;
  cover_image_url?: string;
  cover_url?: string;
  price_eur?: number | null;
  is_enrolled?: boolean | "true" | "false" | 1 | 0 | null;
};

const fmtEUR = (v?: number | null) =>
  typeof v === "number"
    ? new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(v)
    : "—";

function isEnrolledFlag(v: Course["is_enrolled"]): boolean {
  const s = String(v);
  return s === "true" || s === "1";
}

export default function CourseDetail() {
  const { id } = useParams<{ id: string }>();
  const courseId = Number(id);

  const [loading, setLoading] = React.useState(true);
  const [course, setCourse] = React.useState<Course | null>(null);

  React.useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      const res = await api.get<Course>(`/v1/courses/${courseId}/`);
      if (!mounted) return;
  if (res.ok) setCourse(res.data ?? null);
      setLoading(false);
    }
    load();
    return () => { mounted = false; };
  }, [courseId]);

  if (!Number.isFinite(courseId)) return <div className="p-6">ID corso non valido.</div>;

  const enrolled = isEnrolledFlag(course?.is_enrolled ?? null);
  const cover = course?.cover_image ?? course?.cover_image_url ?? course?.cover_url;

  return (
    <div className="space-y-4">
      {loading && (
        <div className="flex items-center gap-3">
          <Spinner />
          <span className="text-sm text-muted-foreground">Caricamento…</span>
        </div>
      )}
      {!loading && course && (
        <>
          <div className="flex flex-col gap-4 md:flex-row">
            {cover && (
              <img
                src={cover}
                alt=""
                className="aspect-[16/9] w-full max-w-2xl rounded-xl object-cover"
              />
            )}
            <div className="flex-1 space-y-2">
              <h1 className="text-2xl font-semibold">{course.title}</h1>
              <div className="text-sm text-muted-foreground">
                {course.description || "—"}
              </div>
              <div className="text-base font-medium">{fmtEUR(course.price_eur ?? null)}</div>

              <div className="pt-2 flex items-center gap-2">
                {enrolled ? (
                  <Link
                    to={`/learn/${courseId}`}
                    className="h-10 inline-flex items-center rounded-lg bg-muted px-4 hover:opacity-90"
                    data-testid="go-to-course"
                  >
                    Vai al corso
                  </Link>
                ) : (
                  <BuyCourseButton
                    courseId={courseId}
                    className="h-10 inline-flex items-center rounded-lg bg-primary px-4 text-primary-foreground hover:opacity-90"
                  >
                    Acquista
                  </BuyCourseButton>
                )}
              </div>
            </div>
          </div>
        </>
      )}
  {!loading && !course && <EmptyState title="Corso non trovato" description="Il corso richiesto non esiste o è stato rimosso." />}
    </div>
  );
}
