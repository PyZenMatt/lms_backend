import { useEffect } from "react";

export default function Styleguide() {
  useEffect(() => {
    const html = document.documentElement;
    html.setAttribute("data-theme", "v2");
    return () => html.removeAttribute("data-theme");
  }, []);

  return (
    <div className="p-6 space-y-4">
      <div className="bg-background text-foreground border border-border rounded-lg p-4">
        Card (usa token V2)
      </div>
      <button className="bg-primary text-primary-foreground px-4 py-2 rounded-md">
        Primary (V2)
      </button>
      <div
        style={{
          background: "hsl(var(--background))",
          color: "hsl(var(--foreground))",
          border: "1px solid hsl(var(--border))",
          padding: 16, borderRadius: 12,
        }}
      >
        Litmus: legge direttamente le var del tema
      </div>
    </div>
  );
}
