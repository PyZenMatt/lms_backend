// src/pages/CourseCheckout.tsx
import React from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { getPaymentSummary, createPaymentIntent, purchaseCourse } from "../services/payments"
import { getCourse } from "../services/courses"
import { loadStripe } from "@stripe/stripe-js"
import type { Stripe } from "@stripe/stripe-js"
import { Elements, PaymentElement, useElements, useStripe } from "@stripe/react-stripe-js"

type SummaryState = {
  price_eur?: number
  discount_percent?: number
  total_eur?: number
  teo_required?: number
  currency?: string
}

function maskKey(pk?: string | null) {
  if (!pk) return "(none)"
  if (pk.length <= 10) return pk
  return `${pk.slice(0, 10)}…${pk.slice(-4)}`
}

function getPublishableKeyFromEnv(): string | null {
  // preferisci .env Vite
  const pk = (import.meta as any).env?.VITE_STRIPE_PUBLISHABLE_KEY || (window as any)?.VITE_STRIPE_PUBLISHABLE_KEY
  return typeof pk === "string" ? pk : null
}

export default function CourseCheckout() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const courseId = Number(id)

  const [loading, setLoading] = React.useState(true)
  const [submitting, setSubmitting] = React.useState<null | "card" | "teo">(null)
  const [error, setError] = React.useState<string | null>(null)
  const [title, setTitle] = React.useState<string>("")
  const [summary, setSummary] = React.useState<SummaryState>({})

  // Stripe state
  const [clientSecret, setClientSecret] = React.useState<string | null>(null)
  const [publishableKey, setPublishableKey] = React.useState<string | null>(null)

  const [studentAddress, setStudentAddress] = React.useState<string>("")

  React.useEffect(() => {
    let mounted = true
    ;(async () => {
      setLoading(true)
      setError(null)
      const [s, c] = await Promise.all([getPaymentSummary(courseId), getCourse(courseId)])
      if (!mounted) return
      if (s.ok) {
        setSummary({
          price_eur: s.data.price_eur,
          discount_percent: s.data.discount_percent,
          total_eur: s.data.total_eur,
          teo_required: s.data.teo_required,
          currency: s.data.currency || "EUR",
        })
      }
      setTitle(c.ok ? (c.data.title ?? `Corso #${courseId}`) : `Corso #${courseId}`)
      setLoading(false)
    })()
    return () => {
      mounted = false
    }
  }, [courseId])

  async function onPayCard() {
    setSubmitting("card")
    setError(null)

    // 1) Publishable key (pk_test...) dal .env
    const envPk = getPublishableKeyFromEnv()
    if (!envPk) {
      setSubmitting(null)
      setError(
        "Publishable key Stripe mancante. Aggiungi VITE_STRIPE_PUBLISHABLE_KEY=pk_test_... nel .env e riavvia il dev server."
      )
      return
    }
    if (!/^pk_(test|live)_/.test(envPk)) {
      setSubmitting(null)
      setError(
        "Publishable key non valida. Deve iniziare con pk_test_ (in modalità test) o pk_live_."
      )
      return
    }

    // 2) Creo l'intent sul BE (restituisce client_secret)
    const res = await createPaymentIntent(courseId, {})
    setSubmitting(null)

    if (!res.ok) {
      setError(`Creazione pagamento fallita (HTTP ${res.status})`)
      return
    }
    // Caso Checkout Session → redirect
    if (res.checkout_url) {
      window.location.href = res.checkout_url
      return
    }
    // Caso Payment Intent → Elements
    const pk = res.publishable_key || envPk
    // Debug non sensibile (mascherato)
    console.debug("[Stripe] publishableKey:", maskKey(pk), "clientSecret:", res.client_secret ? "present" : "missing")

    if (res.client_secret && pk) {
      setPublishableKey(pk)
      setClientSecret(res.client_secret)
      return
    }

    setError("Il server non ha fornito dati di pagamento utilizzabili (client_secret assente).")
  }

  async function onPayTeo() {
    setSubmitting("teo")
    setError(null)
    const res = await purchaseCourse(courseId, {
      method: "teocoin",
      student_address: studentAddress || undefined,
    })
    setSubmitting(null)
    if (!res.ok) {
      setError(`Acquisto con TeoCoin fallito (HTTP ${res.status})`)
      return
    }
    navigate(`/courses/${courseId}`)
  }

  if (loading) return <div className="p-6">Caricamento…</div>

  const showSummary =
    summary.price_eur !== undefined ||
    summary.total_eur !== undefined ||
    summary.teo_required !== undefined

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Checkout corso</h1>
        <p className="text-sm opacity-80">
          <Link to={`/courses/${courseId}`} className="underline">
            {title || `Corso #${courseId}`}
          </Link>
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-300/40 bg-red-50 text-red-800 p-4">
          {error}
        </div>
      )}

      <div className="rounded-2xl border p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="text-sm opacity-70">Riepilogo</div>
          {showSummary ? (
            <>
              {summary.price_eur !== undefined && (
                <div className="text-sm">
                  Prezzo: <b>{summary.price_eur.toFixed(2)} {summary.currency || "EUR"}</b>
                </div>
              )}
              {(summary.discount_percent ?? 0) > 0 && (
                <div className="text-sm text-emerald-700">Sconto {summary.discount_percent}%</div>
              )}
              {summary.total_eur !== undefined && (
                <div className="text-sm">
                  Totale: <b>{summary.total_eur.toFixed(2)} {summary.currency || "EUR"}</b>
                </div>
              )}
              {summary.teo_required !== undefined && (
                <div className="text-sm">Oppure <b>{summary.teo_required} TEO</b></div>
              )}
            </>
          ) : (
            <div className="text-sm opacity-70">
              Riepilogo non disponibile — puoi procedere al pagamento.
            </div>
          )}
        </div>

        <div className="space-y-4">
          {!clientSecret ? (
            <>
              <button
                onClick={onPayCard}
                disabled={!!submitting}
                className="w-full rounded-xl px-4 py-2 border bg-black text-white disabled:opacity-50"
              >
                {submitting === "card" ? "Creo pagamento…" : "Paga con carta (Stripe)"}
              </button>

              {summary.teo_required !== undefined && (
                <div className="space-y-2">
                  <input
                    type="text"
                    placeholder="Wallet address (opzionale)"
                    value={studentAddress}
                    onChange={(e) => setStudentAddress(e.target.value)}
                    className="w-full rounded-xl border px-3 py-2"
                  />
                  <button
                    onClick={onPayTeo}
                    disabled={!!submitting}
                    className="w-full rounded-xl px-4 py-2 border bg-white disabled:opacity-50"
                  >
                    {submitting === "teo" ? "Processo in corso…" : "Paga con TeoCoin"}
                  </button>
                </div>
              )}
            </>
          ) : (
            <StripeElementsBlock
              clientSecret={clientSecret}
              publishableKey={publishableKey!}
              returnTo={`${window.location.origin}/payments/return?course=${courseId}`}
            />
          )}
        </div>
      </div>

      <div className="text-sm opacity-70">
        Al termine del pagamento verrai riportato alla pagina del corso.
      </div>
    </div>
  )
}

