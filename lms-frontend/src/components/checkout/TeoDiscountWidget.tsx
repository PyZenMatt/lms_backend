import { useEffect, useState } from "react";
import { getWallet, type WalletInfo } from "../../services/wallet";
import { previewDiscount, confirmDiscount } from "../../services/payments";

type Props = {
  priceEUR: number;
  courseId?: number;
  // onApply ora riceve anche idempotency_key per tracciarlo lato checkout
  onApply: (finalPriceEUR: number, discountEUR: number, details?: Record<string, unknown>) => void;
  onReceipt?: (receipt: {
    final_price_eur: number;
    discount_eur: number;
    teo_spent?: number;
    stripe_client_secret?: string;
    order_id?: string | number;
  }) => void;
  // refetch callback (per aggiornar e saldo/movimenti post esito)
  onRefreshAfterSuccess?: () => Promise<void> | void;
};

export default function TeoDiscountWidget({ priceEUR, courseId, onApply }: Props) {
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  // result will contain server-side breakdown from previewDiscount
  const [checking, setChecking] = useState(false);
  const options = [5, 10, 15];
  // TEO per 1 EUR (frontend config via Vite). Default fallback 10 (1 EUR = 10 TEO)
  // Read Vite env value for TEO rate. Try window.__ENV (injected), then import.meta.env.
  let TEO_PER_EUR = 10
  try {
    const win = window as unknown as Record<string, unknown>
    const wenv = (win['__ENV'] as Record<string, unknown> | undefined)
    if (wenv && typeof wenv.VITE_TEO_EUR_RATE === 'string') {
      TEO_PER_EUR = Number(wenv.VITE_TEO_EUR_RATE)
    } else if (typeof (import.meta as { env?: Record<string, string> }).env?.VITE_TEO_EUR_RATE === 'string') {
      TEO_PER_EUR = Number((import.meta as { env?: Record<string, string> }).env!.VITE_TEO_EUR_RATE)
    }
  } catch {
    // ignore and keep fallback
  }
  const [selectedPct, setSelectedPct] = useState<number | null>(null);
  const [applied, setApplied] = useState(false);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    // If price, course or selected percent change, clear previous check/apply result to avoid stale teo_required
    setResult(null);
    setApplied(false);
  }, [priceEUR, selectedPct, courseId]);

  useEffect(() => {
    let alive = true;
    async function load() {
      setLoading(true);
      setError(null);
      const w = await getWallet();
      if (!alive) return;
      if (w.ok) setWallet(w.data);
      else setError(`Wallet error: ${w.status}`);
      setLoading(false);
    }
    load();
    return () => { alive = false; };
  }, [courseId, priceEUR]);

  async function handleCheck() {
    setChecking(true);
    setError(null);
    const payload: { price_eur: number; course_id?: number; discount_percent?: number; [k: string]: unknown } = { price_eur: priceEUR };
    if (courseId) payload.course_id = courseId;
    if (selectedPct) payload.discount_percent = selectedPct;
    console.debug('[TeoDiscountWidget] preview payload:', payload);
    const res = await previewDiscount(payload);
    console.debug('[TeoDiscountWidget] preview response:', res);
    setChecking(false);
    if (!res.ok) {
      setError(`Verifica sconto fallita (${res.status})`);
      return;
    }
    // res.data is our DiscountBreakdown shape from the server
    setResult(res.data as Record<string, unknown>);
  }
  async function handleApply() {
    if (!result) return;
    setError(null);
    setApplying(true);
    // propagate server-provided breakdown via onApply. Parent will call createPaymentIntent with discount flags.
    const finalPrice = Number(result['student_pay_eur'] ?? result['student_pay'] ?? priceEUR) as number;
    const discountEUR = Number.isFinite(Number(priceEUR - finalPrice)) ? Number(priceEUR - finalPrice) : Number(result['discount_eur'] ?? 0);
      try {
      // First, try to persist the preview as a discount snapshot on the server so the flow is idempotent
      // and teachers can be notified. We call confirmDiscount which is safe to call multiple times.
      try {
        // backend requires an order_id on confirm; frontend generates a lightweight id so the snapshot
        // can be created before the Stripe PaymentIntent exists. The PaymentReturn flow will call
        // confirmDiscount again with the real order_id (payment intent) and be idempotent.
        const payload: Record<string, unknown> = {
          order_id: `local_${Date.now()}`,
          course_id: courseId,
          price_eur: priceEUR,
          discount_percent: selectedPct ?? undefined,
          breakdown: result,
        };
        console.debug('[TeoDiscountWidget] confirming discount snapshot with payload:', payload)
        const conf = await confirmDiscount(payload)
        console.debug('[TeoDiscountWidget] confirmDiscount response:', conf)
        if (!conf.ok) {
          // keep going but surface an error to user
          setError(`Impossibile registrare lo sconto: HTTP ${conf.status}`)
        } else {
          // Prefer server-side breakdown values when available (they are the source of truth).
          // The server may return breakdown in several shapes; attempt to parse common variants.
          const serverBreakdown: unknown = (conf.data && (conf.data.breakdown ?? conf.data.snapshot ?? conf.data)) || null;

          // helper to read nested numeric fields safely
          const readNumber = (obj: unknown, ...keys: string[]) => {
            const map = (obj && typeof obj === 'object') ? (obj as Record<string, unknown>) : undefined
            for (const k of keys) {
              if (!map) continue
              const v = map[k]
              if (v === undefined || v === null) continue
              // if value is an object that wraps the real value (like { source, parsedValue }) dig deeper
              if (typeof v === 'object') {
                const vmap = v as Record<string, unknown>
                if ('parsedValue' in vmap) return Number(vmap['parsedValue'])
                if ('source' in vmap) {
                  const n = Number(vmap['source'])
                  if (!Number.isNaN(n)) return n
                }
                // try common nested locations
                if ('data' in vmap) {
                  const n = Number((vmap['data'] as unknown) as number)
                  if (!Number.isNaN(n)) return n
                }
                continue
              }
              const n = Number(v)
              if (!Number.isNaN(n)) return n
            }
            return undefined
          }

          let finalFromServer = readNumber(serverBreakdown, 'student_pay_eur', 'student_pay', 'final_price_eur')
          // sometimes serverBreakdown.raw.data.student_pay_eur
          if (finalFromServer === undefined && serverBreakdown && typeof serverBreakdown === 'object') {
            const sb = serverBreakdown as Record<string, unknown>
            if (sb['raw'] && typeof sb['raw'] === 'object') {
              const raw = sb['raw'] as Record<string, unknown>
              if (raw['data'] && typeof raw['data'] === 'object') {
                finalFromServer = readNumber(raw['data'], 'student_pay_eur', 'student_pay')
              }
            }
          }

          let final = Number(result['student_pay_eur'] ?? result['student_pay'] ?? priceEUR)
          if (finalFromServer !== undefined && Number.isFinite(finalFromServer)) final = finalFromServer

          // compute discount eur from server value if available
          let discountComputed = Number(priceEUR) - final
          if (!Number.isFinite(discountComputed) || discountComputed === 0) {
            // try server-provided discount if present
            const serverDiscount = readNumber(serverBreakdown, 'discount_eur', 'discount_amount')
            if (serverDiscount !== undefined && Number.isFinite(serverDiscount)) discountComputed = serverDiscount
          }

          const detailsWithSnapshot = {
            breakdown: serverBreakdown ?? result,
            snapshot: conf.data.snapshot ?? null,
            // normalized helpers expected by CourseCheckout
            final_price_eur: final,
            discount_eur: discountComputed,
          } as Record<string, unknown>

          onApply(final, discountComputed, detailsWithSnapshot)
          setApplied(true)
          setError(null)
          // persist a normalized breakdown in local state so it won't be the full wrapper later
          try {
            setResult((r) => ({ ...(r ?? {}), _snapshot: conf.data.snapshot ?? null, ...((serverBreakdown && typeof serverBreakdown === 'object') ? serverBreakdown : {}) }))
          } catch {
            // ignore
          }
          return
        }
      } catch (e) {
        console.debug('confirmDiscount failed:', e)
        setError(String(e))
      }

  // Fallback: still call onApply even if confirmDiscount failed, to preserve UX
  onApply(finalPrice, discountEUR, { breakdown: result, final_price_eur: finalPrice, discount_eur: discountEUR })
      setApplied(true)
    } catch (e) {
      setError(String(e));
    } finally {
      setApplying(false);
    }
  }

  return (
    <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm text-muted-foreground">Sconto con TEO</div>
          <div className="text-base">Prezzo corrente: <span className="font-semibold text-foreground">{priceEUR.toFixed(2)} EUR</span></div>
        </div>
    {loading ? (
          <div className="h-6 w-24 animate-pulse rounded bg-muted/20" />
        ) : (
          <div className="text-right">
            <div className="text-xs text-muted-foreground">Saldo TEO</div>
      <div className="font-semibold text-foreground">{wallet && typeof wallet.balance_teo === 'number' ? wallet.balance_teo.toFixed(8) : "--"} TEO</div>
          </div>
        )}
      </div>

      {error && <div className="mt-3 rounded border border-destructive/40 bg-destructive/10 p-2 text-sm text-destructive-foreground">{error}</div>}

      <div className="mt-4">
        <div className="text-sm mb-2 text-foreground">Scegli sconto TEO</div>
        <div className="flex gap-2">
      {options.map((pct) => {
      const discountEUR = Number((priceEUR * pct) / 100)
      // convert EUR discount to TEO required using configured rate
      const teoNeeded = discountEUR * TEO_PER_EUR
            const availableTEO = (typeof wallet?.balance_teo === 'number') ? wallet!.balance_teo : 0
            const disabled = availableTEO < teoNeeded
            return (
              <button
                key={pct}
                onClick={() => setSelectedPct(pct)}
                disabled={loading || disabled}
                className={`rounded-lg px-3 py-2 text-sm border disabled:opacity-50 ${selectedPct === pct ? 'bg-primary text-primary-foreground border-primary' : 'bg-card text-foreground border-border'}`}
              >
        {pct}% {disabled ? '(non disponibile)' : `-€${discountEUR.toFixed(2)} / ${teoNeeded.toFixed(8)} TEO`}
              </button>
            )
          })}
        </div>


        <div className="mt-3 flex items-center gap-2">
          <button
            onClick={handleCheck}
            disabled={loading || checking}
            className="rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground disabled:opacity-60"
          >
            {checking ? 'Verifico...' : 'Verifica sconto TEO'}
          </button>
          {result && (
            <button
              onClick={handleApply}
              disabled={applying}
              className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground disabled:opacity-60"
            >
              {applying ? 'Applico...' : applied ? 'Applicato' : 'Applica sconto'}
            </button>
          )}
        </div>
      </div>

      {applied && result && (
        <div className="mt-4 rounded-lg border border-border bg-popover p-3 text-sm text-foreground">
              {(() => {
                const studentPay = Number(result['student_pay_eur'] ?? result['student_pay'] ?? priceEUR);
                const discount = Number.isFinite(Number(priceEUR - studentPay)) ? Number(priceEUR - studentPay) : Number(result['discount_eur'] ?? 0);
                const teoReq = Number(result['teacher_teo'] ?? result['teacher_teocoin'] ?? result['teo_required'] ?? 0);
                return (
                  <>
                    <div className="flex justify-between"><span>Sconto:</span><span>-{discount.toFixed(2)} EUR</span></div>
                    <div className="flex justify-between"><span>TEO richiesti:</span><span>{teoReq.toFixed(8)} TEO</span></div>
                    <div className="flex justify-between font-semibold"><span>Totale finale:</span><span>{studentPay.toFixed(2)} EUR</span></div>
                  </>
                )
              })()}
        </div>
      )}
    </div>
  );
}
