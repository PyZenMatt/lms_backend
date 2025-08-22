// src/pages/ExerciseSubmit.tsx
import React from "react"
import { useParams } from "react-router-dom"
import { getExercise, submitExercise, getMySubmission } from "../services/exercises"

export default function ExerciseSubmit() {
  const { id } = useParams<{ id: string }>()
  const exerciseId = Number(id)

  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [title, setTitle] = React.useState<string>("")
  const [description, setDescription] = React.useState<string>("—")
  const [status, setStatus] = React.useState<string>("")
  const [reviewsCount, setReviewsCount] = React.useState<number | null>(null)
  const [text, setText] = React.useState<string>("")
  const [files, setFiles] = React.useState<File[]>([])
  const [submitting, setSubmitting] = React.useState(false)
  const [submittedMsg, setSubmittedMsg] = React.useState<string | null>(null)
  const [hasSubmitted, setHasSubmitted] = React.useState<boolean>(false)

  React.useEffect(() => {
    let mounted = true
    async function load() {
      setLoading(true)
      setError(null)
      const res = await getExercise(exerciseId)
      if (!mounted) return
      if (!res.ok) {
        setError(`Impossibile caricare l'esercizio (HTTP ${res.status})`)
      } else {
        setTitle(res.data.title ?? `Esercizio #${exerciseId}`)
        setDescription(res.data.description || "—")
        setStatus(res.data.status ?? "")
      }
      // try to get my submission and reviews count
      const my = await getMySubmission(exerciseId)
      if (my.ok && my.data) {
        const d = my.data as Record<string, unknown>
  // If there's a submission object, mark as already submitted
  setHasSubmitted(true)
        // prefer explicit reviews array
        if (Array.isArray(d.reviews)) setReviewsCount(d.reviews.length)
        else if (typeof d.reviews_count === "number") setReviewsCount(d.reviews_count)
        else if (typeof d.review_count === "number") setReviewsCount(d.review_count)
        else setReviewsCount(null)
      }
      setLoading(false)
    }
    load()
    return () => { mounted = false }
  }, [exerciseId])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setSubmittedMsg(null)
    setError(null)
    const res = await submitExercise(exerciseId, { text: text?.trim() || undefined, files })
    setSubmitting(false)
    if (!res.ok) {
      setError(`Invio non riuscito (HTTP ${res.status}). Controlla i campi e riprova.`)
      return
    }
  setSubmittedMsg("Consegna inviata correttamente. Non potrai più inviare una nuova consegna per questo esercizio.")
    setText("")
    setFiles([])
  setHasSubmitted(true)
  }

  return (
    <div className="mx-auto max-w-3xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold">{title}</h1>

      {loading && <div className="text-sm text-muted-foreground">Caricamento…</div>}
      {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {submittedMsg && <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{submittedMsg}</div>}

      {!loading && !error && (
        <>
          <div className="rounded-lg border p-4">
            <div className="text-sm text-muted-foreground whitespace-pre-wrap">{description}</div>
            <div className="mt-2 text-xs text-muted-foreground">Stato corrente: <b>{status || "—"}</b></div>
          </div>

          {!hasSubmitted ? (
            <form onSubmit={onSubmit} className="space-y-3">
            <div>
              <label className="mb-1 block text-sm font-medium">Risposta (testo)</label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Scrivi qui la tua risposta…"
                className="min-h-[120px] w-full rounded-lg border p-3"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">Allegati (opzionali)</label>
              <input
                type="file"
                multiple
                onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
                className="block w-full text-sm"
              />
              {files.length > 0 && (
                <div className="mt-1 text-xs text-muted-foreground">{files.length} file selezionati</div>
              )}
            </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={submitting || (status === "submitted" && (reviewsCount === null || reviewsCount < 3))}
                  className="rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50"
                  title={status === "submitted" && (reviewsCount === null || reviewsCount < 3) ? "La tua consegna è in attesa di valutazioni: non puoi reinviare finché non riceve 3 valutazioni." : undefined}
                >
                  {submitting ? "Invio in corso…" : "Invia esercizio"}
                </button>
              </div>
            </form>
          ) : (
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800">Hai già inviato questo esercizio. Non puoi inviare nuovamente.</div>
          )}
        </>
      )}
    </div>
  )
}
