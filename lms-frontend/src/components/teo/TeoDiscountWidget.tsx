import React, { useMemo, useState } from "react";
import { checkDiscount, applyDiscount } from "@/services/wallet";
import { showToast } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Props = {
  courseId: number;
  priceEUR: number;
  studentAddress: string;
  className?: string;
  onApplied?: (result: any) => void;
};

type Summary = {
  price_eur?: number;
  discount_percent?: number;
  discounted_eur?: number;
  teo_cost?: number;
  detail?: string;
  [k: string]: any;
};

function clamp01(n: number) {
  return Math.max(0, Math.min(1, n));
}

async function retry<T>(fn: () => Promise<T>, attempts = 2, waitMs = 400): Promise<T> {
  let err: any;
  for (let i = 0; i <= attempts; i++) {
    try {
      return await fn();
    } catch (e) {
      err = e;
      if (i < attempts) await new Promise((r) => setTimeout(r, waitMs * (i + 1)));
    }
  }
  throw err;
}

export default function TeoDiscountWidget({ courseId, priceEUR, studentAddress, className, onApplied }: Props) {
  const [code, setCode] = useState("");
  const [percent, setPercent] = useState<number | "">("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [applied, setApplied] = useState(false);

  const computedDiscounted = useMemo(() => {
    if (summary?.discounted_eur != null) return summary.discounted_eur;
    const p = typeof percent === "number" ? clamp01(percent / 100) : 0;
    return Number((priceEUR * (1 - p)).toFixed(2));
  }, [summary, percent, priceEUR]);

  async function handleCheck() {
    setLoading(true);
    try {
      const s = await retry(
        () =>
          checkDiscount({
            student_address: studentAddress,
            course_id: courseId,
            code: code || undefined,
            amount: priceEUR,
          }),
        1
      );
      setSummary(s);
      showToast({
        variant: "success",
        title: "Sconto verificato",
        message: s?.detail || "Puoi procedere all'applicazione.",
      });
    } catch (e: any) {
      setSummary(null);
      showToast({
        variant: "error",
        title: "Verifica sconto fallita",
        message: e?.message || "Controllo non riuscito.",
      });
    } finally {
      setLoading(false);
    }
  }

  async function handleApply() {
    setLoading(true);
    try {
      // verifica sempre prima di applicare
      if (!summary) {
        await handleCheck();
        if (!summary) return;
      }
      const res = await retry(
        () =>
          applyDiscount({
            student_address: studentAddress,
            course_id: courseId,
            amount: priceEUR,
            code: code || undefined,
          }),
        1
      );
      setApplied(true);
      showToast({
        variant: "success",
        title: "Sconto applicato",
        message: "Il pagamento ibrido può proseguire.",
      });
      onApplied?.(res);
    } catch (e: any) {
      showToast({
        variant: "error",
        title: "Applicazione sconto fallita",
        message: e?.message || "Operazione non riuscita.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className={cn("max-w-xl", className)}>
      <CardHeader>
        <CardTitle>Usa TEO per lo sconto</CardTitle>
        <CardDescription>Verifica e applica lo sconto prima del checkout.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm text-neutral-600 dark:text-neutral-300">
              Codice sconto (opzionale)
            </label>
            <Input
              placeholder="TEO-2025..."
              value={code}
              onChange={(e) => setCode(e.target.value)}
              disabled={loading || applied}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-neutral-600 dark:text-neutral-300">
              Percentuale (opzionale)
            </label>
            <Input
              type="number"
              placeholder="Es. 15"
              value={percent}
              onChange={(e) => {
                const v = e.target.value;
                if (v === "") return setPercent("");
                const n = Number(v);
                if (!Number.isNaN(n)) setPercent(Math.max(0, Math.min(100, n)));
              }}
              suffix={<span className="text-neutral-500">%</span>}
              disabled={loading || applied}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-neutral-500 dark:text-neutral-400">Prezzo</div>
          <div className="text-right font-medium">€ {priceEUR.toFixed(2)}</div>
          <div className="text-neutral-500 dark:text-neutral-400">Sconto</div>
          <div className="text-right font-medium">
            {summary?.discount_percent != null
              ? `${summary.discount_percent}%`
              : typeof percent === "number"
              ? `${percent}%`
              : "—"}
          </div>
          <div className="text-neutral-500 dark:text-neutral-400">Totale</div>
          <div className="text-right font-semibold">€ {computedDiscounted.toFixed(2)}</div>
        </div>

        {summary?.teo_cost != null ? (
          <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-3 text-sm dark:border-neutral-800 dark:bg-neutral-900/40">
            TEO richiesti: <span className="font-medium">{summary.teo_cost}</span>
          </div>
        ) : null}
      </CardContent>
      <CardFooter className="flex gap-2">
        <button
          className={cn(
            "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium",
            "bg-neutral-900 text-white hover:bg-neutral-800 active:translate-y-px",
            "disabled:opacity-60 disabled:pointer-events-none"
          )}
          onClick={handleCheck}
          disabled={loading || applied}
        >
          {loading ? "Verifico…" : "Verifica sconto"}
        </button>
        <button
          className={cn(
            "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium",
            "bg-emerald-600 text-white hover:bg-emerald-700 active:translate-y-px",
            "disabled:opacity-60 disabled:pointer-events-none"
          )}
          onClick={handleApply}
          disabled={loading || applied}
        >
          {applied ? "Sconto applicato" : "Applica sconto"}
        </button>
      </CardFooter>
    </Card>
  );
}
