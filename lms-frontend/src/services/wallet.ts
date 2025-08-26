import { api } from "../lib/api"

// Tipi
export type WalletInfo = {
  address?: string | null;
  balance_teo: number;      // saldo in TEO
  balance_eur?: number;     // opzionale, se il BE lo fornisce
  updated_at?: string;
  [k: string]: unknown;
};

export type WalletTransaction = {
  id: string | number;
  type: "earn" | "spend" | "refund" | "airdrop" | "adjustment" | string;
  amount_teo: number;       // positivo earn, negativo spend
  description?: string;
  created_at: string;
  reference?: string;
  [k: string]: unknown;
};

type DrfPage<T> = { count: number; next?: string | null; previous?: string | null; results: T[] };

type Ok<T> = { ok: true; status: number; data: T };
type Err = { ok: false; status: number; error?: unknown; tried?: string[] };
export type Result<T> = Ok<T> | Err;

async function tryGet<T>(paths: string[], params?: Record<string, unknown>): Promise<Result<T>> {
  const tried: string[] = [];
  for (const p of paths) {
    tried.push(p);
    const res = await api.get<T>(p, { params });
    if (res.ok) return { ok: true, status: res.status, data: res.data as T };
    // se 404/405, prova il prossimo endpoint
    if (![404, 405].includes(res.status)) return { ok: false, status: res.status, error: res.error, tried };
  }
  return { ok: false, status: 404, error: "All endpoints not found", tried };
}

async function tryPost<T>(paths: string[], body?: Record<string, unknown>): Promise<Result<T>> {
  const tried: string[] = [];
  for (const p of paths) {
    tried.push(p);
    const res = await api.post<T>(p, body);
    if (res.ok) return { ok: true, status: res.status, data: res.data as T };
    if (![404, 405].includes(res.status)) return { ok: false, status: res.status, error: res.error, tried };
  }
  return { ok: false, status: 404, error: "All endpoints not found", tried };
}

export function coerceNumber(v: unknown): number {
  if (v === null || v === undefined) return NaN;
  if (typeof v === 'number') return Number.isFinite(v) ? (v as number) : NaN;
  if (typeof v === 'string') {
    const n = Number(v as string);
    return Number.isFinite(n) ? n : NaN;
  }
  if (typeof v === 'object') {
    const obj = v as Record<string, unknown>;
    if (typeof obj.parsedValue === 'number' && Number.isFinite(obj.parsedValue as number)) return obj.parsedValue as number;
    if (typeof obj.source === 'string') {
      const n = Number(obj.source);
      if (Number.isFinite(n)) return n;
    }
    if (typeof obj.value === 'number' && Number.isFinite(obj.value as number)) return obj.value as number;
    if (typeof obj.value === 'string') {
      const n = Number(obj.value);
      if (Number.isFinite(n)) return n;
    }
    return NaN;
  }
  return NaN;
}

/** GET wallet dell’utente */
export async function getWallet(): Promise<Result<WalletInfo>> {
  // Canonical DB-based TeoCoin endpoints (no speculative fallbacks)
  // -> backend api: /api/v1/teocoin/balance/ (returns { success: true, balance: { available_balance, staked_balance, pending_withdrawal, total_balance } })
  const endpoints = ["/v1/teocoin/balance/"];

  // If profile endpoint returns user profile, normalize it to WalletInfo
  const res = await tryGet<Record<string, unknown>>(endpoints);
  if (!res.ok) return res as Err;

  const data = res.data as Record<string, unknown>;
  console.debug("getWallet: raw response", data);

  // db_teocoin_views.TeocoinBalanceView returns { success: true, balance: {...} }
  if (data && data.balance && typeof data.balance === "object") {
    const b = data.balance as Record<string, unknown>
    // various backends return numbers as strings; coerce safely
    const available = coerceNumber(b.available_balance ?? b.available ?? b["available"] ?? NaN)
    const total = coerceNumber(b.total_balance ?? b.total ?? NaN)
    const address = (b.wallet_address ?? data.wallet_address ?? null) as string | null
    const updated_at = (b.updated_at ?? data.updated_at ?? undefined) as string | undefined

    // If backend provides both total and staked, derive available = total - staked
    const staked = coerceNumber(b.staked_balance ?? b.staked ?? NaN);
    const availableFromTotal = (Number.isFinite(total) && Number.isFinite(staked)) ? Math.max(0, total - staked) : NaN;

    const walletInfo: WalletInfo = {
      address,
      // Prefer explicit available when present. Otherwise prefer computed available (total - staked) when possible.
      // Fallback to total if neither available nor computable available exist.
      balance_teo: Number.isFinite(available) ? available : Number.isFinite(availableFromTotal) ? availableFromTotal : Number.isFinite(total) ? total : 0,
      balance_eur: undefined,
      updated_at,
      raw: data,
    }
  console.debug("getWallet: normalized walletInfo", walletInfo);

    return { ok: true, status: res.status, data: walletInfo };
  }

  // If shape unexpected, return an error with tried info for debugging
  return { ok: false, status: res.status, error: "Unexpected balance payload", tried: (res as unknown as { tried?: string[] }).tried };
}

