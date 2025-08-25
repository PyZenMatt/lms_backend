// src/components/checkout/ReceiptCard.tsx
type Receipt = {
  final_price_eur: number;
  discount_eur: number;
  teo_spent?: number;
  stripe_client_secret?: string;
  order_id?: string | number;
  created_at?: string;
};

export default function ReceiptCard({ r }: { r: Receipt }) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <div className="text-lg font-semibold">Ricevuta</div>
      <div className="mt-3 space-y-1 text-sm">
        <div className="flex justify-between"><span>Prezzo finale</span><span className="font-medium">{r.final_price_eur.toFixed(2)} EUR</span></div>
        <div className="flex justify-between"><span>Sconto TEO</span><span>-{r.discount_eur.toFixed(2)} EUR</span></div>
        {typeof r.teo_spent === "number" && (
          <div className="flex justify-between"><span>TEO spesi</span><span>{r.teo_spent.toFixed(2)} TEO</span></div>
        )}
        {r.order_id && <div className="flex justify-between"><span>Ordine</span><span className="font-mono">{String(r.order_id)}</span></div>}
        {r.created_at && <div className="text-xs text-gray-500">Data: {new Date(r.created_at).toLocaleString()}</div>}
      </div>
    </div>
  );
}
