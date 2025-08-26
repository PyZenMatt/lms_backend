// src/services/payments.ts
import { api } from "../lib/api"
import { showToast } from "../components/ToastHost"

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
 *  API: Rewards / Discounts (preview & confirm)
 *  These wrap the backend endpoints that return the server-side breakdown
 *  for teocoin-based discounts and confirm the persisted snapshot after
 *  a successful payment (idempotent).
 *  ========================= */

export type DiscountBreakdown = {
  student_pay_eur?: number
  teacher_eur?: number
  platform_eur?: number
  teacher_teo?: number
  platform_teo?: number
  absorption_policy?: string
  // full raw payload from backend
  raw?: any
}

export async function previewDiscount(payload?: Record<string, any>): Promise<Result<DiscountBreakdown>> {
  const body = payload ?? {}
  const res = await api.post<any>(`/v1/rewards/discounts/preview/`, body)
  if (!res.ok) return { ok: false, status: res.status, error: (res as any).error }

  const data = res.data ?? {}
  const breakdown: DiscountBreakdown = {
    student_pay_eur: asNumber(data.student_pay_eur ?? data.student_pay ?? data.student_amount) ?? undefined,
    teacher_eur: asNumber(data.teacher_eur ?? data.teacher_amount) ?? undefined,
    platform_eur: asNumber(data.platform_eur ?? data.platform_amount) ?? undefined,
    teacher_teo: asNumber(data.teacher_teo ?? data.teacher_teocoin) ?? undefined,
    platform_teo: asNumber(data.platform_teo ?? data.platform_teocoin) ?? undefined,
    absorption_policy: data.absorption_policy ?? data.policy ?? undefined,
    raw: data,
  }

  return { ok: true, status: res.status, data: breakdown }
}

export async function confirmDiscount(payload?: Record<string, any>): Promise<Result<{ snapshot?: any; breakdown?: DiscountBreakdown }>> {
  const body = payload ?? {}
  const res = await api.post<any>(`/v1/rewards/discounts/confirm/`, body)
  if (!res.ok) return { ok: false, status: res.status, error: (res as any).error }

  const data = res.data ?? {}
  const breakdownData = data.breakdown ?? data ?? {}
  const breakdown: DiscountBreakdown = {
    student_pay_eur: asNumber(breakdownData.student_pay_eur ?? breakdownData.student_pay ?? breakdownData.student_amount) ?? undefined,
    teacher_eur: asNumber(breakdownData.teacher_eur ?? breakdownData.teacher_amount) ?? undefined,
    platform_eur: asNumber(breakdownData.platform_eur ?? breakdownData.platform_amount) ?? undefined,
    teacher_teo: asNumber(breakdownData.teacher_teo ?? breakdownData.teacher_teocoin) ?? undefined,
    platform_teo: asNumber(breakdownData.platform_teo ?? breakdownData.platform_teocoin) ?? undefined,
    absorption_policy: breakdownData.absorption_policy ?? breakdownData.policy ?? undefined,
    raw: data,
  }

  return { ok: true, status: res.status, data: { snapshot: data.snapshot ?? data, breakdown } }
}

/**
 * GET discount snapshot by order_id.
 * Fallback callers should call confirmDiscount(...) when GET is not available (404).
 */
export async function getDiscountSnapshot(orderId: string): Promise<Result<{ snapshot?: any; breakdown?: DiscountBreakdown; status?: string; deadline_at?: string }>> {
  if (!orderId) return { ok: false, status: 400, error: "order_id required" }
  const path = `/v1/rewards/discounts/${orderId}/`
  const res = await api.get<any>(path)
  if (!res.ok) return { ok: false, status: res.status, error: (res as any).error }

  const data = (res.data ?? {}) as any
  const snapshot = data.snapshot ?? data
  const breakdownData = snapshot.breakdown ?? snapshot ?? {}
  const breakdown: DiscountBreakdown = {
    student_pay_eur: asNumber(breakdownData.student_pay_eur ?? breakdownData.student_pay ?? breakdownData.student_amount) ?? undefined,
    teacher_eur: asNumber(breakdownData.teacher_eur ?? breakdownData.teacher_amount) ?? undefined,
    platform_eur: asNumber(breakdownData.platform_eur ?? breakdownData.platform_amount) ?? undefined,
    teacher_teo: asNumber(breakdownData.teacher_teo ?? breakdownData.teacher_teocoin) ?? undefined,
    platform_teo: asNumber(breakdownData.platform_teo ?? breakdownData.platform_teocoin) ?? undefined,
    absorption_policy: breakdownData.absorption_policy ?? breakdownData.policy ?? undefined,
    raw: snapshot,
  }

  const status = (snapshot.status ?? snapshot.state) as string | undefined
  const deadline_at = snapshot.deadline_at ?? snapshot.expires_at

  return { ok: true, status: res.status, data: { snapshot, breakdown, status, deadline_at } }
}

/** =========================
 *  API: Teacher Inbox & Staking wrappers
 *  These are small FE wrappers around rewards endpoints used by
 *  the teacher inbox (pending teo decisions) and staking pages.
 *  They follow the project's Result<T> style and surface 404 as a
 *  friendly toast "funzionalità in arrivo".
 *  ========================= */

export type PendingTeoDecision = {
  id: number
  order_id?: string
  course_title?: string
  student_name?: string
  teacher_eur?: number
  platform_eur?: number
  teacher_teo?: number
  expected_bonus_teo?: number
  deadline_at?: string
  status?: string
  raw?: any
}

