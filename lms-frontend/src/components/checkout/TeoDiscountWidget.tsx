import { useEffect, useState } from "react";
import { getWallet, type WalletInfo } from "../../services/wallet";

type Props = {
  /** prezzo corrente in EUR (listino o già scontato da coupon) */
  priceEUR: number;
  /** opzionale, utile se il BE usa logiche per-corso */
  courseId?: number;
  /** callback quando lo sconto TEO è applicato correttamente */
  onApply: (finalPriceEUR: number, discountEUR: number, details?: Record<string, unknown>) => void;
};

export default function TeoDiscountWidget({ priceEUR, courseId, onApply }: Props) {
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const options = [5, 10, 15];
  const [selectedPct, setSelectedPct] = useState<number | null>(null);
  const [applied, setApplied] = useState(false);

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

  function handleApply() {
    if (!selectedPct) return
    const pctUsed = selectedPct
    const discountEUR = Number((priceEUR * pctUsed) / 100)
    const final = Number((priceEUR - discountEUR))
    const teo_needed = discountEUR // 1 TEO = 1 EUR

    const details: Record<string, unknown> = {
      discount_percent: pctUsed,
      discount_eur: discountEUR,
      final_price_eur: final,
      teo_required: teo_needed,
    }

    setResult(details)
    setApplied(true)
    onApply(final, discountEUR, details)
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
            onClick={handleApply}
            disabled={!selectedPct}
            className="rounded-lg bg-black px-3 py-2 text-sm text-white disabled:opacity-60"
          >
            Applica sconto
          </button>
          {applied && result && (
            <div className="text-sm text-green-700">Sconto applicato: -{Number(result['discount_eur'] ?? 0).toFixed(2)} EUR</div>
          )}
        </div>
      </div>

      {applied && result && (
        <div className="mt-4 rounded-lg border bg-gray-50 p-3 text-sm">
          <div className="flex justify-between"><span>Sconto:</span><span>-{Number(result['discount_eur'] ?? 0).toFixed(2)} EUR</span></div>
          <div className="flex justify-between"><span>TEO richiesti:</span><span>{Number(result['teo_required'] ?? 0).toFixed(2)} TEO</span></div>
          <div className="flex justify-between font-semibold"><span>Totale finale:</span><span>{(priceEUR - Number(result['discount_eur'] ?? 0)).toFixed(2)} EUR</span></div>
        </div>
      )}
    </div>
  );
}
