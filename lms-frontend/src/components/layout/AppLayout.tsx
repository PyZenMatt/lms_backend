// src/components/layout/AppLayout.tsx
import React from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import NotificationsBell from "../NotificationsBell";
import ThemeToggle from "../ThemeToggle";

function cls(...xs: Array<string | false | undefined | null>) {
  return xs.filter(Boolean).join(" ");
}

export default function AppLayout() {
  const { isAuthenticated, role, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = React.useState(false);

  async function onLogout() {
    await logout();
    navigate("/", { replace: true });
  }

  // ✅ Admin → /admin, Teacher → /teacher, altri → /dashboard
  const dashHref = role === "admin" ? "/admin" : role === "teacher" ? "/teacher" : "/dashboard";

  const NavLinkItem = ({
    to,
    children,
    end,
  }: {
    to: string;
    children: React.ReactNode;
    end?: boolean;
  }) => (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cls(
          "px-3 py-2 rounded-md text-sm font-medium transition-colors",
          isActive ? "bg-accent text-foreground" : "text-muted-foreground hover:text-foreground"
        )
      }
      onClick={() => setOpen(false)}
    >
      {children}
    </NavLink>
  );

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top Nav */}
      <header className="sticky top-0 z-40 border-b bg-card/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-2">
          {/* Brand + mobile menu button */}
          <div className="flex items-center gap-3">
            <button
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border md:hidden"
              onClick={() => setOpen((v) => !v)}
              aria-label="Toggle menu"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <Link to="/" className="flex items-center gap-2">
              <div className="h-8 w-8 rounded bg-primary/20" />
              <span className="text-base font-semibold">LMS</span>
            </Link>

            {/* Desktop links */}
            <nav className="ml-4 hidden items-center gap-1 md:flex">
              <NavLinkItem to="/courses">Corsi</NavLinkItem>
              {isAuthenticated && <NavLinkItem to={dashHref}>Dashboard</NavLinkItem>}
            </nav>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-2">
            <ThemeToggle />
            {isAuthenticated ? (
              <>
                <Link
                  to="/notifications"
                  className="hidden md:inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
                  onClick={() => setOpen(false)}
                >
                  <NotificationsBell />
                  <span className="sr-only md:not-sr-only">Notifiche</span>
                </Link>
                <NavLinkItem to="/profile">Profilo</NavLinkItem>
                <button
                  onClick={onLogout}
                  className="inline-flex h-9 items-center rounded-md bg-primary px-3 text-sm text-primary-foreground hover:opacity-90"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <NavLinkItem to="/login">Login</NavLinkItem>
                <NavLinkItem to="/register">Registrati</NavLinkItem>
              </>
            )}
          </div>
        </div>

        {/* Mobile menu */}
        {open && (
          <div className="border-t md:hidden">
            <div className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-2">
              <NavLinkItem to="/courses" end>
                Corsi
              </NavLinkItem>
              {isAuthenticated && <NavLinkItem to={dashHref}>Dashboard</NavLinkItem>}
              {isAuthenticated ? (
                <>
                  <Link
                    to="/notifications"
                    className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
                    onClick={() => setOpen(false)}
                  >
                    Notifiche
                  </Link>
                  <NavLinkItem to="/profile">Profilo</NavLinkItem>
                  <button
                    onClick={onLogout}
                    className="mt-1 inline-flex h-9 items-center rounded-md bg-primary px-3 text-sm text-primary-foreground hover:opacity-90"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <NavLinkItem to="/login">Login</NavLinkItem>
                  <NavLinkItem to="/register">Registrati</NavLinkItem>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Page content */}
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t py-6 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} LMS – All rights reserved.
      </footer>
    </div>
  );
}
