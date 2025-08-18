/**
 * scripts/color-mapping.js
 * Mapping per tokenizzare colori legacy -> CSS variables/token.
 * - Longest-first garantito dal tuo script (ok per gradienti e dichiarazioni complete).
 * - Include varianti con/ senza spazi per rgba().
 * - Evita file sorgente dei token (tokens.css) nel run.
 */

export const mapping = {
  /* ===== NEUTRALI / BASE ===== */
  "#fff": "hsl(var(--background))",
  "#ffffff": "hsl(var(--background))",
  "#000": "hsl(var(--foreground))",
  "#333": "hsl(var(--muted-foreground))",
  "#222": "hsl(var(--foreground))",
  "#1a1a1a": "hsl(var(--foreground))",

  "rgba(0, 0, 0, 0.05)": "hsl(var(--foreground) / 0.05)",
  "rgba(0,0,0,0.05)": "hsl(var(--foreground) / 0.05)",
  "rgba(0, 0, 0, 0.08)": "hsl(var(--foreground) / 0.08)",
  "rgba(0,0,0,0.08)": "hsl(var(--foreground) / 0.08)",
  "rgba(0, 0, 0, 0.1)": "hsl(var(--foreground) / 0.10)",
  "rgba(0,0,0,0.1)": "hsl(var(--foreground) / 0.10)",
  "rgba(0, 0, 0, 0.10)": "hsl(var(--foreground) / 0.10)",
  "rgba(0, 0, 0, 0.12)": "hsl(var(--foreground) / 0.12)",
  "rgba(0, 0, 0, 0.15)": "hsl(var(--foreground) / 0.15)",
  "rgba(0,0,0,0.15)": "hsl(var(--foreground) / 0.15)",
  "rgba(0, 0, 0, 0.2)": "hsl(var(--foreground) / 0.20)",
  "rgba(0,0,0,0.2)": "hsl(var(--foreground) / 0.20)",
  "rgba(0, 0, 0, 0.20)": "hsl(var(--foreground) / 0.20)",
  "rgba(0, 0, 0, 0.25)": "hsl(var(--foreground) / 0.25)",
  "rgba(0, 0, 0, 0.30)": "hsl(var(--foreground) / 0.30)",
  "rgba(0, 0, 0, 0.40)": "hsl(var(--foreground) / 0.40)",
  "rgba(0, 0, 0, 0.70)": "hsl(var(--foreground) / 0.70)",
  "rgba(0, 0, 0, 0.80)": "hsl(var(--foreground) / 0.80)",

  "rgba(255, 255, 255, 0.05)": "hsl(var(--background) / 0.05)",
  "rgba(255, 255, 255, 0.1)": "hsl(var(--background) / 0.10)",
  "rgba(255, 255, 255, 0.125)": "hsl(var(--background) / 0.125)",
  "rgba(255, 255, 255, 0.15)": "hsl(var(--background) / 0.15)",
  "rgba(255, 255, 255, 0.2)": "hsl(var(--background) / 0.20)",
  "rgba(255, 255, 255, 0.25)": "hsl(var(--background) / 0.25)",
  "rgba(255, 255, 255, 0.3)": "hsl(var(--background) / 0.30)",
  "rgba(255, 255, 255, 0.4)": "hsl(var(--background) / 0.40)",
  "rgba(255, 255, 255, 0.5)": "hsl(var(--background) / 0.50)",
  "rgba(255, 255, 255, 0.6)": "hsl(var(--background) / 0.60)",
  "rgba(255, 255, 255, 0.7)": "hsl(var(--background) / 0.70)",
  "rgba(255, 255, 255, 0.8)": "hsl(var(--background) / 0.80)",
  "rgba(255, 255, 255, 0.9)": "hsl(var(--background) / 0.90)",

  /* ===== PALETTE BOOTSTRAP-LIKE / SEMANTIC ===== */
  // Primary (blu)
  "#007bff": "hsl(var(--primary))",
  "#0056b3": "hsl(var(--primary-700))",
  "rgba(0, 123, 255, 0.05)": "hsl(var(--primary) / 0.05)",
  "rgba(0, 123, 255, 0.1)": "hsl(var(--primary) / 0.10)",
  "rgba(0, 123, 255, 0.2)": "hsl(var(--primary) / 0.20)",
  "rgba(0, 123, 255, 0.25)": "hsl(var(--primary) / 0.25)",
  "rgba(0, 123, 255, 0.3)": "hsl(var(--primary) / 0.30)",
  "outline: 2px solid #007bff": "outline: 2px solid hsl(var(--primary))",
  "border: 2px solid #007bff": "border: 2px solid hsl(var(--primary))",

  // Success (verde)
  "#28a745": "hsl(var(--success))",
  "#1e7e34": "hsl(var(--success-700))",
  "#218838": "hsl(var(--success-600))",
  "rgba(40, 167, 69, 0.05)": "hsl(var(--success) / 0.05)",
  "rgba(40, 167, 69, 0.10)": "hsl(var(--success) / 0.10)",
  "rgba(40, 167, 69, 0.20)": "hsl(var(--success) / 0.20)",
  "rgba(40, 167, 69, 0.30)": "hsl(var(--success) / 0.30)",
  "rgba(40, 167, 69, 0.40)": "hsl(var(--success) / 0.40)",
  "rgba(40, 167, 69, 0.50)": "hsl(var(--success) / 0.50)",
  "rgba(40, 167, 69, 0.60)": "hsl(var(--success) / 0.60)",
  "rgba(40, 167, 69, 0.80)": "hsl(var(--success) / 0.80)",
  "border-left: 4px solid #28a745": "border-left: 4px solid hsl(var(--success))",

  // Danger (rosso)
  "#dc3545": "hsl(var(--danger))",
  "rgba(220, 53, 69, 0.05)": "hsl(var(--danger) / 0.05)",
  "rgba(220, 53, 69, 0.10)": "hsl(var(--danger) / 0.10)",
  "rgba(220, 53, 69, 0.15)": "hsl(var(--danger) / 0.15)",
  "rgba(220, 53, 69, 0.20)": "hsl(var(--danger) / 0.20)",
  "rgba(220, 53, 69, 0.30)": "hsl(var(--danger) / 0.30)",
  "rgba(220, 53, 69, 0.40)": "hsl(var(--danger) / 0.40)",
  "rgba(220, 53, 69, 0.60)": "hsl(var(--danger) / 0.60)",
  "border-left: 4px solid #dc3545": "border-left: 4px solid hsl(var(--danger))",

  // Warning (giallo/ambra)
  "#ffc107": "hsl(var(--warning))",
  "rgba(255, 193, 7, 0.05)": "hsl(var(--warning) / 0.05)",
  "rgba(255, 193, 7, 0.10)": "hsl(var(--warning) / 0.10)",
  "rgba(255, 193, 7, 0.20)": "hsl(var(--warning) / 0.20)",
  "rgba(255, 193, 7, 0.30)": "hsl(var(--warning) / 0.30)",
  "rgba(255, 193, 7, 0.40)": "hsl(var(--warning) / 0.40)",
  "border-left: 4px solid #ffc107": "border-left: 4px solid hsl(var(--warning))",

  // Info (ciano)
  "#17a2b8": "hsl(var(--info))",
  "rgba(23, 162, 184, 0.05)": "hsl(var(--info) / 0.05)",
  "rgba(23, 162, 184, 0.10)": "hsl(var(--info) / 0.10)",

  /* ===== BRAND LEGACY ===== */
  "#04a9f5": "hsl(var(--brand-primary))",
  "#1de9b6": "hsl(var(--brand-teal))",
  "rgba(4, 169, 245, 0.05)": "hsl(var(--brand-primary) / 0.05)",
  "rgba(4, 169, 245, 0.10)": "hsl(var(--brand-primary) / 0.10)",
  "rgba(4, 169, 245, 0.15)": "hsl(var(--brand-primary) / 0.15)",
  "rgba(4, 169, 245, 0.30)": "hsl(var(--brand-primary) / 0.30)",
  "rgba(4,169,245,0.05)": "hsl(var(--brand-primary) / 0.05)",
  "rgba(4,169,245,0.10)": "hsl(var(--brand-primary) / 0.10)",
  "rgba(4,169,245,0.15)": "hsl(var(--brand-primary) / 0.15)",
  "rgba(4,169,245,0.30)": "hsl(var(--brand-primary) / 0.30)",

  /* ===== SECONDARI / GRIGI TIPICI ===== */
  "#6c757d": "hsl(var(--secondary-foreground))",
  "#495057": "hsl(var(--muted-foreground))",
  "#e9ecef": "hsl(var(--muted))",
  "border: 1px solid #e9ecef": "border: 1px solid hsl(var(--muted))",
  "#f8f9fa": "hsl(var(--background))",
  "#e2e8f0": "hsl(var(--muted))",
  "#f1f3f4": "hsl(var(--muted))",
  "#d1d5db": "hsl(var(--muted))",
  "#dee2e6": "hsl(var(--muted))",
  "#d6d8db": "hsl(var(--muted))",
  "#adb5bd": "hsl(var(--muted-foreground))",
  "#999": "hsl(var(--muted-foreground))",
  "#666": "hsl(var(--muted-foreground))",
  "#ccc": "hsl(var(--muted))",
  "#ddd": "hsl(var(--muted))",
  "#eee": "hsl(var(--muted))",

  /* ===== ACCENTI RICORRENTI ===== */
  "#ffc107": "hsl(var(--warning))",
  "#fd7e14": "hsl(var(--warning-600))",
  "#FFA500": "hsl(var(--warning))",
  "#FFD700": "hsl(var(--accent-gold))",
  "#f59e0b": "hsl(var(--warning))",
  "#d97706": "hsl(var(--warning-700))",
  "#e53e3e": "hsl(var(--danger))",
  "#dc2626": "hsl(var(--danger))",
  "#ff6b6b": "hsl(var(--destructive))",
  "#e83e8c": "hsl(var(--pink))",
  "#6f42c1": "hsl(var(--purple))",
  "#667eea": "hsl(var(--indigo-500))",
  "#764ba2": "hsl(var(--indigo-600))",
  "#00ad5b": "hsl(var(--success-500))",
  "#008845": "hsl(var(--success-700))",

  /* ===== GRADIENTI ===== */
  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)": "var(--gradient-indigo-classic)",
  "linear-gradient(135deg, #28a745, #20c997)": "var(--gradient-success-teal)",
  "linear-gradient(135deg, #ffc107, #fd7e14)": "var(--gradient-warn-amber)",
  "linear-gradient(135deg, #11998e, #38ef7d)": "var(--gradient-accent-mint)",
  "linear-gradient(135deg, #6c63ff, #5a54d4)": "var(--gradient-accent-indigo)",
  "linear-gradient(135deg, rgba(0, 123, 255, 0.05), rgba(0, 123, 255, 0.02))":
    "linear-gradient(135deg, hsl(var(--primary) / 0.05), hsl(var(--primary) / 0.02))",
  "linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent)":
    "linear-gradient(90deg, transparent, hsl(var(--background) / 0.2), transparent)",

  /* ===== DICHIARAZIONI COMPLETE (quando presenti nel codice) ===== */
  "border-left: 4px solid #28a745": "border-left: 4px solid hsl(var(--success))",
  "border-left: 4px solid #dc3545": "border-left: 4px solid hsl(var(--danger))",
  "border-left: 4px solid #ffc107": "border-left: 4px solid hsl(var(--warning))",
  "outline: 2px solid #007bff": "outline: 2px solid hsl(var(--primary))",
  "border: 2px solid #007bff": "border: 2px solid hsl(var(--primary))",
};
