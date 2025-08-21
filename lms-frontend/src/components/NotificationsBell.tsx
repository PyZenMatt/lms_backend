// src/components/NotificationsBell.tsx
import React from "react";
import { Bell } from "lucide-react";
import { getUnreadCount } from "../services/notifications";

type Props = { pollMs?: number; className?: string; onClick?: () => void };

export default function NotificationsBell({ pollMs = 60000, className = "", onClick }: Props) {
  const [count, setCount] = React.useState<number>(0);
  const [loading, setLoading] = React.useState<boolean>(false);

  async function refresh() {
    setLoading(true);
    try {
      const n = await getUnreadCount();
      setCount(n);
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, pollMs);
    // ascolta evento globale per sync immediato
    function onUpdated() { refresh(); }
    window.addEventListener("notifications:updated", onUpdated);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("notifications:updated", onUpdated);
    };
  }, [pollMs]);

  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative inline-flex h-10 w-10 items-center justify-center rounded-full border bg-card hover:bg-accent transition ${className}`}
      aria-label="Notifications"
      title={loading ? "Aggiornamento..." : "Notifiche"}
    >
      <Bell className="h-5 w-5" />
      {count > 0 && (
        <span className="absolute -top-1 -right-1 min-w-[1.25rem] rounded-full bg-red-600 px-1.5 text-xs font-medium text-white ring-2 ring-background text-center">
          {count > 99 ? "99+" : count}
        </span>
      )}
    </button>
  );
}
