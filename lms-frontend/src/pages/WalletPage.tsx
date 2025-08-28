import { useEffect, useState } from "react";
import { getWallet, getTransactions, type WalletInfo, type WalletTransaction, coerceNumber } from "@/services/wallet";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert } from "@/components/ui/alert";
import EmptyState from "@/components/ui/empty-state";

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

    // Listen for external signals to refresh wallet (e.g. after discount accept)
  const onUpdated = () => { void load(); };
  window.addEventListener("wallet:updated", onUpdated as EventListener);
  return () => { alive = false; window.removeEventListener("wallet:updated", onUpdated as EventListener); };
  }, [page]);

  // Helper: try to read available balance from raw payload or derive from total - staked
  function parseAvailableFromRaw(w: WalletInfo | null): number | null {
    if (!w) return null;
    const raw: any = (w as any).raw ?? null;
    if (raw) {
      const b = raw.balance ?? raw;
      if (b) {
        const availableRaw = b.available_balance ?? b.available ?? b.available_teo ?? b.available_teocoin;
        if (availableRaw !== undefined && availableRaw !== null) {
          const n = coerceNumber(availableRaw);
          if (Number.isFinite(n)) return n;
        }
        // try derive from total - staked
        const totalRaw = b.total_balance ?? b.total ?? w.balance_teo;
        const stakedRaw = b.staked_balance ?? b.staked ?? raw.staked_teo ?? raw.staked;
        const t = coerceNumber(totalRaw);
        const s = coerceNumber(stakedRaw);
        if (Number.isFinite(t) && Number.isFinite(s)) return Math.max(0, t - s);
      }
      // fallback if top-level raw has staked and balance_teo
      const topStaked = raw.staked_teo ?? raw.staked;
      if (topStaked !== undefined && topStaked !== null && typeof w.balance_teo === 'number') {
        const s = coerceNumber(topStaked);
        if (Number.isFinite(s)) return Math.max(0, w.balance_teo - s);
      }
    }
    // default to balance_teo
    return typeof w.balance_teo === 'number' ? w.balance_teo : null;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Wallet TEO</h1>

      {/* Card saldo */}
      {loading && <Skeleton className="h-24 rounded-2xl" />}
      {error && (
        <Alert variant="error" title="Errore">
          {error} — Assicurati di essere loggato.
        </Alert>
      )}
      {wallet && (
        <Card>
          <CardHeader>
            <CardTitle>Saldo disponibile</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-start justify-between">
              <div>
                {(() => {
                  const displayed = parseAvailableFromRaw(wallet);
                  return <div className="mt-1 text-3xl font-bold">{(displayed !== null ? displayed : wallet.balance_teo).toFixed(2)} TEO</div>;
                })()}
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
          {count === 0 && !loading ? (
            <EmptyState title="Nessun movimento" description="Non ci sono movimenti da mostrare." />
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
