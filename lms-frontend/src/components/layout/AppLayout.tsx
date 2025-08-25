import * as React from "react";
import { Sidebar, type SidebarItem } from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import ThemeToggle from "@/components/ThemeToggle";
import NotificationsBell from "@/components/NotificationsBell";
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
    <div className="flex min-h-screen bg-background text-foreground">
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

      <div className="flex w-full flex-col">
        {/* Topbar with toggles */}
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background/90 px-3 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="flex items-center gap-2">
            <button
              className="inline-flex items-center justify-center rounded-md border px-2 py-1 text-sm md:hidden"
              onClick={() => setCollapsed((v) => !v)}
            >
              Menu
            </button>
            <span className="text-sm text-muted-foreground">SchoolPlatform</span>
          </div>
          <div className="flex items-center gap-2">
            <NotificationsBell />
            <ThemeToggle />
          </div>
        </header>

        <main className={cn("mx-auto w-full max-w-[1200px] p-3 md:p-6")}>
          {children}
        </main>
      </div>
    </div>
  );
}

