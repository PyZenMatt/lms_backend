import React from "react";
import { useAuth } from "../../context/AuthContext";
import { getStakingOverview, stakeTeo, unstakeTeo } from "../../services/payments";
import type { StakingOverview } from "../../services/payments";
import { showToast } from "../../components/ToastHost";

export default function StakingPage() {
  const { isAuthenticated, isTeacher } = useAuth();
  const [overview, setOverview] = React.useState<StakingOverview | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [amount, setAmount] = React.useState<string>("");
  const [actionLoading, setActionLoading] = React.useState(false);

  const fetchOverview = React.useCallback(async () => {
    setLoading(true);
    const res = await getStakingOverview();
    setLoading(false);
    if (!res.ok) return;
    setOverview(res.data ?? null);
  }, []);

  React.useEffect(() => {
    if (isAuthenticated && isTeacher) fetchOverview();
  }, [fetchOverview, isAuthenticated, isTeacher]);

  function fmtTeo(v?: number) {
    if (v === undefined) return "-";
    return v.toFixed(8);
  }

  async function doStake() {
    if (!amount) return showToast({ variant: "info", message: "Inserisci un importo" });
    const n = Number(amount);
    if (!Number.isFinite(n) || n <= 0) return showToast({ variant: "error", message: "Importo non valido" });
    // validate against balance
    if (overview?.balance_teo !== undefined && n > overview.balance_teo) return showToast({ variant: "error", message: "Importo maggiore del saldo" });
    setActionLoading(true);
    const res = await stakeTeo(amount);
    setActionLoading(false);
    if (!res.ok) return;
    showToast({ variant: "success", message: "Stake completato" });
    fetchOverview();
  }

  async function doUnstake() {
    if (!amount) return showToast({ variant: "info", message: "Inserisci un importo" });
    const n = Number(amount);
    if (!Number.isFinite(n) || n <= 0) return showToast({ variant: "error", message: "Importo non valido" });
    if (overview?.staked_teo !== undefined && n > overview.staked_teo) return showToast({ variant: "error", message: "Importo maggiore dello staked" });
    setActionLoading(true);
    const res = await unstakeTeo(amount);
    setActionLoading(false);
    if (!res.ok) return;
    showToast({ variant: "success", message: "Unstake completato" });
    fetchOverview();
  }

  const progressPct = (() => {
    const cur = overview?.staked_teo ?? 0;
    const next = overview?.next_tier_threshold_teo ?? 0;
    if (!next || next <= 0) return 100;
    return Math.min(100, Math.round((cur / next) * 100));
  })();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">Staking TEO</h1>
      {loading && <div>Caricamento...</div>}
      {!loading && overview && (
        <div className="space-y-4">
          <div className="p-4 border rounded-md">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-muted">Tier corrente</div>
                <div className="text-lg font-semibold">{overview.tier_name ?? "-"} ({overview.bonus_multiplier ? `+${(overview.bonus_multiplier * 100).toFixed(0)}%` : "-"})</div>
              </div>
              <div className="text-right">
                <div className="text-sm text-muted">Saldo TEO</div>
                <div className="text-lg font-semibold">{fmtTeo(overview.balance_teo)}</div>
              </div>
            </div>
            <div className="mt-4">
              <div className="w-full bg-gray-200 h-3 rounded overflow-hidden">
                <div style={{ width: `${progressPct}%` }} className="h-3 bg-emerald-600" />
              </div>
              <div className="text-sm mt-1">Progresso verso {overview.next_tier ?? "-"}: {progressPct}%</div>
            </div>
          </div>

          <div className="p-4 border rounded-md">
            <div className="mb-2">Stake / Unstake</div>
            <input
              type="number"
              step="0.00000001"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="border px-2 py-1 rounded mr-2"
              placeholder="0.00000000"
            />
            <button onClick={doStake} disabled={actionLoading} className="px-3 py-1 rounded bg-emerald-600 text-white mr-2">Stake</button>
            <button onClick={doUnstake} disabled={actionLoading} className="px-3 py-1 rounded bg-red-600 text-white">Unstake</button>
          </div>

          <div className="text-xs text-muted">1 TEO = 1 EUR (contabile). I bonus dipendono dal tier.</div>
        </div>
      )}
      {!loading && !overview && <div>Staking non disponibile.</div>}
    </div>
  );
}
