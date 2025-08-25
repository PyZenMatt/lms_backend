// src/pages/WalletPage.tsx
import React, { useEffect, useState } from "react";
import { getWallet, getTransactions, type WalletTransaction, type Paginated } from "@/services/wallet";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { showToast } from "@/lib/api";

export default function WalletPage() {
  const [loading, setLoading] = useState(true);
  const [balance, setBalance] = useState<{ balance: number; currency?: string; address?: string }>({ balance: 0 });
  const [txs, setTxs] = useState<Paginated<WalletTransaction> | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const [w, list] = await Promise.all([getWallet(), getTransactions({ page_size: 20 })]);
        if (cancelled) return;
        setBalance(w);
        setTxs(list);
      } catch (e: any) {
        showToast({ variant: "error", title: "Wallet", message: e?.message || "Impossibile caricare il wallet" });
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-6 p-4 md:p-6">
      <Card>
        <CardHeader>
          <CardTitle>Saldo</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {loading ? (
            <>
              <Skeleton className="h-12 rounded-xl" />
              <Skeleton className="h-12 rounded-xl" />
              <Skeleton className="h-12 rounded-xl" />
            </>
          ) : (
            <>
              <div className="rounded-xl border p-3 text-sm dark:border-neutral-800">
                <div className="text-neutral-500">Disponibile</div>
                <div className="text-xl font-semibold">{balance.balance} {balance.currency ?? "TEO"}</div>
              </div>
              <div className="rounded-xl border p-3 text-sm dark:border-neutral-800">
                <div className="text-neutral-500">Address</div>
                <div className="truncate">{balance.address ?? "—"}</div>
              </div>
              <div className="rounded-xl border p-3 text-sm dark:border-neutral-800">
                <div className="text-neutral-500">Transazioni</div>
                <div className="text-xl font-semibold">{txs?.count ?? 0}</div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Storico transazioni</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 rounded-xl" />
              <Skeleton className="h-10 rounded-xl" />
              <Skeleton className="h-10 rounded-xl" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data</TableHead>
                  <TableHead>Descrizione</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead className="text-right">Importo</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {txs?.results?.map((t) => (
                  <TableRow key={String(t.id)}>
                    <TableCell>{t.created_at ? new Date(t.created_at).toLocaleString() : "—"}</TableCell>
                    <TableCell>{t.description ?? "—"}</TableCell>
                    <TableCell>{t.status ?? "—"}</TableCell>
                    <TableCell className="text-right">
                      {t.direction === "out" ? "-" : "+"}
                      {t.amount} {t.currency ?? "TEO"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <TableCaption>Ultime operazioni del tuo wallet.</TableCaption>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
