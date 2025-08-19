// src/reportWebVitals.tsx
type ReportHandler = (metric: unknown) => void;

export default function reportWebVitals(onPerfEntry?: ReportHandler) {
  if (typeof onPerfEntry !== "function") return;

  import("web-vitals")
    .then((mod: any) => {
      // web-vitals v3+/v4 usa on*, le versioni precedenti usano get*
      const onCLS  = mod.onCLS  ?? mod.getCLS;
      const onFID  = mod.onFID  ?? mod.getFID;
      const onFCP  = mod.onFCP  ?? mod.getFCP;
      const onLCP  = mod.onLCP  ?? mod.getLCP;
      const onTTFB = mod.onTTFB ?? mod.getTTFB;

      onCLS?.(onPerfEntry);
      onFID?.(onPerfEntry);
      onFCP?.(onPerfEntry);
      onLCP?.(onPerfEntry);
      onTTFB?.(onPerfEntry);
    })
    .catch(() => {
      /* no-op: non bloccare l'app se web-vitals fallisce */
    });
}
