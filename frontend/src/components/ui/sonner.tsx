"use client";

import { Toaster, type ToasterProps } from "sonner";

export function Sonner(props: ToasterProps) {
  // opzionale: adattare theme chiaro/scuro via CSS vars globali
  return <Toaster richColors {...props} />;
}

export { Toaster };