function StripeElementsBlock({
  clientSecret,
  publishableKey,
  returnTo,
}: {
  clientSecret: string
  publishableKey: string
  returnTo: string
}) {
  const stripePromise = React.useMemo<Promise<Stripe | null>>(
    () => loadStripe(publishableKey),
    [publishableKey]
  )

  return (
    <Elements
      stripe={stripePromise}
      options={{
        clientSecret,
        appearance: { theme: "stripe" },
        locale: "it",
      }}
    >
      <StripeCheckoutForm returnTo={returnTo} />
    </Elements>
  )
}

function StripeCheckoutForm({ returnTo }: { returnTo: string }) {
  const stripe = useStripe()
  const elements = useElements()
  const [busy, setBusy] = React.useState(false)
  const [err, setErr] = React.useState<string | null>(null)

  async function onConfirm(e: React.FormEvent) {
    e.preventDefault()
    if (!stripe || !elements) return
    setBusy(true)
    setErr(null)
    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: returnTo },
    })
    setBusy(false)
    if (error) setErr(error.message || "Errore nella conferma del pagamento.")
  }

  return (
    <form onSubmit={onConfirm} className="space-y-3">
      <PaymentElement onReady={() => console.debug("[Stripe] PaymentElement ready")} />
      {err && <div className="text-sm text-red-700">{err}</div>}
      <button
        type="submit"
        disabled={!stripe || !elements || busy}
        className="w-full rounded-xl px-4 py-2 border bg-black text-white disabled:opacity-50"
      >
        {busy ? "Elaboro…" : "Conferma pagamento"}
      </button>
    </form>
  )
}
