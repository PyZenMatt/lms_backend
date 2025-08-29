import { useEffect, useState } from "react";

// typed helper for the ad-hoc refresh hook exposed on window
type WalletRefreshFn = (() => Promise<void>) | undefined;
declare global {
  interface Window { __wallet_refresh__?: WalletRefreshFn }
}
import { getWallet, getTransactions, type WalletInfo, type WalletTransaction, coerceNumber, verifyDeposit, refreshBalance } from "@/services/wallet";
import { getTxStatus } from "@/features/wallet/walletApi";
import { useWeb3 } from "@/web3/context";
import { queryClient } from "@/lib/queryClientInstance";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert } from "@/components/ui/alert";
import EmptyState from "@/components/ui/empty-state";
import WalletConnectButton from "@/features/wallet/WalletConnectButton";
import WalletActions from "@/features/wallet/WalletActions";
import TxStatusPanel from "@/features/wallet/components/TxStatusPanel";

type Page<T> = { count: number; next?: string | null; previous?: string | null; results: T[] };

export default function WalletPage() {
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const [tx, setTx] = useState<WalletTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  // no direct on-chain context here: WalletPage uses server-side mint/burn endpoints

  // extract load/refresh so it can be called after mint/burn
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
  // expose for children's usage via a bound function
  window.__wallet_refresh__ = load as WalletRefreshFn;
    load();

  // Listen for external signals to refresh wallet (e.g. after discount accept)
  const onUpdated = () => { void window.__wallet_refresh__?.(); };
  const onNotifUpdated = () => { void window.__wallet_refresh__?.(); };
  window.addEventListener("wallet:updated", onUpdated as EventListener);
  window.addEventListener("notifications:updated", onNotifUpdated as EventListener);
  return () => { alive = false; window.removeEventListener("wallet:updated", onUpdated as EventListener); window.removeEventListener("notifications:updated", onNotifUpdated as EventListener); };
  }, [page]);

  // Helper: try to read available balance from raw payload or derive from total - staked
  function parseAvailableFromRaw(w: WalletInfo | null): number | null {
    if (!w) return null;
    const raw: unknown = (w as unknown as { raw?: unknown }).raw ?? null;
    if (raw) {
      const b = (raw as Record<string, unknown>).balance ?? raw as Record<string, unknown>;
      if (b) {
        const availableRaw = (b as Record<string, unknown>).available_balance ?? (b as Record<string, unknown>).available ?? (b as Record<string, unknown>).available_teo ?? (b as Record<string, unknown>).available_teocoin;
        if (availableRaw !== undefined && availableRaw !== null) {
          const n = coerceNumber(availableRaw);
          if (Number.isFinite(n)) return n;
        }
        // try derive from total - staked
        const totalRaw = (b as Record<string, unknown>).total_balance ?? (b as Record<string, unknown>).total ?? w.balance_teo;
        const stakedRaw = (b as Record<string, unknown>).staked_balance ?? (b as Record<string, unknown>).staked ?? (raw as Record<string, unknown>).staked_teo ?? (raw as Record<string, unknown>).staked;
        const t = coerceNumber(totalRaw);
        const s = coerceNumber(stakedRaw);
        if (Number.isFinite(t) && Number.isFinite(s)) return Math.max(0, t - s);
      }
      // fallback if top-level raw has staked and balance_teo
      const topStaked = (raw as Record<string, unknown>).staked_teo ?? (raw as Record<string, unknown>).staked;
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
      {/* Wallet connect */}
      <div>
        <WalletConnectButton />
      </div>

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

  {/* Legacy DB Mint/Burn controls removed for on-chain-only MVP */}

      {/* MetaMask on-chain bridge: Withdraw (DB→chain) and Deposit verify (chain→DB) */}
      <Card>
        <CardHeader>
          <CardTitle>MetaMask bridge (chain)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="font-medium">Preleva (DB → MetaMask)</h3>
              <WalletActions />
            </div>

            <div>
              <h3 className="font-medium">Deposita (chain → DB)</h3>
              <DepositForm onVerify={async (tx: string) => {
                // call service directly and forward result data so form can show amount/tx
                const res = await verifyDeposit(tx);
                if (res.ok) {
                  // backend may return { success: true, amount, tx_hash, ... } even on HTTP 200
                  const data = res.data as Record<string, unknown>;
                  // invalidate cache and refresh
                  queryClient.invalidateQueries({ queryKey: ["wallet","balance"] });
                  queryClient.invalidateQueries({ queryKey: ["wallet","txs"] });
                  void window.__wallet_refresh__?.();
                  return { ok: true, data } as { ok: true; data?: Record<string, unknown> };
                }
                // include more info for error UI when available
                return { ok: false, error: res.error ?? (res as unknown as Record<string, unknown>)?.data ?? 'verify failed' };
              }} />
            </div>
          </div>
        </CardContent>
      </Card>

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

// Legacy MintBurnForm removed: on-chain flows handled via WalletActions

function DepositForm({ onVerify }: { onVerify: (tx_hash: string) => Promise<{ ok: boolean; data?: Record<string, unknown>; error?: unknown }> }) {
  // no inline tx input anymore
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle'|'pending'|'success'|'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [resultData, setResultData] = useState<Record<string, unknown> | null>(null);


  // explorer base is provided by TxStatusPanel via VITE_EXPLORER_TX

  return (
    <div className="flex flex-col gap-2">
      <div className="text-sm">Verifica deposito on-chain</div>
      <div className="flex gap-2">
        <button
          type="button"
          className="rounded bg-primary px-3 py-1 text-white disabled:opacity-50"
          onClick={async () => {
            const input = window.prompt("Incolla qui il transaction hash (0x...):") ?? "";
            if (!input) return;
            const txhash = input.trim();
            setLoading(true);
            setStatus('pending');
            setError(null);
            try {
              const res = await onVerify(txhash);
              if (res.ok) {
                setStatus('success');
                setResultData(res.data ?? null);
              } else {
                const err = res.error ?? 'Verification failed';
                if (typeof err === 'object' && err !== null) {
                  const eobj = err as Record<string, unknown>;
                  if (eobj.status === 'pending') {
                    setStatus('pending');
                    setError((eobj.message as string) ?? 'Transazione non ancora confermata. Riprova più tardi.');
                  } else {
                    setStatus('error');
                    setError(String(eobj.message ?? eobj.error ?? JSON.stringify(eobj)));
                  }
                } else {
                  setStatus('error');
                  setError(String(err));
                }
              }
            } catch (e) {
              setStatus('error');
              setError(String(e));
            } finally {
              setLoading(false);
            }
          }}
        >
          {loading ? '...' : 'Verifica transazione'}
        </button>
      </div>

      {status === 'success' && resultData && (
        <div className="text-sm text-green-700">
          ✅ Deposito verificato
          {resultData.amount !== undefined && resultData.amount !== null && (
            <div>Importo accreditato: {String(resultData.amount)} TEO</div>
          )}
          {resultData.tx_hash !== undefined && resultData.tx_hash !== null && (
            <div className="mt-2">
              <TxStatusPanel identifier={String(resultData.tx_hash)} />
            </div>
          )}
        </div>
      )}

      {status === 'pending' && (
        <div className="text-sm text-amber-700">⏳ Transazione in attesa di conferma. Ritenta tra qualche istante.</div>
      )}

      {status === 'error' && error && (
        <div className="text-xs text-red-600">{error}</div>
      )}
    </div>
  );
}

// Legacy WithdrawPanel removed: use WalletActions for on-chain interactions
