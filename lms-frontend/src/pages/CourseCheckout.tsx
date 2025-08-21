// src/pages/CourseCheckout.tsx
import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getPaymentSummary, purchaseCourse, type PaymentSummary } from "../services/payments";
import PriceBreakdown from "../components/PriceBreakdown";
import { showToast } from "../components/ToastHost";

export default function CourseCheckout() {
  const { id } = useParams<{ id: string }>();
  const courseId = Number(id);
  const navigate = useNavigate();

  const [loading, setLoading] = React.useState(true);
  const [summary, setSummary] = React.useState<PaymentSummary | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [purchasing, setPurchasing] = React.useState(false);

  React.useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      const res = await getPaymentSummary(courseId);
      if (!mounted) return;

      if (res.ok) {
        setSummary(res.data);
      } else {
        setSummary({
          course_id: courseId,
          // fallback minimale se il BE non ha il summary
          price_eur: undefined,
          discount_percent: undefined,
          total_eur: undefined,
          raw: null,
        });
        setError("Impossibile recuperare il riepilogo pagamento.");
      }
      setLoading(false);
    }
    load();
    return () => { mounted = false; };
  }, [courseId]);

  async function onPurchase() {
    setPurchasing(true);
    const res = await purchaseCourse(courseId, {});
    setPurchasing(false);

    if (res.ok) {
      showToast({ variant: "success", message: "Acquisto completato. Sei iscritto al corso!" });
      navigate(`/courses/${courseId}`);
    } else {
      showToast({ variant: "error", message: "Acquisto non riuscito. Riprova più tardi." });
    }
  }

  if (!Number.isFinite(courseId)) {
    return <div className="p-6">ID corso non valido.</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Acquisto corso</h1>
        <p className="text-sm text-muted-foreground">
          Conferma l’acquisto del corso {summary?.title ? <strong>“{summary.title}”</strong> : `#${courseId}`}
        </p>
      </div>

      {loading && <div>Caricamento riepilogo…</div>}
      {!loading && error && (
        <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-700 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </div>
      )}

      {!loading && summary && <PriceBreakdown summary={summary} />}

      <div className="flex gap-3">
        <button
          onClick={() => navigate(-1)}
          className="h-10 rounded-lg border px-4"
          disabled={purchasing}
        >
          Indietro
        </button>
        <button
          onClick={onPurchase}
          className="h-10 rounded-lg bg-primary px-4 text-primary-foreground hover:opacity-90 disabled:opacity-50"
          disabled={purchasing}
        >
          {purchasing ? "Acquisto in corso…" : "Acquista ora"}
        </button>
      </div>
    </div>
  );
}
