// src/pages/Dashboard.tsx
import React from "react";
import { getEnrolledCourses } from "../services/student";
import type { Course } from "../types/course";
import CourseCard from "../components/CourseCard";
import EmptyState from "../components/EmptyState";

export default function Dashboard() {
  const [courses, setCourses] = React.useState<Course[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    const res = await getEnrolledCourses();
    if (!res.ok) {
      setError(`Impossibile caricare i corsi (status ${res.status}).`);
      setCourses([]);
    } else {
      setCourses(res.data);
    }
    setLoading(false);
  }

  React.useEffect(() => {
    load();
  }, []);

  return (
    <section className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">La tua dashboard</h1>
        <button onClick={load} className="inline-flex h-9 items-center rounded-md border px-3 hover:bg-accent">
          Ricarica
        </button>
      </header>

      {loading && <div className="text-sm text-muted-foreground">Caricamento in corso…</div>}
      {error && <div className="text-sm text-red-600">{error}</div>}

      {!loading && !error && courses.length === 0 && (
        <EmptyState
          title="Non sei iscritto ad alcun corso"
          description="Quando ti iscriverai a un corso, lo troverai qui."
        />
      )}

      {!loading && !error && courses.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {courses.map((c) => (
            <CourseCard key={c.id} course={c} showProgress />
          ))}
        </div>
      )}
    </section>
  );
}
