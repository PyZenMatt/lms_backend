// src/services/payments.ts
import { api } from "../lib/api"

/** =========================
 *  Tipi e helper comuni
 *  ========================= */
type Ok<T> = { ok: true; status: number; data: T }
type Err = { ok: false; status: number; error: any }
export type Result<T> = Ok<T> | Err

const asNumber = (v: any): number | undefined => {
  if (v === null || v === undefined) return undefined
  const n = Number(v)
  return Number.isFinite(n) ? n : undefined
}

const withQuery = (params?: Record<string, any>) => ({
  params: params ?? undefined,
  query: params ?? undefined,
})

/** =========================
 *  Tipi dominio pagamenti
 *  ========================= */
export type PaymentSummary = {
  course_id: number
  title?: string
  price_eur?: number
  discount_percent?: number
  total_eur?: number
  teo_required?: number
  currency?: string
  raw?: Record<string, any>
}

export type PaymentIntentInitResult = {
  ok: boolean
  status: number
  client_secret?: string
  publishable_key?: string
  checkout_url?: string
  raw?: any
  error?: any
}

export type VerificationData = {
  enrolled?: boolean
  course_id?: number
  payment_intent?: string
  status?: string // "succeeded" | "processing" | "requires_payment_method" | ...
  raw?: any
}

/** =========================
 *  API: Payment Summary
 *  ========================= */
export async function getPaymentSummary(
  courseId: number,
  params?: { discount_percent?: number; student_address?: string }
): Promise<Result<PaymentSummary>> {
  const res = await api.get<any>(`/v1/courses/${courseId}/payment-summary/`, withQuery(params as any))
  if (!res.ok) return { ok: false, status: res.status, error: (res as any).error }

  const raw = res.data ?? {}
  const pricing = (raw.pricing ?? raw.pricing_summary) as Record<string, any> | undefined
  const firstOption = Array.isArray(raw.pricing_options) && raw.pricing_options.length ? (raw.pricing_options[0] as Record<string, any>) : undefined

  const price_eur =
    asNumber(raw.price_eur ?? raw.price ?? raw.base_price ?? raw.original_price) ??
    asNumber(pricing?.original_price) ??
    asNumber(firstOption?.price) ??
    undefined

  const discount_percent = asNumber(raw.discount_percent ?? raw.discountPct ?? pricing?.discount_percent ?? firstOption?.discount_percent)

  const total_eur =
    asNumber(raw.total_eur ?? raw.total ?? raw.final_price) ??
    asNumber(pricing?.final_price) ??
    asNumber(firstOption?.final_price) ??
    undefined

  // Compute teo_required carefully: prefer explicit teocoin pricing option (and only if not disabled).
  // Avoid falling back to fiat price (firstOption.price) which would show e.g. 49.99 TEO incorrectly.
  let teo_required = asNumber(raw.teo_required ?? raw.teo_cost ?? raw.teocoin_required) ?? undefined

  const teocoinOption = Array.isArray(raw.pricing_options)
    ? (raw.pricing_options as Record<string, any>[]).find((o) => o.method === "teocoin")
    : undefined

  if (teocoinOption && !teocoinOption.disabled) {
    const optPriceNum = asNumber(teocoinOption.price)
    if (optPriceNum !== undefined) {
      teo_required = optPriceNum
    } else if (teocoinOption.discount_percent && price_eur !== undefined) {
      const pct = Number(teocoinOption.discount_percent)
      if (Number.isFinite(pct) && price_eur !== undefined) {
        // assume 1 TEO = 1 EUR for DB-based system
        teo_required = Math.round((price_eur * pct) / 100)
      }
    }
  }

  const currency = String(raw.currency ?? pricing?.currency ?? firstOption?.currency ?? "EUR")

  const summary: PaymentSummary = {
    course_id: Number(courseId),
    title: raw.title,
    price_eur,
    discount_percent,
    total_eur,
    teo_required,
    currency,
    raw,
  }

  return { ok: true, status: res.status, data: summary }
}

/** =========================
 *  API: Create Payment Intent (Stripe)
 *  ========================= */
export async function createPaymentIntent(
  courseId: number,
  payload?: Record<string, any>
): Promise<PaymentIntentInitResult> {
  const body = payload ?? {}
  const candidates = [
    `/v1/courses/${courseId}/create-payment-intent/`,
    `/v1/courses/${courseId}/start-payment/`,
    `/v1/courses/${courseId}/payment-intent/`,
  ]
  for (const path of candidates) {
    const res = await api.post<any>(path, body)
    if (res.ok) {
      const data = res.data ?? {}
      return {
        ok: true,
        status: res.status,
        client_secret: data.client_secret ?? data.clientSecret,
        publishable_key: data.publishable_key ?? data.publishableKey,
        checkout_url: data.checkout_url ?? data.url ?? data.redirect_url,
        raw: data,
      }
    }
    if (![404, 405, 501].includes((res as any).status ?? res.status)) {
      return { ok: false, status: res.status, error: (res as any).error }
    }
  }
  return { ok: false, status: 404, error: "No payment-intent endpoint available" }
}

