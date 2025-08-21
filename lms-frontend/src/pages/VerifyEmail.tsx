import React from "react";
import { useParams, Link, Navigate } from "react-router-dom";
import { apiFetch } from "../lib/api";

export default function VerifyEmail() {
  const { uid, token } = useParams<{ uid: string; token: string }>();
  const [status, setStatus] = React.useState<"loading" | "ok" | "error">("loading");
  const [detail, setDetail] = React.useState<string>("");

  React.useEffect(() => {
    (async () => {
      if (!uid || !token) { setStatus("error"); setDetail("Parametri mancanti"); return; }
      const res = await apiFetch(`/v1/verify-email/${uid}/${token}/`, { method: "GET" });
      if (res.ok) setStatus("ok");
      else { setStatus("error"); setDetail((res.data as any)?.detail || `HTTP ${res.status}`); }
    })();
  }, [uid, token]);

  if (status === "loading") return (
    <div className="min-h-screen bg-background text-foreground grid place-items-center p-6">
      <div className="text-sm text-muted-foreground">Verifica in corso…</div>
    </div>
  );

  if (status === "ok") return (
    <div className="min-h-screen bg-background text-foreground grid place-items-center p-6">
      <div className="w-full max-w-md space-y-3 p-6 rounded-lg border border-border bg-card text-card-foreground">
        <h1 className="text-xl font-bold">Email verificata ✅</h1>
        <p className="text-sm text-muted-foreground">Il tuo account è attivo. Ora puoi accedere.</p>
        <Link to="/login" className="inline-block px-3 py-2 rounded-md bg-primary text-primary-foreground">Vai al Login</Link>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background text-foreground grid place-items-center p-6">
      <div className="w-full max-w-md space-y-3 p-6 rounded-lg border border-border bg-card text-card-foreground">
        <h1 className="text-xl font-bold">Verifica non riuscita</h1>
        <p className="text-sm text-destructive">Dettagli: {detail}</p>
        <div className="text-sm">
          Torna al <Link to="/login" className="underline">Login</Link>
        </div>
      </div>
    </div>
  );
}

