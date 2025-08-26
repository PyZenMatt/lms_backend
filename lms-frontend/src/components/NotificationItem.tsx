// src/components/NotificationItem.tsx
// React import not required with new JSX transform
import { Badge } from "./ui/badge";

// Local notification type (types/notification does not export NotificationItem)
type N = {
  id: number | string;
  title?: string | null;
  message?: string | null;
  is_read?: boolean;
  created_at?: string | null;
};

type Props = {
  item: N;
  onMarkRead?: (id: N["id"]) => void;
};

export default function NotificationItem({ item, onMarkRead }: Props) {
  const isRead = !!item.is_read;
  const created = item.created_at ? new Date(item.created_at) : null;

  return (
    <div className="flex items-start gap-3 rounded-md border p-4">
      <div className="mt-1">
        <Badge variant={isRead ? "muted" : "default"} className="h-2 w-2 p-0" />
      </div>
      <div className="flex-1">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-medium">{item.title}</h3>
          {created && (
            <time className="text-xs text-muted-foreground" dateTime={created.toISOString()}>
              {created.toLocaleString()}
            </time>
          )}
        </div>
        {item.message && <p className="mt-1 text-sm text-muted-foreground">{item.message}</p>}
        {!isRead && onMarkRead && (
          <div className="mt-3">
            <button
              onClick={() => onMarkRead(item.id)}
              className="inline-flex h-8 items-center rounded-md border px-2 text-xs hover:bg-accent"
            >
              Segna come letta
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
