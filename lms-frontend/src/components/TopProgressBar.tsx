// src/components/TopProgressBar.tsx
import React from "react";

/**
 * Barra di progresso globale:
 * - Mostra una barra in alto quando ci sono richieste API in corso (eventi "api:loading").
 * - Debounce: compare solo dopo 120ms (evita flicker su richieste istantanee).
 * - Avanza fino al 90% mentre è attiva; quando finisce, va al 100% e scompare.
 */
export default function TopProgressBar() {
  const [active, setActive] = React.useState(0);     // conteggio richieste in corso
  const [width, setWidth] = React.useState(0);       // larghezza %
  const [visible, setVisible] = React.useState(false);
  const incTimer = React.useRef<number | null>(null);
  const showTimer = React.useRef<number | null>(null);

  // Ascolta gli eventi di caricamento emessi da api.ts (emitLoading(+1/-1))
  React.useEffect(() => {
    function onLoading(e: Event) {
      const { delta } = (e as CustomEvent<{ delta: number }>).detail || { delta: 0 };
      setActive((n) => Math.max(0, n + (Number.isFinite(delta) ? delta : 0)));
    }
    window.addEventListener("api:loading", onLoading as EventListener);
    return () => window.removeEventListener("api:loading", onLoading as EventListener);
  }, []);

  // Gestione visibilità + animazione
  React.useEffect(() => {
    // cleanup utility
    const stopInc = () => {
      if (incTimer.current) { window.clearInterval(incTimer.current); incTimer.current = null; }
    };
    const stopShowDelay = () => {
      if (showTimer.current) { window.clearTimeout(showTimer.current); showTimer.current = null; }
    };

    if (active > 0) {
      // Mostra la barra con un piccolo ritardo per evitare flash
      if (!visible && !showTimer.current) {
        showTimer.current = window.setTimeout(() => { setVisible(true); setWidth(10); }, 120);
      }
      // Avanza gradualmente verso ~90%
      if (!incTimer.current) {
        incTimer.current = window.setInterval(() => {
          setWidth((w) => (w < 90 ? Math.min(90, w + 8 + Math.random() * 10) : w));
        }, 200) as unknown as number;
      }
    } else {
      // Fine: completa al 100% e poi nascondi
      stopShowDelay();
      stopInc();
      if (visible) {
        setWidth(100);
        const t = window.setTimeout(() => { setVisible(false); setWidth(0); }, 250);
        return () => window.clearTimeout(t);
      } else {
        setWidth(0);
      }
    }

    return () => { stopShowDelay(); /* incTimer lo lasciamo attivo mentre active>0 */ };
  }, [active, visible]);

  return (
    <div className="pointer-events-none fixed left-0 right-0 top-0 z-[9999] h-0">
      <div
        className={[
          "transition-[width,opacity] duration-200 will-change-[width,opacity]",
          "h-0.5 sm:h-[2px]",                    // più visibile: 2px su schermi >= sm
          visible ? "opacity-100" : "opacity-0",
          // colore più evidente; se il tuo primary è poco contrastato, cambia in bg-blue-500
          "bg-primary",
          // leggero bagliore per separarla dallo sfondo
          "shadow-[0_0_8px_rgba(0,0,0,0.10)]",
        ].join(" ")}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}
