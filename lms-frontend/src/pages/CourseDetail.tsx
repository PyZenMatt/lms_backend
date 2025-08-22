// src/pages/CourseDetail.tsx
import React from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import BuyCourseButton from "../components/BuyCourseButton";

type Course = {
  id: number;
  title: string;
  description?: string;
  cover_image?: string;
  cover_image_url?: string;
  cover_url?: string;
  price_eur?: number | null;
  is_enrolled?: boolean | "true" | "false" | null;
};

const fmtEUR = (v?: number | null) =>
  typeof v === "number"
    ? new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(v)
    : "—";

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
      if (res.ok) setCourse(res.data);
      setLoading(false);
    }
    load();
    return () => {
      mounted = false;
    };
  }, [courseId]);

  const enrolled =
    course?.is_enrolled === true ||
    course?.is_enrolled === "true" ||
    (course as any)?.is_enrolled === 1;

  const cover = course?.cover_image ?? course?.cover_image_url ?? course?.cover_url;

  if (!Number.isFinite(courseId)) return <div className="p-6">ID corso non valido.</div>;

  return (
    <div className="space-y-4">
      {loading && <div>Caricamento…</div>}
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
                {course.description ?? "—"}
              </div>
              <div className="text-base font-medium">
                {fmtEUR(course.price_eur ?? null)}
              </div>

              {!enrolled && (
                <div className="pt-2">
                  <BuyCourseButton
                    courseId={courseId}
                    // stesso stile del tuo bottone originale
                    className="h-10 rounded-lg bg-primary px-4 text-primary-foreground hover:opacity-90 inline-flex items-center"
                    // in caso la card fosse cliccabile, evita bubbling
                    stopPropagation
                    // usa navigate interno per evitare conflitti con wrapper <Link>
                    useNavigateMode
                  >
                    Acquista
                  </BuyCourseButton>
                </div>
              )}
            </div>
          </div>
        </>
      )}
      {!loading && !course && <div>Corso non trovato.</div>}
    </div>
  );
}