export async function listPendingTeoDecisions(): Promise<Result<PendingTeoDecision[]>> {
  const path = `/v1/rewards/discounts/pending/`
  const res = await api.get<any>(path)
  if (!res.ok) {
    if ((res as any).status === 404) {
      showToast({ variant: "info", message: "Funzionalità in arrivo: Inbox decisioni TEO" })
    }
    return { ok: false, status: res.status, error: (res as any).error }
  }

  const raw = res.data ?? []
  const items: PendingTeoDecision[] = Array.isArray(raw)
    ? raw.map((r: any) => ({
        id: Number(r.id ?? r.snapshot_id ?? r.pk),
        order_id: r.order_id ?? r.order ?? undefined,
        course_title: r.course_title ?? r.title ?? r.course_title_preview ?? undefined,
        student_name: r.student_name ?? r.student ?? undefined,
        teacher_eur: asNumber(r.teacher_eur ?? r.teacher_amount ?? r.teacher_amount_eur) ?? undefined,
        platform_eur: asNumber(r.platform_eur ?? r.platform_amount) ?? undefined,
        teacher_teo: asNumber(r.teacher_teo ?? r.teacher_teocoin) ?? undefined,
        expected_bonus_teo: asNumber(r.expected_bonus_teo ?? r.bonus_teo) ?? undefined,
        deadline_at: r.deadline_at ?? r.expires_at ?? undefined,
        status: r.status ?? r.state ?? undefined,
        raw: r,
      }))
    : []

  return { ok: true, status: res.status, data: items }
}

export async function acceptTeo(snapshotId: number): Promise<Result<any>> {
  if (!snapshotId) return { ok: false, status: 400, error: "snapshot id required" }
  const path = `/v1/rewards/discounts/${snapshotId}/accept/`
  const res = await api.post<any>(path, {})
  if (!res.ok) {
    if ((res as any).status === 404) showToast({ variant: "info", message: "Funzionalità in arrivo: accetta TEO" })
    return { ok: false, status: res.status, error: (res as any).error }
  }
  return { ok: true, status: res.status, data: res.data ?? {} }
}

export async function rejectTeo(snapshotId: number): Promise<Result<any>> {
  if (!snapshotId) return { ok: false, status: 400, error: "snapshot id required" }
  const path = `/v1/rewards/discounts/${snapshotId}/reject/`
  const res = await api.post<any>(path, {})
  if (!res.ok) {
    if ((res as any).status === 404) showToast({ variant: "info", message: "Funzionalità in arrivo: rifiuta TEO" })
    return { ok: false, status: res.status, error: (res as any).error }
  }
  return { ok: true, status: res.status, data: res.data ?? {} }
}

export type StakingOverview = {
  balance_teo?: number
  staked_teo?: number
  tier_name?: string
  bonus_multiplier?: number
  next_tier?: string
  next_tier_threshold_teo?: number
  raw?: any
}

export async function getStakingOverview(): Promise<Result<StakingOverview>> {
  const path = `/v1/rewards/staking/overview/`
  const res = await api.get<any>(path)
  if (!res.ok) {
    if ((res as any).status === 404) showToast({ variant: "info", message: "Funzionalità in arrivo: staking" })
    return { ok: false, status: res.status, error: (res as any).error }
  }

  const data = res.data ?? {}
  const out: StakingOverview = {
    balance_teo: asNumber(data.balance_teo ?? data.balance ?? data.balance_teocoin) ?? undefined,
    staked_teo: asNumber(data.staked_teo ?? data.staked ?? undefined) ?? undefined,
    tier_name: data.tier_name ?? data.tier ?? undefined,
    bonus_multiplier: asNumber(data.bonus_multiplier ?? data.bonus ?? undefined) ?? undefined,
    next_tier: data.next_tier ?? undefined,
    next_tier_threshold_teo: asNumber(data.next_tier_threshold_teo ?? data.next_threshold ?? data.next_tier_threshold) ?? undefined,
    raw: data,
  }

  return { ok: true, status: res.status, data: out }
}

export async function stakeTeo(amount: string): Promise<Result<StakingOverview>> {
  if (!amount) return { ok: false, status: 400, error: "amount required" }
  const path = `/v1/rewards/staking/stake/`
  const body = { amount }
  const res = await api.post<any>(path, body)
  if (!res.ok) {
    if ((res as any).status === 404) showToast({ variant: "info", message: "Funzionalità in arrivo: stake TEO" })
    return { ok: false, status: res.status, error: (res as any).error }
  }

  const data = res.data ?? {}
  // assume backend returns overview
  return getStakingOverview().then((r) => (r.ok ? r : { ok: true, status: res.status, data: { raw: data } }))
}

export async function unstakeTeo(amount: string): Promise<Result<StakingOverview>> {
  if (!amount) return { ok: false, status: 400, error: "amount required" }
  const path = `/v1/rewards/staking/unstake/`
  const body = { amount }
  const res = await api.post<any>(path, body)
  if (!res.ok) {
    if ((res as any).status === 404) showToast({ variant: "info", message: "Funzionalità in arrivo: unstake TEO" })
    return { ok: false, status: res.status, error: (res as any).error }
  }

  return getStakingOverview().then((r) => (r.ok ? r : { ok: true, status: res.status, data: { raw: res.data ?? {} } }))
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