/** GET movimenti wallet paginati */
export async function getTransactions(page = 1, page_size = 20): Promise<Result<DrfPage<WalletTransaction>>> {
  const endpoints = [
    "/v1/wallet/transactions/",
    "/v1/teocoin/transactions/",
    "/v1/teocoin/transactions/history/",
    "/v1/services/earnings/history/",
    "/v1/users/me/wallet/transactions/",
  ];

  const res = await tryGet<unknown>(endpoints, { page, page_size, limit: page_size });
  if (!res.ok) return res as Err;
  const payload = res.data as unknown;

  // Support multiple shapes: DRF { results: [] }, legacy { transactions: [] }, { data: [] } or raw array
  const resultsField = (payload as Record<string, unknown>)?.results;
  const transactionsField = (payload as Record<string, unknown>)?.transactions;
  const dataField = (payload as Record<string, unknown>)?.data;

  const arr: unknown[] =
    Array.isArray(resultsField) ? (resultsField as unknown[]) :
    Array.isArray(transactionsField) ? (transactionsField as unknown[]) :
    Array.isArray(dataField) ? (dataField as unknown[]) :
    Array.isArray(payload) ? (payload as unknown[]) : [];

  const count = typeof (payload as Record<string, unknown>)?.count === 'number'
    ? (payload as Record<string, unknown>).count as number
    : (Array.isArray(arr) ? arr.length : 0);

  const results: WalletTransaction[] = arr.map((r, i) => {
    const obj = r as Record<string, unknown>;
    const amountRaw = obj.amount_teo ?? obj.amount ?? obj.value ?? 0;
    return {
      id: obj.id ?? obj.tx_id ?? i,
      type: (obj.type ?? obj.transaction_type ?? obj.kind ?? 'unknown') as string,
      amount_teo: typeof amountRaw === 'number' ? amountRaw as number : Number(amountRaw ?? 0),
      description: (obj.description ?? obj.note ?? obj.notes ?? obj.memo ?? null) as string | null,
      created_at: (obj.created_at ?? obj.timestamp ?? new Date().toISOString()) as string,
      reference: (obj.reference ?? obj.tx_hash ?? obj.hash ?? null) as string | null,
      ...obj,
    } as WalletTransaction;
  });

  const nextRaw = (payload as Record<string, unknown>)?.next;
  const prevRaw = (payload as Record<string, unknown>)?.previous;
  const next = typeof nextRaw === 'string' ? nextRaw : null;
  const previous = typeof prevRaw === 'string' ? prevRaw : null;

  return { ok: true, status: res.status, data: { count, next, previous, results } };
}

/**
 * POST verifica sconto in checkout lato BE
 * body es.: { course_id, price_eur }
 * risposta attesa: {
 *   available: boolean,
 *   discount_eur?: number,
 *   final_price_eur?: number,
 *   teo_spent?: number,
 *   message?: string,
 *   ... }
 */
export async function checkDiscount(body: {
  course_id?: number;
  price_eur: number;
  [k: string]: unknown;
}): Promise<Result<Record<string, unknown>>> {
  // Use DB-based calculate-discount endpoint
  const endpoints = ["/v1/teocoin/calculate-discount/"];
  // backend expects `course_price` field in some implementations; include it for compatibility
  const payload: Record<string, unknown> = { ...body } as Record<string, unknown>;
  if (payload.course_price === undefined && payload.price_eur !== undefined) {
    payload.course_price = payload.price_eur;
  }
  return tryPost<Record<string, unknown>>(endpoints, payload);
}

/**
 * POST applicazione sconto TEO / pagamento ibrido
 * Se fornito course_id → preferisce l'endpoint course-scoped:
 *   POST /v1/courses/{course_id}/hybrid-payment/
 * Altrimenti fallback generico:
 *   POST /v1/teocoin/apply-discount/
 */
export async function applyDiscount(body: {
  course_id?: number;
  price_eur?: number;
  discount_percent?: number;
  student_address?: string;
  student_signature?: string;
  idempotency_key?: string;
  [k: string]: unknown;
}): Promise<Result<Record<string, unknown>>> {
  const { course_id, ...rest } = body || {};

  // Try course-scoped hybrid payment when course_id present
  if (typeof course_id === 'number' && Number.isFinite(course_id)) {
    const courseEndpoint = `/v1/courses/${course_id}/hybrid-payment/`;
    const coursePayload: Record<string, unknown> = { ...rest } as Record<string, unknown>;
    if (coursePayload.course_price === undefined && coursePayload.price_eur !== undefined) {
      coursePayload.course_price = coursePayload.price_eur;
    }
    const courseRes = await api.post<Record<string, unknown>>(courseEndpoint, coursePayload);
    // If OK or error not 404/405, return it (don't fallback)
    if (courseRes.ok || ![404, 405].includes(courseRes.status)) return courseRes as Result<Record<string, unknown>>;
    // otherwise continue to fallbacks
  }

  const fallbacks = ["/v1/teocoin/apply-discount/", "/v1/payments/apply-discount/"];
  const payload: Record<string, unknown> = { course_id, ...rest } as Record<string, unknown>;
  if (payload.course_price === undefined && payload.price_eur !== undefined) payload.course_price = payload.price_eur;
  return tryPost<Record<string, unknown>>(fallbacks, payload);
}

// Backwards-compatible aliases requested by integration:
export const getBalance = getWallet;
export const calculateDiscount = checkDiscount;
