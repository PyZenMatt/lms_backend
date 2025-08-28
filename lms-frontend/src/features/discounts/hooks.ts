import { useCallback, useEffect, useState } from "react";
import { discountsApi } from "./api";
import type { DecisionResponse, PendingListItem } from "./types";

function errMsg(e: unknown): string {
  if (!e) return "";
  if (typeof e === 'string') return e;
  if (typeof e === 'object' && e !== null && 'message' in e) {
    return String((e as any).message);
  }
  return String(e);
}

function isPromise(v: unknown): v is Promise<unknown> {
  return !!v && typeof v === "object" && typeof ((v as unknown) as { then?: unknown }).then === "function";
}

export function usePendingDiscounts() {
  const [data, setData] = useState<PendingListItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await discountsApi.listPending();
      setData(res.results ?? []);
    } catch (e: unknown) {
      setError(errMsg(e) || "Errore");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refetch(); }, [refetch]);

  return { items: data ?? [], loading, error, refetch };
}

export function useAcceptDecline(opts?: { onAfterChange?: (resp: DecisionResponse) => void | Promise<void> }) {
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const accept = useCallback(async (decisionId: number) => {
    setBusyId(decisionId);
    setError(null);
    try {
      const resp = await discountsApi.acceptDecision(decisionId);
      // Await the callback if it returns a promise to ensure refetch completes
  const maybePromise = opts?.onAfterChange?.(resp);
  if (isPromise(maybePromise)) await (maybePromise as unknown as Promise<void>);
      return;
    } catch (e: unknown) {
      setError(errMsg(e) || "Errore");
      throw e;
    } finally {
      setBusyId(null);
    }
  }, [opts]);

  const decline = useCallback(async (decisionId: number) => {
    setBusyId(decisionId);
    setError(null);
    try {
      const resp = await discountsApi.declineDecision(decisionId);
  const maybePromise = opts?.onAfterChange?.(resp);
  if (isPromise(maybePromise)) await (maybePromise as unknown as Promise<void>);
      return;
    } catch (e: unknown) {
      setError(errMsg(e) || "Errore");
      throw e;
    } finally {
      setBusyId(null);
    }
  }, [opts]);

  return { accept, decline, busyId, error };
}
