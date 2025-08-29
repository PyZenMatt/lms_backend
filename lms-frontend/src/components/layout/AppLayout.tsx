import * as React from "react";
import { Sidebar, type SidebarItem } from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import ThemeToggle from "@/components/ThemeToggle";
import NotificationsBell from "@/components/NotificationsBell";
import TeacherDecisionNav from "@/components/teo/TeacherDecisionNav";
// Navbar wallet button removed to avoid duplicate connect controls.
// ConnectWalletButton is still used on Profile and Wallet pages.
import { useAuth } from "@/context/AuthContext";

export default function AppLayout({
  items,
  footer,
  children,
}: {
  items?: SidebarItem[];
  footer?: React.ReactNode;
  children?: React.ReactNode;
}) {
  const [collapsed, setCollapsed] = React.useState(false);
  const { isAuthenticated, role, logout } = useAuth();

  // Default items if none provided — includes icons and role-based links
  const defaultItems: SidebarItem[] = [];

  // Common top items — role-aware dashboard and menus
  if (role === "teacher" || role === "admin") {
    // teacher/admin: dashboard goes to /teacher, studio goes to course creation
    defaultItems.push({ to: "/teacher", label: "🏠 Dashboard", end: true });
    defaultItems.push({ to: "/studio/courses/new", label: "🏫 Studio Docente" });
    defaultItems.push({ to: "/courses", label: "📚 Corsi" });
    defaultItems.push({ to: "/wallet", label: "👛 Wallet" });
    // Restore TEO Inbox and Staking in the sidebar for teachers
  // TEO Inbox page removed; decisions are handled via notifications

  defaultItems.push({ to: "/teacher/staking", label: <>💎 Staking</> });
  defaultItems.push({ to: "/teacher/pending-discounts", label: "Pending Discounts" });
  // Teacher choices page removed; use the topbar inbox (TeacherDecisionNav) instead
  // TEO Inbox and Staking are surfaced on the Teacher Dashboard only.
    // teachers don't need 'I miei esercizi' in the sidebar; they manage exercises via Studio
  } else {
    // student / anonymous sidebar — learning-focused
    defaultItems.push({ to: "/dashboard", label: "🏠 Dashboard", end: true });
    defaultItems.push({ to: "/courses", label: "🔎 Esplora Corsi" });
    defaultItems.push({ to: "/my/courses", label: "📘 I miei corsi" });
    defaultItems.push({ to: "/wallet", label: "👛 Wallet" });
    defaultItems.push({ to: "/my/exercises", label: "📝 I miei esercizi" });
  }

  // Auth-only items
  if (isAuthenticated) {
    // link to assigned reviews list by default
    defaultItems.push({ to: "/reviews/assigned", label: "🔎 Revisioni" });
  }

  // Admin-only
  if (role === "admin") {
    defaultItems.push({ to: "/admin", label: "⚙️ Admin" });
  }

  defaultItems.push({ to: "/notifications", label: "🔔 Notifiche" });

  const sidebarItems = items && items.length > 0 ? items : defaultItems;

  // Add Login/Register or Logout action at the end
  const trailingItems: SidebarItem[] = [];
  if (isAuthenticated) {
    trailingItems.push({ label: "⇦ Logout", icon: "⏏️", onClick: () => logout() });
  } else {
    trailingItems.push({ to: "/login", label: "🔐 Login" });
    trailingItems.push({ to: "/register", label: "✍️ Registrati" });
  }

  const finalItems = [...sidebarItems, ...trailingItems];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card/50 backdrop-blur">
        <div className="container flex h-14 items-center gap-4">{/* nav */}</div>
      </header>
      <div className="flex">
        <aside className="w-64 border-r border-border bg-card/40">
          <Sidebar
            items={finalItems}
            footer={
              footer ?? (
                <div className="flex items-center justify-between gap-2">
                  <ThemeToggle />
                  <div className="text-xs text-muted-foreground">v1.0 • beta</div>
                </div>
              )
            }
            collapsed={collapsed}
            onToggle={setCollapsed}
          />
        </aside>
        <main className="flex-1 py-6">
          <div className="container">
            {/* Topbar with toggles */}
            <div className="h-14 flex items-center px-4 border-b border-border shadow-sm bg-card/60 backdrop-blur">
              <div className="flex items-center gap-2">
                <button
                  className="inline-flex items-center justify-center rounded-md border border-border px-2 py-1 text-sm md:hidden focus-visible:outline-none focus-visible:shadow-focus"
                  onClick={() => setCollapsed((v) => !v)}
                >
                  Menu
                </button>
                <span className="text-sm text-muted-foreground">SchoolPlatform</span>
              </div>
              <div className="flex items-center gap-2">
                <NotificationsBell />
                <TeacherDecisionNav />
                <ThemeToggle />
                {/* Wallet connect button removed from navbar to avoid duplicates; use Wallet page button */}
              </div>
            </div>
            <div className="py-6">
              <div className="container">
                {children}
              </div>
            </div>
          </div>
        </main>
      </div>
      <footer className="border-t border-border bg-card/40">
        <div className="container h-12 flex items-center">{/* footer */}</div>
      </footer>
    </div>
  );
}

