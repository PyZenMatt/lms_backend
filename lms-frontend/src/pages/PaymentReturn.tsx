// src/pages/PaymentReturn.tsx
import React from "react"
import { useLocation, useNavigate, Link } from "react-router-dom"
import { confirmStripePaymentSmart, purchaseCourse } from "../services/payments"
import { getCourse } from "../services/courses"

function useQS() {
  const { search } = useLocation()
  return React.useMemo(() => new URLSearchParams(search), [search])
}

function isEnrolledFlag(course: any): boolean {
  const v = course?.is_enrolled
  return v === true || v === "true" || v === 1
}

async function pollEnrollment(courseId: number, tries = 6, delayMs = 1500): Promise<boolean> {
  for (let i = 0; i < tries; i++) {
    const res = await getCourse(courseId)
    if (res.ok && isEnrolledFlag(res.data)) return true
    await new Promise(r => setTimeout(r, delayMs))
  }
  return false
}

export default function PaymentReturn() {
  const qs = useQS()
  const navigate = useNavigate()

  const paymentIntent = qs.get("payment_intent") || undefined
  const piClientSecret = qs.get("payment_intent_client_secret") || undefined
  const courseParam = qs.get("course") || undefined
  const redirectStatus = qs.get("redirect_status") || undefined
  const courseId = courseParam ? Number(courseParam) : undefined

  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [statusText, setStatusText] = React.useState<string>("in attesa di verifica")
  const [step, setStep] = React.useState<"init" | "confirm" | "fallback" | "poll" | "done">("init")
  const [serverMsg, setServerMsg] = React.useState<string | null>(null)

  async function runFlow() {
    setBusy(true)
    setError(null)
    setServerMsg(null)
    setStatusText("Inizio verifica pagamento…")

    try {
      if (!paymentIntent || !courseId) {
        setError("Informazioni incomplete nel ritorno da Stripe (manca payment_intent o course).")
        setBusy(false)
        return
      }

      // 1) Conferma “smart”
      setStep("confirm")
      setStatusText("Conferma pagamento lato server…")
      const confirmRes = await confirmStripePaymentSmart(courseId, {
        payment_intent: paymentIntent,
        payment_intent_client_secret: piClientSecret || undefined,
        redirect_status: redirectStatus || undefined,
      })

      if (confirmRes.ok) {
        setServerMsg(confirmRes.data.status || "ok")
        setStatusText("Verifico l'iscrizione…")
        setStep("poll")
        const ok = await pollEnrollment(confirmRes.data.course_id ?? courseId, 8, 1200)
        if (ok) {
          setStatusText("Enrollment confermato, reindirizzo al corso…")
          setStep("done")
          setBusy(false)
          setTimeout(() => navigate(`/courses/${courseId}`), 700)
          return
        }
        // se non appare subito, continuo col fallback
      } else if (confirmRes.status !== 400 && ![404, 405, 501].includes(confirmRes.status)) {
        setError(`Errore conferma pagamento (HTTP ${confirmRes.status}).`)
        setBusy(false)
        return
      }

      // 2) Fallback: purchase/ con method: "stripe"
      setStep("fallback")
      setStatusText("Conferma alternativa (purchase) in corso…")
      const purchaseRes = await purchaseCourse(courseId, {
        method: "stripe",
        payment_intent: paymentIntent,
      })
      if (!purchaseRes.ok && ![404, 405, 501].includes((purchaseRes as any).status ?? 0)) {
        setError(`Errore nella conferma alternativa (HTTP ${purchaseRes.status}).`)
        setBusy(false)
        return
      }

      // 3) Poll finale dell’enrollment (anche se purchase ha risposto 200, potrebbe essere async)
      setStep("poll")
      setStatusText("Aggiorno lo stato d'iscrizione…")
      const ok = await pollEnrollment(courseId, 8, 1200)
      if (ok) {
        setStatusText("Enrollment confermato, reindirizzo al corso…")
        setStep("done")
        setBusy(false)
        setTimeout(() => navigate(`/courses/${courseId}`), 700)
        return
      }

      // 4) Avviso all’utente se non riusciamo a determinare l’iscrizione
      const msg = confirmRes.status === 400
        ? "Conferma non accettata dal server (400). Potrebbe mancare un campo nel payload; riprova più tardi o contatta il supporto."
        : "Verifica non disponibile lato server. Il pagamento è riuscito, l'iscrizione potrebbe richiedere qualche istante."
      setError(msg)
      setBusy(false)
    } catch (e: any) {
      setError(e?.message || "Errore imprevisto nella verifica.")
      setBusy(false)
    }
  }

  React.useEffect(() => {
    runFlow()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="max-w-xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Ritorno da Stripe</h1>

      <div className="rounded-xl border p-4 space-y-1 text-sm">
        <div>Stato redirect: <b>{redirectStatus || "sconosciuto"}</b></div>
        <div>Payment Intent: <b>{paymentIntent || "—"}</b></div>
        <div>Corso: <b>{courseId ?? "—"}</b></div>
        <div>Fase: <b>{step}</b></div>
        {serverMsg && <div>Server: <b>{serverMsg}</b></div>}
      </div>

      {busy && (
        <div className="rounded-xl border p-4 text-sm">{statusText}</div>
      )}

      {!busy && error && (
        <div className="rounded-xl border border-yellow-300/50 bg-yellow-50 text-yellow-900 p-4 text-sm space-y-2">
          <div>{error}</div>
          <div className="flex gap-3">
            {courseId ? (
              <Link className="underline" to={`/courses/${courseId}`}>Vai al corso</Link>
            ) : (
              <Link className="underline" to="/courses">Vai al catalogo</Link>
            )}
            <button className="underline" onClick={() => runFlow()}>
              Riprova verifica
            </button>
          </div>
        </div>
      )}

      {!busy && !error && (
        <div className="rounded-xl border p-4 text-sm">
          {statusText}
        </div>
      )}
    </div>
  )
}
