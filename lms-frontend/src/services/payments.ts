// src/services/payments.ts
import { api } from "../lib/api";

/**
 * Tipi flessibili: lo Swagger non specifica lo schema di payment-summary.
 * Mappiamo campi comuni e manteniamo data grezza in raw per compatibilità.
 */
export type PaymentSummary = {
  course_id: number;
  title?: string;
  price_eur?: number;           // prezzo listino
  discount_percent?: number;    // sconto % (se presente)
  total_eur?: number;           // totale da pagare in EUR (post-sconto)
  teo_required?: number;        // TEO necessari (se hybrid)
  currency?: string;            // "EUR" (default)
  // qualsiasi altro dato restituito dal BE
  raw?: any;
};

type Ok<T> = { ok: true; status: number; data: T };
type Err = { ok: false; status: number; error?: any };
export type Result<T> = Ok<T> | Err;

function asNumber(v: any): number | undefined {
  if (v === null || v === undefined) return undefined;
  const n = typeof v === "number" ? v : Number(String(v));
  return Number.isFinite(n) ? n : undefined;
}

/** GET /v1/courses/{course_id}/payment-summary/ */
export async function getPaymentSummary(courseId: number, params?: {
  discount_percent?: number;
  student_address?: string;
}): Promise<Result<PaymentSummary>> {
  const res = await api.get<any>(`/v1/courses/${courseId}/payment-summary/`, {
    params: {
      discount_percent: params?.discount_percent,
      student_address: params?.student_address,
    },
  });

  if (!res.ok) return { ok: false, status: res.status, error: (res as any).error };

  const raw = res.data ?? {};
  // Normalizzazione soft dei principali campi economici
  const price_eur = asNumber(raw.price_eur ?? raw.price ?? raw.base_price ?? raw.original_price);
  const discount_percent = asNumber(raw.discount_percent ?? raw.discountPct);
  const total_eur = asNumber(raw.total_eur ?? raw.total ?? raw.final_price);
  const teo_required = asNumber(raw.teo_required ?? raw.teo_cost ?? raw.teocoin_required);

  const summary: PaymentSummary = {
    course_id: Number(courseId),
    title: raw.title ?? raw.course_title,
    price_eur,
    discount_percent,
    total_eur: total_eur ?? price_eur, // se il BE non calcola, assumi totale = listino
    teo_required,
    currency: raw.currency ?? "EUR",
    raw,
  };
  return { ok: true, status: res.status, data: summary };
}

/**
 * POST /v1/courses/{course_id}/purchase/
 * Stub “one-click”: se il BE ritorna 201 → acquisto completato (e tipicamente iscrizione effettuata).
 * Fallback: prova /enroll/ se /purchase/ non esiste.
 */
export async function purchaseCourse(courseId: number, payload?: Record<string, any>): Promise<Result<any>> {
  // tentativo principale
  let res = await api.post<any>(`/v1/courses/${courseId}/purchase/`, payload ?? {});
  if (res.ok) return { ok: true, status: res.status, data: res.data };

  // fallback 404 → prova endpoint di iscrizione
  if (res.status === 404) {
    res = await api.post<any>(`/v1/courses/${courseId}/enroll/`, payload ?? {});
    if (res.ok) return { ok: true, status: res.status, data: res.data };
  }

  return { ok: false, status: res.status, error: (res as any).error };
}
