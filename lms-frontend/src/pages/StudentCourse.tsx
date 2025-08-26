// src/pages/StudentCourse.tsx
import React from "react"
import { Link, useParams } from "react-router-dom"
import { api } from "../lib/api"
import { getCourseBatchData, listCourseLessons } from "../services/exercises"
import { Spinner } from "../components/ui/spinner"
import { Alert } from "../components/ui/alert"
import EmptyState from "../components/ui/empty-state"

type Course = {
  id: number
  title: string
  description?: string | null
}

type Lesson = {
  id: number
  title: string
  duration_min?: number | null
  is_completed?: boolean
  order?: number
}

type Module = {
  id: number
  title: string
  order?: number
  lessons?: Lesson[]
}

type Progress = {
  percent?: number // 0..100
  completed_lessons?: number
  total_lessons?: number
}

function clamp(n?: number | null, min = 0, max = 100) {
  if (typeof n !== "number" || Number.isNaN(n)) return 0
  return Math.max(min, Math.min(max, n))
}

export default function StudentCourse() {
  const { id } = useParams<{ id: string }>()
  const courseId = Number(id)

  const [loading, setLoading] = React.useState(true)
  const [course, setCourse] = React.useState<Course | null>(null)
  const [modules, setModules] = React.useState<Module[]>([])
  const [progress, setProgress] = React.useState<Progress>({})
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    let mounted = true
    async function load() {
      setLoading(true)
      setError(null)

      // 1) corso base
      // Prefer batch endpoint that returns course + lessons + progress
      const batch = await getCourseBatchData(courseId)
         let hadModulesFromBatch = false
         if (mounted && batch.ok && batch.data) {
           const dObj = batch.data as unknown as Record<string, unknown>
           const title = (dObj["title"] ?? dObj["name"]) as string | undefined
           const description = dObj["description"] as string | undefined
           setCourse({ id: Number(dObj["id"] ?? courseId), title: title ?? `Corso #${courseId}`, description: description ?? null })
           // Normalize modules/lessons if present
           const mods: Module[] = []
           if (Array.isArray(dObj.modules)) {
             for (const m of dObj.modules as unknown[]) {
               const mObj = m as Record<string, unknown>
               const lessonsArr = Array.isArray(mObj["lessons"]) ? (mObj["lessons"] as unknown[]) : []
               mods.push({
                 id: Number(mObj["id"] ?? mObj["pk"] ?? Math.random() * 1e9),
                 title: String(mObj["title"] ?? mObj["name"] ?? "Modulo"),
                 order: Number(mObj["order"] ?? mObj["position"] ?? 0),
                 lessons: lessonsArr.map((l) => {
                   const lObj = l as Record<string, unknown>
                   return {
                     id: Number(lObj["id"] ?? lObj["pk"] ?? Math.random() * 1e9),
                     title: String(lObj["title"] ?? lObj["name"] ?? "Lezione"),
                     duration_min: typeof lObj["duration_min"] === "number" ? (lObj["duration_min"] as number) : undefined,
                     is_completed: !!(lObj["is_completed"] ?? lObj["completed"]),
                     order: Number(lObj["order"] ?? lObj["position"] ?? 0),
                   } as Lesson
                 }),
               })
             }
           }
           if (mods.length) {
             // Try to apply any transient completion flags stored in sessionStorage
             try {
               if (typeof window !== "undefined" && typeof window.sessionStorage !== "undefined") {
                 // iterate via index/key to be compatible across browsers
                 for (let i = 0; i < sessionStorage.length; i++) {
                   const k = sessionStorage.key(i)
                   if (!k || !k.startsWith("lesson_completed_")) continue
                   const lId = Number(k.replace("lesson_completed_", ""))
                   const storedCourse = sessionStorage.getItem(k)
                   if (!Number.isFinite(lId)) continue
                   if (storedCourse && Number(storedCourse) !== courseId) continue
                   // mark found lesson completed in mods
                   for (let mi = 0; mi < mods.length; mi++) {
                     const m = mods[mi]
                     if (!m.lessons) continue
                     mods[mi] = {
                       ...m,
                       lessons: m.lessons.map((ls) => (ls.id === lId ? { ...ls, is_completed: true } : ls)),
                     }
                   }
                   // remove applied key
                   sessionStorage.removeItem(k)
                   // adjust index because we removed an item
                   i--
                 }
               }
             } catch {
               // ignore storage errors
             }
             setModules(mods)
             hadModulesFromBatch = true
           }
        // progress
        const prog = dObj["progress"] as Record<string, unknown> | undefined
        if (prog) {
          const percent = typeof (prog["percent"] as unknown) === "number" ? (prog["percent"] as number)
            : typeof (prog["progress"] as unknown) === "number" ? (prog["progress"] as number)
            : undefined
          const completed_lessons = (prog["completed_lessons"] ?? prog["completed"]) as number | undefined
          const total_lessons = (prog["total_lessons"] ?? prog["total"]) as number | undefined
          setProgress({ percent, completed_lessons, total_lessons })
        }
      } else {
        // fallback: course detail endpoint
        const cRes = await api.get<Course>(`/v1/courses/${courseId}/`)
        if (mounted && cRes.ok && cRes.data) setCourse(cRes.data)
      }

      // If batch returned no modules, try listing lessons as fallback
      if (mounted && !hadModulesFromBatch) {
        const lessonsRes = await listCourseLessons(courseId)
        if (lessonsRes.ok) {
          // group lessons into a single implicit module
          const lessons = (lessonsRes.data ?? []) as unknown[]
          setModules([{ id: courseId, title: "Lezioni", lessons: lessons.map((l) => {
            const lObj = l as Record<string, unknown>
            return {
              id: Number(lObj["id"] ?? lObj["pk"] ?? Math.random() * 1e9),
              title: String(lObj["title"] ?? lObj["name"] ?? "Lezione"),
              duration_min: typeof lObj["duration_min"] === "number" ? (lObj["duration_min"] as number) : undefined,
              is_completed: !!(lObj["is_completed"] ?? lObj["completed"]),
            } as Lesson
          }) }])
        }
      }

  // NOTE: esercizi rimossi dalla vista corso (gestiti separatamente nella pagina Lezione / MyExercises)

      if (mounted) setLoading(false)
    }
    load()
    return () => { mounted = false }
  }, [courseId])

  // Update UI immediately when a lesson is marked complete elsewhere
  React.useEffect(() => {
    function onLessonCompleted(ev: Event) {
      const detail = (ev as CustomEvent)?.detail as { lessonId?: number; courseId?: number } | undefined
      if (!detail || !detail.lessonId) return
  // If event carries courseId and it doesn't match current course, ignore
  if (typeof detail.courseId !== "undefined" && Number(detail.courseId) !== courseId) return
      const lId = Number(detail.lessonId)
      setModules((prev) => {
        let changed = false
        const next = prev.map((m) => {
          const lessons = (m.lessons ?? []).map((ls) => {
            if (ls.id === lId && !ls.is_completed) {
              changed = true
              return { ...ls, is_completed: true }
            }
            return ls
          })
          return lessons === (m.lessons ?? []) ? m : { ...m, lessons }
        })
        return changed ? next : prev
      })
      // optionally adjust progress
      setProgress((p) => {
        const completed = typeof p.completed_lessons === "number" ? (p.completed_lessons ?? 0) + 1 : undefined
        const total = typeof p.total_lessons === "number" ? p.total_lessons : undefined
        const percent = typeof completed === "number" && typeof total === "number" && total > 0 ? Math.min(100, Math.round((completed / total) * 100)) : p.percent
        return { percent, completed_lessons: completed, total_lessons: total }
      })
    }

    if (typeof window !== "undefined" && typeof window.addEventListener === "function") {
      window.addEventListener("lesson:completed", onLessonCompleted as EventListener)
      return () => window.removeEventListener("lesson:completed", onLessonCompleted as EventListener)
    }
    return undefined
  }, [courseId])

  if (!Number.isFinite(courseId)) return <div className="p-6">ID corso non valido.</div>

  const p = clamp(progress.percent ?? 0)

  return (
    <div className="mx-auto max-w-5xl p-6 space-y-8">
      {/* Header corso */}
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">{course?.title ?? `Corso #${courseId}`}</h1>
        <div className="text-sm text-muted-foreground">{course?.description || "—"}</div>
        <div className="mt-2">
          <div className="h-2 w-full rounded-full bg-muted">
            <div className="h-2 rounded-full bg-primary transition-all" style={{ width: `${p}%` }} />
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            Progresso: <b>{p}%</b>
            {typeof progress.completed_lessons === "number" && typeof progress.total_lessons === "number" && (
              <>{progress.completed_lessons}/{progress.total_lessons} lezioni</>
            )}
          </div>
        </div>
      </header>

      {/* Moduli & Lezioni */}
      <section className="space-y-3">
        <h2 className="text-lg font-medium">Contenuti del corso</h2>
        {loading && (
          <div className="flex items-center gap-3">
            <Spinner />
            <span className="text-sm text-muted-foreground">Caricamento contenuti…</span>
          </div>
        )}
        {!loading && modules.length === 0 && (
          <EmptyState title="Nessun contenuto" description="Non ci sono moduli o lezioni disponibili per questo corso." />
        )}
        {!loading && modules.length > 0 && (
          <div className="space-y-3">
            {modules
              .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
              .map((m) => (
                <div key={m.id} className="rounded-xl border">
                  <div className="border-b p-3 font-medium">{m.title}</div>
                  <ul className="divide-y">
                    {(m.lessons ?? [])
                      .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                      .map((l) => (
                        <li key={l.id} className="flex items-center justify-between p-3">
                          <div className="min-w-0">
                            <div className="truncate text-sm">{l.title}</div>
                            <div className="text-xs text-muted-foreground">
                              {l.duration_min ? `${l.duration_min} min` : "—"} • {l.is_completed ? "Completa" : "Da completare"}
                            </div>
                          </div>
                          <Link
                            to={`/lessons/${l.id}`}
                            className="rounded-lg border px-3 py-1 text-sm hover:bg-accent"
                          >
                            Apri
                          </Link>
                        </li>
                      ))}
                  </ul>
                </div>
              ))}
          </div>
        )}
      </section>

  {/* Esercizi rimossi dalla vista corso */}

  {error && <Alert variant="warning" title="Attenzione">{error}</Alert>}
    </div>
  )
}
