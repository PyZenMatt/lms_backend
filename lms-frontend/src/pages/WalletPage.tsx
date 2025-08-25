import { useEffect, useState } from "react";
import { getWallet, getTransactions, type WalletInfo, type WalletTransaction } from "@/services/wallet";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, THead, TBody, TR, TH, TD, TableEmpty } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

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
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Wallet TEO</h1>

      {/* Card saldo */}
      {loading && <Skeleton className="h-24 rounded-2xl" />}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
          {error} — Assicurati di essere loggato.
        </div>
      )}
      {wallet && (
        <Card>
          <CardHeader>
            <CardTitle>Saldo disponibile</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-start justify-between">
              <div>
                <div className="mt-1 text-3xl font-bold">{wallet.balance_teo.toFixed(2)} TEO</div>
                {typeof wallet.balance_eur === "number" && (
                  <div className="text-sm text-muted-foreground">≈ {wallet.balance_eur.toFixed(2)} EUR</div>
                )}
              </div>
              {wallet.address && (
                <div className="text-right">
                  <div className="text-xs text-muted-foreground">Indirizzo</div>
                  <div className="font-mono text-sm break-all">{wallet.address}</div>
                </div>
              )}
            </div>
            {wallet.updated_at && (
              <div className="mt-3 text-xs text-muted-foreground">
                Aggiornato: {new Date(wallet.updated_at).toLocaleString()}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Movimenti */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Movimenti</CardTitle>
          <div className="text-sm text-muted-foreground">Totale: {count}</div>
        </CardHeader>
        <CardContent>
          {tx.length === 0 && !loading ? (
            <TableEmpty>Nessun movimento</TableEmpty>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <THead>
                  <TR>
                    <TH>Data</TH>
                    <TH>Tipo</TH>
                    <TH>Descrizione</TH>
                    <TH className="text-right">Importo (TEO)</TH>
                  </TR>
                </THead>
                <TBody>
                  {tx.map((r) => (
                    <TR key={String(r.id)}>
                      <TD>{new Date(r.created_at).toLocaleString()}</TD>
                      <TD>{r.type}</TD>
                      <TD>{r.description ?? "-"}</TD>
                      <TD className="text-right font-medium">
                        {r.amount_teo >= 0 ? "+" : ""}
                        {r.amount_teo.toFixed(2)}
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            </div>
          )}

          {/* Paginazione semplice */}
          <div className="mt-4 flex items-center justify-between">
            <button
              className="rounded-lg border px-3 py-1 text-sm disabled:opacity-50"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1 || loading}
            >
              Precedente
            </button>
            <div className="text-sm">Pagina {page}</div>
            <button
              className="rounded-lg border px-3 py-1 text-sm disabled:opacity-50"
              onClick={() => setPage((p) => p + 1)}
              disabled={loading || page * 20 >= count}
            >
              Successiva
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
