import React from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { getRoleFromToken } from "@/lib/auth";
import { Button, Input, Label, Card, CardHeader, CardContent } from "@/components/ds";

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const location = useLocation() as ReturnType<() => { state?: { from?: { pathname?: string } } }>;
  const from: string | undefined = location?.state?.from?.pathname;

  const [ident, setIdent] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [msg, setMsg] = React.useState("");
  const identRef = React.useRef<HTMLInputElement | null>(null);

  React.useEffect(() => {
    // Autofocus the first field for keyboard users on mount
    identRef.current?.focus();
  }, []);

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
  const role = getRoleFromToken();
    if (role === "admin")      { nav("/admin", { replace: true }); return; }
    if (role === "teacher")    { nav("/teacher", { replace: true }); return; }
    /* student/default */        nav("/dashboard", { replace: true });
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="container">
        <Card className="mx-auto max-w-md">
            <CardHeader>
              <h1 className="text-xl font-semibold">Accedi</h1>
              <p className="text-sm text-muted-foreground mt-1">Usa le tue credenziali per proseguire</p>
            </CardHeader>
            <CardContent>
              <form onSubmit={onSubmit} className="mt-2 grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="ident">Email o Username</Label>
                  <Input ref={identRef} id="ident" type="text" autoComplete="username" value={ident} onChange={e=>setIdent(e.target.value)} />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="password">Password</Label>
                  <Input id="password" type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} />
                </div>
                <Button type="submit" className="mt-2 w-full">Entra</Button>
                <div className="text-sm text-muted-foreground">{msg}</div>
                <div className="text-sm">
                  Non hai un account? <Link to="/register" className="underline">Registrati</Link>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    );
}
