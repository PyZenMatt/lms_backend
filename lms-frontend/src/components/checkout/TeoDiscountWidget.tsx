import { useEffect, useState } from "react";
import { getWallet, checkDiscount, applyDiscount, type WalletInfo } from "../../services/wallet";
import { makeIdempotencyKey, clearIdempotencyKey } from "../../lib/idempotency";

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

export default function TeoDiscountWidget({ priceEUR, courseId, onApply, onReceipt, onRefreshAfterSuccess }: Props) {
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [stripeClientSecret, setStripeClientSecret] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const options = [5, 10, 15];
  const [selectedPct, setSelectedPct] = useState<number | null>(null);
  const [applied, setApplied] = useState(false);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    // If price, course or selected percent change, clear previous check/apply result to avoid stale teo_required
    setResult(null);
    setApplied(false);
    setStripeClientSecret(null);
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
  console.debug('[TeoDiscountWidget] check payload:', payload);
  const res = await checkDiscount(payload);
  console.debug('[TeoDiscountWidget] check response:', res);
    setChecking(false);
    if (!res.ok) {
      setError(`Verifica sconto fallita (${res.status})`);
      return;
    }
  setResult(res.data);
  }

  async function handleApply() {
    if (!result) return;
    setError(null);
    setStripeClientSecret(null);
    setApplying(true);
    const idemp = makeIdempotencyKey("apply-discount");
    const body: Record<string, unknown> = { price_eur: priceEUR, idempotency_key: idemp };
    if (courseId) body.course_id = courseId;
    if (selectedPct) body.discount_percent = selectedPct;
    // When calling course-scoped hybrid-payment, backend expects teocoin_to_spend and wallet_address
    // If the user explicitly selected a percent, prefer that value (avoid using stale result.teo_required)
    // result might be nested under `discount` (CalculateDiscountView) or flat (hybrid response)
  const discountObj = result ? ((result as Record<string, unknown>).discount ?? result) as Record<string, unknown> : undefined;
    const teoFromResultRaw = discountObj && (discountObj['teo_spent'] ?? discountObj['teo_required'] ?? discountObj['teo_used'] ?? discountObj['teo']);
    const teoFromResult = teoFromResultRaw !== undefined && teoFromResultRaw !== null ? Number(teoFromResultRaw) : undefined;
    let teoToSpend: number | undefined = undefined;
    if (selectedPct) {
      // user explicitly picked a percent — compute from price
      const discountEUR = Math.round((priceEUR * selectedPct) / 100);
      teoToSpend = discountEUR;
    } else if (typeof teoFromResult === 'number' && Number.isFinite(teoFromResult)) {
      teoToSpend = Math.round(teoFromResult as number);
    }
    if (teoToSpend !== undefined && Number.isFinite(teoToSpend) && teoToSpend > 0) {
      body.teocoin_to_spend = teoToSpend;
    } else {
      // fallback: try to read teo_required from previous check result
  const prev = result ? ((result as Record<string, unknown>).discount ?? result) as Record<string, unknown> : undefined;
      const prevTeo = prev && (prev['teo_required'] ?? prev['teo_spent'] ?? prev['teo_used']);
      const prevTeoNum = prevTeo !== undefined && prevTeo !== null ? Number(prevTeo) : NaN;
      if (Number.isFinite(prevTeoNum) && prevTeoNum > 0) body.teocoin_to_spend = Math.round(prevTeoNum);
    }

    // Debug computed values to diagnose incorrect teocoin_to_spend
    const debugInfo = {
      priceEUR,
      selectedPct,
      computedFromSelected: selectedPct ? Number(((priceEUR * selectedPct) / 100).toFixed(4)) : null,
      computedTeoToSpend: teoToSpend,
      teoFromResultRaw,
      body
    };
    console.debug("[TeoDiscountWidget] apply computed:", debugInfo);
    console.debug("[TeoDiscountWidget] apply payload:", body);

    const res = await applyDiscount(body);
    setApplying(false);
    console.debug("[TeoDiscountWidget] apply response:", res);
    if (!res.ok) {
      setError(`Applicazione sconto fallita (${res.status})`);
      // allow retry with same idempotency key — keep it pending
      return;
    }
    const data = (res.data || {}) as Record<string, unknown>;

    // Normalize various backend response shapes:
    // - { final_price_eur, discount_eur }
    // - { discounted_amount, discount_applied }
    // - { success: true, discount: { final_price, discount_amount, teo_required } }
    const nestedDiscount = (data.discount ?? null) as Record<string, unknown> | null;
    const finalFromData = Number(
      data.final_price_eur ?? data.discounted_amount ?? data.final_price ?? nestedDiscount?.final_price ?? nestedDiscount?.final_price_eur ?? priceEUR
    );
    const discountFromData = Number(
      data.discount_eur ?? data.discount_applied ?? data.discount_amount ?? nestedDiscount?.discount_amount ?? nestedDiscount?.discount_eur ?? (priceEUR - finalFromData)
    );

    // Ensure the UI sees normalized fields
    const normalized = {
      ...data,
      final_price_eur: finalFromData,
      discount_eur: discountFromData,
      teo_required: data.teo_required ?? data.teo_spent ?? nestedDiscount?.teo_required ?? teoToSpend,
      stripe_client_secret: (data.stripe_client_secret ?? data.client_secret ?? data.clientSecret) as string | undefined,
    } as Record<string, unknown>;

    setResult(normalized);
    setApplied(true);
    if (typeof normalized.stripe_client_secret === 'string') setStripeClientSecret(normalized.stripe_client_secret as string);
    onApply(normalized.final_price_eur as number, normalized.discount_eur as number, { ...normalized, idempotency_key: idemp });

    if (typeof onReceipt === "function") {
      onReceipt({
        final_price_eur: Number(normalized.final_price_eur ?? priceEUR),
  discount_eur: Number(normalized.discount_eur ?? (priceEUR - Number(normalized.final_price_eur ?? priceEUR))),
        teo_spent: typeof normalized.teo_required === 'number' ? Number(normalized.teo_required) : typeof normalized.teo_spent === 'number' ? Number(normalized.teo_spent) : undefined,
        stripe_client_secret: typeof normalized.stripe_client_secret === 'string' ? normalized.stripe_client_secret : undefined,
        order_id: (normalized.order_id ?? normalized.payment_intent_id) as string | number | undefined,
      });
    }

    // Chiave idempotente consumata
    clearIdempotencyKey(idemp);

    // Aggiorna saldo/movimenti dopo esito OK
    if (onRefreshAfterSuccess) await onRefreshAfterSuccess();
  }

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm text-gray-500">Sconto con TEO</div>
          <div className="text-base">Prezzo corrente: <span className="font-semibold">{priceEUR.toFixed(2)} EUR</span></div>
        </div>
        {loading ? (
          <div className="h-6 w-24 animate-pulse rounded bg-gray-200" />
        ) : (
          <div className="text-right">
            <div className="text-xs text-gray-500">Saldo TEO</div>
            <div className="font-semibold">{wallet && typeof wallet.balance_teo === 'number' ? wallet.balance_teo.toFixed(2) : "--"} TEO</div>
          </div>
        )}
      </div>

      {error && <div className="mt-3 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700">{error}</div>}

      <div className="mt-4">
        <div className="text-sm mb-2">Scegli sconto TEO</div>
        <div className="flex gap-2">
          {options.map((pct) => {
            const discountEUR = Number((priceEUR * pct) / 100)
            const teoNeeded = discountEUR
            const availableTEO = (typeof wallet?.balance_teo === 'number') ? wallet!.balance_teo : 0
            const disabled = availableTEO < teoNeeded
            return (
              <button
                key={pct}
                onClick={() => setSelectedPct(pct)}
                disabled={loading || disabled}
                className={`rounded-lg px-3 py-2 text-sm ${selectedPct === pct ? 'border bg-black text-white' : 'border bg-white'} disabled:opacity-50`}
              >
                {pct}% {disabled ? '(non disponibile)' : `-€${discountEUR.toFixed(2)} / ${teoNeeded.toFixed(2)} TEO`}
              </button>
            )
          })}
        </div>

  
        <div className="mt-3 flex items-center gap-2">
          <button
            onClick={handleCheck}
            disabled={loading || checking}
            className="rounded-lg bg-black px-3 py-2 text-sm text-white disabled:opacity-60"
          >
            {checking ? 'Verifico...' : 'Verifica sconto TEO'}
          </button>
          {result && (
            <button
              onClick={handleApply}
              disabled={applying}
              className="rounded-lg border px-3 py-2 text-sm disabled:opacity-60"
            >
              {applying ? 'Applico...' : applied ? 'Applicato' : 'Applica sconto'}
            </button>
          )}
        </div>
      </div>

      {applied && result && (
        <div className="mt-4 rounded-lg border bg-gray-50 p-3 text-sm">
          <div className="flex justify-between"><span>Sconto:</span><span>-{Number(result['discount_eur'] ?? 0).toFixed(2)} EUR</span></div>
          <div className="flex justify-between"><span>TEO richiesti:</span><span>{Number(result['teo_required'] ?? 0).toFixed(2)} TEO</span></div>
          <div className="flex justify-between font-semibold"><span>Totale finale:</span><span>{(priceEUR - Number(result['discount_eur'] ?? 0)).toFixed(2)} EUR</span></div>
          {stripeClientSecret && (
            <div className="mt-2 text-sm text-gray-700">Pagamento Stripe richiesto — client_secret presente</div>
          )}
        </div>
      )}
    </div>
  );
}
