import React from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate, Link } from "react-router-dom";

export default function LoginPage() {
  const { login, isTeacher } = useAuth();
  const nav = useNavigate();
  const [username, setU] = React.useState("");
  const [password, setP] = React.useState("");
  const [msg, setMsg] = React.useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("Signing in...");
    const ok = await login(username, password);
    if (!ok) { setMsg("Credenziali non valide"); return; }
    setMsg("OK");
    nav(isTeacher ? "/teacher" : "/dashboard", { replace: true });
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-6">
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-3 p-6 rounded-lg border border-border bg-card text-card-foreground">
        <h1 className="text-xl font-bold">Accedi</h1>
        <input className="w-full px-3 py-2 rounded-md border border-border bg-background"
               placeholder="Email" value={username} onChange={e=>setU(e.target.value)} />
        <input type="password" className="w-full px-3 py-2 rounded-md border border-border bg-background"
               placeholder="Password" value={password} onChange={e=>setP(e.target.value)} />
        <button type="submit" className="w-full px-3 py-2 rounded-md bg-primary text-primary-foreground">Entra</button>
        <div className="text-sm text-muted-foreground">{msg}</div>
        <div className="text-sm">
          Non hai un account? <Link to="/register" className="underline">Registrati</Link>
        </div>
      </form>
    </div>
  );
}
