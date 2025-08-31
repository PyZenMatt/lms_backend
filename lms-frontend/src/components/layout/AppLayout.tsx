import * as React from "react";
import { useAuth } from "@/components/figma/AuthContext";
// using Figma AppSidebar as single source of truth
import { AppSidebar } from "@/components/figma/AppSidebar";
// Navbar wallet button removed to avoid duplicate connect controls.
// ConnectWalletButton is still used on Profile and Wallet pages.
import { useLocation, useNavigate } from "react-router-dom";
// using figma header primitives instead of Menubar
import { SidebarTrigger, SidebarProvider } from "@/components/figma/ui/sidebar";
import { Button } from "@/components/figma/ui/button";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/figma/ui/avatar";
import { Badge } from "@/components/figma/ui/badge";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/figma/ui/dropdown-menu";
import { Wallet as WalletIcon, User as UserIcon, Settings as SettingsIcon, LogOut } from "lucide-react";

export default function AppLayout({ children }: { children?: React.ReactNode }) {
  const [collapsed, setCollapsed] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  // removed isDesktop state and resize listener — layout now relies on CSS overrides
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileOpen(false);
    };

    if (mobileOpen) {
      // lock body scroll when mobile drawer is open
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", onKey);

      return () => {
        document.body.style.overflow = prev;
        window.removeEventListener("keydown", onKey);
      };
    }

    return () => {};
  }, [mobileOpen]);
  const { logout, user } = useAuth();
  const location = useLocation();
  const path = location?.pathname ?? "";

  const navigate = useNavigate();

  // derive the sidebar "page" token from the current pathname
  const currentPage = React.useMemo(() => {
    const p = (path || "").toLowerCase();
    if (p === "/" || p === "/dashboard") return "dashboard";
    if (p.startsWith("/courses")) return "courses";
    if (p.startsWith("/peer-review")) return "peer-review";
    if (p.startsWith("/community")) return "community";
    if (p.startsWith("/gallery")) return "gallery";
    if (p.startsWith("/discussions")) return "discussions";
    if (p.startsWith("/achievements")) return "achievements";
    if (p.startsWith("/teacher") || p.startsWith("/teacher-dashboard")) return "teacher-dashboard";
    if (p.startsWith("/students")) return "students";
    if (p.startsWith("/analytics")) return "analytics";
    if (p.startsWith("/wallet")) return "wallet";
    return "dashboard";
  }, [path]);

  // Routes where the app chrome (navbar / sidebar / header spacer) should be hidden
  const isAuthRoute =
    path === "/login" || path === "/register" || path.startsWith("/verify-email");

  // sidebar data and footer are provided by the Figma AppSidebar component

  // If we're on an auth route, render a minimal shell without the app chrome
  if (isAuthRoute) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <main className="w-full">
          <div className="container">{children}</div>
        </main>
      </div>
    );
  }
 
  return (
    <div className="min-h-screen bg-background text-foreground">
      <SidebarProvider
        open={!collapsed}
        onOpenChange={(open) => setCollapsed(!open)}
      >
          <AppSidebar
            currentPage={currentPage}
            onPageChange={(page) => {
              // map sidebar page tokens to app routes
              const pageToPath = (p: string) => {
                switch (p) {
                  // app index and most dashboards point to courses listing by default
                  case "dashboard":
                    return "/dashboard";
                  case "courses":
                    return "/courses";
                  // peer-review in the app is routed to assigned reviews
                  case "peer-review":
                    return "/reviews/assigned";
                  case "community":
                    return "/community";
                  case "gallery":
                    return "/gallery";
                  case "discussions":
                    return "/discussions";
                  case "achievements":
                    return "/achievements";
                  // teacher dashboard maps to teacher home
                  case "teacher-dashboard":
                    return "/teacher";
                  case "students":
                    return "/students";
                  case "analytics":
                    return "/analytics";
                  case "wallet":
                    return "/wallet";
                  case "profile":
                    return "/profile";
                  default:
                    return "/courses";
                }
              };

              const to = pageToPath(page);
              if (to) {
                navigate(to);
              }

              // if we had a mobile drawer open, close it after navigation
              setMobileOpen(false);
            }}
          />
          <div className="flex-1 flex flex-col min-h-0">
          {/* Header: use Figma Menubar styling 1:1 (minimal content, no subcomponents) */}
          <header className="sticky top-0 z-40 border-b border-border bg-card/60 backdrop-blur w-full">
            <div className="flex h-14 items-center px-4 lg:px-6">
              <SidebarTrigger className="mr-4" />
              <div className="flex-1" />
              <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    /* navigate to wallet page */
                    navigate("/wallet");
                  }}
                  className="flex items-center gap-2"
                >
                  <WalletIcon className="size-4" />
                  <Badge variant="secondary" className="bg-purple-100 text-purple-800">
                    {(user?.tokens ?? 0) + " ✨"}
                  </Badge>
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={undefined} alt={undefined} />
                        <AvatarFallback>U</AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                    <DropdownMenuContent className="w-56" align="end" forceMount>
                    <DropdownMenuLabel className="font-normal">
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">{user?.name ?? "User"}</p>
                        <p className="text-xs leading-none text-muted-foreground">{user?.email ?? ""}</p>
                        <Badge variant="outline" className="w-fit mt-1 capitalize">
                          {user?.role ?? "role"}
                        </Badge>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => navigate("/wallet")}> 
                      <WalletIcon className="mr-2 h-4 w-4" />
                      <span>Wallet</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/profile")}>
                      <UserIcon className="mr-2 h-4 w-4" />
                      <span>Profile</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate("/settings")}>
                      <SettingsIcon className="mr-2 h-4 w-4" />
                      <span>Settings</span>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => { if (typeof logout === 'function') { logout(); navigate('/login'); } else navigate('/login'); }}>
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>Log out</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </header>

          <main className="flex-1 py-6 overflow-auto">
            <div className="container app-container">{children}</div>
          </main>
        </div>
      </SidebarProvider>
    <footer className="border-t border-border bg-card/40 w-full">
        <div className="container h-12 flex items-center">{/* footer */}</div>
      </footer>
    </div>
  );
}

