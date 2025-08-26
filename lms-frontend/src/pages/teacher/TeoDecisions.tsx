import React from "react";
import { useAuth } from "../../context/AuthContext";
import { listPendingTeoDecisions, acceptTeo, rejectTeo } from "../../services/payments";
import type { PendingTeoDecision } from "../../services/payments";
import { showToast } from "../../components/ToastHost";

export default function TeoDecisionsPage() {
  const { isAuthenticated, isTeacher, pendingTeoCount, setPendingTeoCount } = useAuth();
  const [items, setItems] = React.useState<PendingTeoDecision[]>([]);
  const [loading, setLoading] = React.useState<boolean>(false);
  const mounted = React.useRef(true);

  const fetchList = React.useCallback(async () => {
    setLoading(true);
    const res = await listPendingTeoDecisions();
    if (!mounted.current) return;
    setLoading(false);
    if (!res.ok) return;
    setItems(res.data ?? []);
    setPendingTeoCount((res.data ?? []).length);
  }, [setPendingTeoCount]);

  React.useEffect(() => {
    mounted.current = true;
    if (isAuthenticated && isTeacher) fetchList();
    const iv = window.setInterval(() => {
      if (document.visibilityState === "visible" && isAuthenticated && isTeacher) fetchList();
    }, 30_000);
    return () => {
      mounted.current = false;
      clearInterval(iv);
    };
  }, [fetchList, isAuthenticated, isTeacher]);

  async function doDecision(id: number, accept: boolean) {
    // optimistic: disable button via local map
    const original = items.slice();
    setItems((arr) => arr.filter((i) => i.id !== id));
    try {
      const res = accept ? await acceptTeo(id) : await rejectTeo(id);
      if (!res.ok) {
        if (res.status === 409 || res.status === 422) {
          showToast({ variant: "info", message: "Decisione già presa" });
        } else {
          showToast({ variant: "error", message: "Errore durante l'azione" });
          setItems(original);
        }
      } else {
        showToast({ variant: "success", message: "Decisione registrata" });
        setPendingTeoCount(Math.max(0, pendingTeoCount - 1));
      }
  } catch {
      showToast({ variant: "error", message: "Errore di rete" });
      setItems(original);
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">TEO da decidere</h1>
      {loading && <div>Caricamento...</div>}
      {!loading && items.length === 0 && <div>Nessuna decisione in attesa.</div>}
      {items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full table-auto border-collapse">
            <thead>
              <tr>
                <th className="text-left">Ordine</th>
                <th className="text-left">Corso</th>
                <th className="text-left">Studente</th>
                <th className="text-right">Docente EUR</th>
                <th className="text-right">TEO offerti</th>
                <th className="text-right">Bonus atteso</th>
                <th className="text-left">Scadenza</th>
                <th className="text-left">Azione</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id} className="border-t">
                  <td>{it.order_id ?? it.id}</td>
                  <td>{it.course_title}</td>
                  <td>{it.student_name}</td>
                  <td className="text-right">{it.teacher_eur?.toFixed(2) ?? "-"} €</td>
                  <td className="text-right">{(it.teacher_teo ?? 0).toFixed(8)}</td>
                  <td className="text-right">{(it.expected_bonus_teo ?? 0).toFixed(8)}</td>
                  <td>{it.deadline_at ?? "-"}</td>
                  <td>
                    <div className="flex gap-2">
                      <button
                        onClick={() => doDecision(it.id, true)}
                        className="px-3 py-1 rounded bg-emerald-600 text-white"
                      >
                        Accetta
                      </button>
                      <button
                        onClick={() => doDecision(it.id, false)}
                        className="px-3 py-1 rounded bg-red-600 text-white"
                      >
                        Rifiuta
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
