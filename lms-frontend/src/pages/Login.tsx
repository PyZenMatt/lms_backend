import React from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { getAccessToken, getRoleFromToken } from "@/lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const location = useLocation() as any;
  const from: string | undefined = location?.state?.from?.pathname;

  const [ident, setIdent] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [msg, setMsg] = React.useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("Signing in...");
    const ok = await login(ident, password);
    if (!ok) { setMsg("Credenziali non valide"); return; }
    setMsg("OK");

    if (from && from !== "/login") {
      nav(from, { replace: true });
      return;
    }

    // Decide la home in base al ruolo
    const role = getRoleFromToken(getAccessToken());
    if (role === "admin")      { nav("/admin", { replace: true }); return; }
    if (role === "teacher")    { nav("/teacher", { replace: true }); return; }
    /* student/default */        nav("/dashboard", { replace: true });
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-6">
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-3 p-6 rounded-lg border border-border bg-card text-card-foreground">
        <h1 className="text-xl font-bold">Accedi</h1>
        <input
          className="w-full px-3 py-2 rounded-md border border-border bg-background"
          placeholder="Email o Username"
          value={ident}
          onChange={e=>setIdent(e.target.value)}
          autoComplete="username"
        />
        <input
          type="password"
          className="w-full px-3 py-2 rounded-md border border-border bg-background"
          placeholder="Password"
          value={password}
          onChange={e=>setPassword(e.target.value)}
          autoComplete="current-password"
        />
        <button type="submit" className="w-full px-3 py-2 rounded-md bg-primary text-primary-foreground hover:opacity-90">
          Entra
        </button>
        <div className="text-sm text-muted-foreground">{msg}</div>
        <div className="text-sm">
          Non hai un account? <Link to="/register" className="underline">Registrati</Link>
        </div>
      </form>
    </div>
  );
}
