import { useEffect, useState } from "react";
import { getWallet, getTransactions, type WalletInfo, type WalletTransaction } from "../services/wallet";

type Page<T> = { count: number; next?: string | null; previous?: string | null; results: T[] };

export default function WalletPage() {
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const [tx, setTx] = useState<WalletTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);

  useEffect(() => {
    let alive = true;
    async function load() {
      setLoading(true);
      setError(null);
      const [w, t] = await Promise.all([getWallet(), getTransactions(page, 20)]);
      if (!alive) return;

      if (w.ok) setWallet(w.data);
      else setError(`Wallet error: ${w.status}`);

      if (t.ok) {
        const data = t.data as Page<WalletTransaction>;
        setTx(data.results || []);
        setCount(data.count || 0);
      } else {
        setError(prev => prev ?? `Transactions error: ${t.status}`);
      }
      setLoading(false);
    }
    load();
    return () => { alive = false; };
  }, [page]);

  return (
    <div className="mx-auto max-w-5xl p-4 md:p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Wallet TEO</h1>

      {/* Stato */}
      {loading && <div className="animate-pulse h-24 rounded-xl bg-gray-200/50" />}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
          {error} — Assicurati di essere loggato.
          {/* se l'errore è un 404 collettivo potremmo anche mostrare gli endpoint provati */}
        </div>
      )}

      {/* Card saldo */}
      {wallet && (
        <div className="rounded-2xl border bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-sm text-gray-500">Saldo disponibile</div>
              <div className="mt-1 text-3xl font-bold">{wallet.balance_teo.toFixed(2)} TEO</div>
              {typeof wallet.balance_eur === "number" && (
                <div className="text-sm text-gray-500">≈ {wallet.balance_eur.toFixed(2)} EUR</div>
              )}
            </div>
            {wallet.address && (
              <div className="text-right">
                <div className="text-xs text-gray-500">Indirizzo</div>
                <div className="font-mono text-sm break-all">{wallet.address}</div>
              </div>
            )}
          </div>
          {wallet.updated_at && (
            <div className="mt-3 text-xs text-gray-500">Aggiornato: {new Date(wallet.updated_at).toLocaleString()}</div>
          )}
        </div>
      )}

      {/* Movimenti */}
      <div className="rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center justify-between p-4">
          <h2 className="text-lg font-medium">Movimenti</h2>
          <div className="text-sm text-gray-500">Totale: {count}</div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr className="text-left">
                <th className="px-4 py-2">Data</th>
                <th className="px-4 py-2">Tipo</th>
                <th className="px-4 py-2">Descrizione</th>
                <th className="px-4 py-2 text-right">Importo (TEO)</th>
              </tr>
            </thead>
            <tbody>
              {tx.map((r) => (
                <tr key={String(r.id)} className="border-t">
                  <td className="px-4 py-2">{new Date(r.created_at).toLocaleString()}</td>
                  <td className="px-4 py-2">{r.type}</td>
                  <td className="px-4 py-2">{r.description ?? "-"}</td>
                  <td className="px-4 py-2 text-right font-medium">
                    {r.amount_teo >= 0 ? "+" : ""}
                    {r.amount_teo.toFixed(2)}
                  </td>
                </tr>
              ))}
              {!loading && tx.length === 0 && (
                <tr><td className="px-4 py-6 text-center text-gray-500" colSpan={4}>Nessun movimento</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Paginazione semplice */}
        <div className="flex items-center justify-between p-4">
          <button
            className="rounded-lg border px-3 py-1 text-sm disabled:opacity-50"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
          >Precedente</button>
          <div className="text-sm">Pagina {page}</div>
          <button
            className="rounded-lg border px-3 py-1 text-sm disabled:opacity-50"
            onClick={() => setPage(p => p + 1)}
            disabled={loading || (page * 20 >= count)}
          >Successiva</button>
        </div>
      </div>
    </div>
  );
}
