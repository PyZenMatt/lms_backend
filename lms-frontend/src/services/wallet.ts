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

/** GET wallet dell’utente */
export async function getWallet(): Promise<Result<WalletInfo>> {
  // Canonical DB-based TeoCoin endpoints (no speculative fallbacks)
  // -> backend api: /api/v1/teocoin/balance/ (returns { success: true, balance: { available_balance, staked_balance, pending_withdrawal, total_balance } })
  const endpoints = ["/v1/teocoin/balance/"];

  // If profile endpoint returns user profile, normalize it to WalletInfo
  const res = await tryGet<Record<string, unknown>>(endpoints);
  if (!res.ok) return res as Err;

  const data = res.data as Record<string, unknown>;

  // db_teocoin_views.TeocoinBalanceView returns { success: true, balance: {...} }
  if (data && data.balance && typeof data.balance === "object") {
    const b = data.balance as Record<string, unknown>
    // various backends return numbers as strings; coerce safely
    const available = Number(b.available_balance ?? b.available ?? b["available"] ?? 0)
    const total = Number(b.total_balance ?? b.total ?? 0)
    const address = (b.wallet_address ?? data.wallet_address ?? null) as string | null
    const updated_at = (b.updated_at ?? data.updated_at ?? undefined) as string | undefined

    const walletInfo: WalletInfo = {
      address,
      balance_teo: Number.isFinite(available) ? available : Number.isFinite(total) ? total : 0,
      balance_eur: undefined,
      updated_at,
      raw: data,
    }

    return { ok: true, status: res.status, data: walletInfo };
  }

  // If shape unexpected, return an error with tried info for debugging
  return { ok: false, status: res.status, error: "Unexpected balance payload", tried: (res as unknown as { tried?: string[] }).tried };
}

/** GET movimenti wallet paginati */
export async function getTransactions(page = 1, page_size = 20): Promise<Result<DrfPage<WalletTransaction>>> {
  // Use canonical DB-based transactions endpoint
  const endpoints = ["/v1/teocoin/transactions/"];

  const res = await tryGet<{ success?: boolean; transactions?: unknown[]; count?: number }>(endpoints, { page, page_size });
  if (!res.ok) return res as Err;

  const payload = res.data as unknown as Record<string, unknown>;
  const maybeTx = payload.transactions ?? payload["transactions"];
  const txs = Array.isArray(maybeTx) ? (maybeTx as unknown[]) : [];

  const results = txs.map((item) => {
    const obj = item as Record<string, unknown>
    return {
      id: (obj.id ?? obj.tx_id ?? Math.random().toString(36).slice(2)) as string,
      type: (obj.type ?? obj.transaction_type ?? obj.kind ?? "unknown") as string,
      amount_teo: Number(obj.amount ?? obj.amount_teo ?? obj.value ?? 0),
      description: (obj.description ?? obj.note ?? obj.reason) as string | undefined,
      created_at: (obj.created_at ?? obj.timestamp ?? new Date().toISOString()) as string,
      reference: (obj.reference ?? obj.tx_hash) as string | undefined,
      raw: obj,
    }
  })

  const countNum = Number((payload.count ?? results.length) as unknown) || results.length
  const pageObj: DrfPage<WalletTransaction> = { count: countNum, next: null, previous: null, results }
  return { ok: true, status: res.status, data: pageObj }
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
  return tryPost<Record<string, unknown>>(endpoints, body as Record<string, unknown>);
}