/** =========================
 *  API: Purchase/Enroll (fallback o TeoCoin/Stripe generico)
 *  ========================= */
export async function purchaseCourse(
  courseId: number,
  payload?: Record<string, any>
): Promise<Result<any>> {
  let res = await api.post<any>(`/v1/courses/${courseId}/purchase/`, payload ?? {})
  if (res.ok) return { ok: true, status: res.status, data: res.data }

  if (res.status === 404) {
    res = await api.post<any>(`/v1/courses/${courseId}/enroll/`, payload ?? {})
    if (res.ok) return { ok: true, status: res.status, data: res.data }
  }

  return { ok: false, status: res.status, error: (res as any).error }
}

/** =========================
 *  API: Confirm post-Stripe (smart payload)
 *  ========================= */
/**
 * Prova più shape di payload per adattarsi ai nomi attesi dal BE.
 * - Preferito: { payment_intent, payment_intent_client_secret, redirect_status, method: "stripe", course_id }
 * - Alternative: { payment_intent_id }, { client_secret }, { intent_id }, { pi_id }, ecc.
 */
export async function confirmStripePaymentSmart(
  courseId: number,
  args: { payment_intent: string; payment_intent_client_secret?: string; redirect_status?: string }
): Promise<Result<VerificationData>> {
  const { payment_intent, payment_intent_client_secret, redirect_status } = args

  const shapes: Record<string, any>[] = [
    { payment_intent, payment_intent_client_secret, redirect_status, method: "stripe", course_id: courseId },
    { payment_intent_id: payment_intent, client_secret: payment_intent_client_secret, redirect_status, method: "stripe", course_id: courseId },
    { pi_id: payment_intent, client_secret: payment_intent_client_secret, method: "stripe", course_id: courseId },
    { intent_id: payment_intent, method: "stripe", course_id: courseId },
    { payment_intent, method: "stripe" },
  ]

  let last400: any = null

  for (const body of shapes) {
    const res = await api.post<any>(`/v1/courses/${courseId}/confirm-payment/`, body)
    if (res.ok) {
      const data = res.data ?? {}
      const enrolled =
        data.enrolled === true ||
        data.enrollment_created === true ||
        data.status === "enrolled" ||
        data.result === "ok"

      const cid =
        asNumber(data.course_id) ??
        asNumber(data.course) ??
        (Number.isFinite(courseId) ? Number(courseId) : undefined)

      const status: string | undefined =
        data.status ?? data.payment_status ?? data.pi_status ?? data.intent_status

      return { ok: true, status: res.status, data: { enrolled, course_id: cid, status, raw: data } }
    }
    if (res.status === 400) {
      last400 = (res as any).error ?? res
      // provo shape successivo
      continue
    }
    if (![404, 405, 501].includes((res as any).status ?? res.status)) {
      return { ok: false, status: res.status, error: (res as any).error }
    }
  }

  return { ok: false, status: 400, error: last400 ?? "Bad Request" }
}

/** =========================
 *  (Opzionale) Verify generico
 *  ========================= */
export async function verifyStripePayment(
  paymentIntentId: string,
  courseId?: number
): Promise<Result<VerificationData>> {
  const payload = { payment_intent: paymentIntentId, course_id: courseId }
  const candidates = [
    `/v1/payments/verify/`,
    `/v1/stripe/verify/`,
    courseId ? `/v1/courses/${courseId}/verify-payment/` : null,
  ].filter(Boolean) as string[]

  for (const path of candidates) {
    const res = await api.post<any>(path, payload)
    if (res.ok) {
      const data = res.data ?? {}
      const enrolled =
        data.enrolled === true ||
        data.enrollment_created === true ||
        data.status === "enrolled" ||
        data.result === "ok"
      const cid =
        asNumber(data.course_id) ??
        asNumber(data.course) ??
        (courseId !== undefined ? Number(courseId) : undefined)
      const status: string | undefined =
        data.status ?? data.payment_status ?? data.pi_status ?? data.intent_status

      return { ok: true, status: res.status, data: { enrolled, course_id: cid, payment_intent: paymentIntentId, status, raw: data } }
    }
    if (![404, 405, 501].includes((res as any).status ?? res.status)) {
      return { ok: false, status: res.status, error: (res as any).error }
    }
  }
  return { ok: false, status: 404, error: "No payment verification endpoint available" }
}
