import { useEffect } from "react";

// Hook: lock body scroll when `enabled` is true.
// Handles desktop (overflow hidden + scrollbar gap) and mobile iOS (position fixed fallback).
export function useScrollLock(enabled: boolean) {
  useEffect(() => {
    if (typeof window === "undefined" || typeof document === "undefined") return;

    const doc = document.documentElement;
    const body = document.body;

    if (!enabled) return;

    // Save previous values
    const prevOverflow = body.style.overflow;
    const prevPaddingRight = body.style.paddingRight;
    const prevPosition = body.style.position;
    const prevTop = body.style.top;

    const scrollY = window.scrollY || window.pageYOffset;

    // On iOS Safari, overflow hidden doesn't prevent scroll; use position fixed hack
    const isIOS = /iP(ad|hone|od)/.test(navigator.userAgent);

    if (isIOS) {
      body.style.position = "fixed";
      body.style.top = `-${scrollY}px`;
    } else {
      // reserve scrollbar gap to avoid layout shift
      const scrollbarGap = window.innerWidth - doc.clientWidth;
      if (scrollbarGap > 0) body.style.paddingRight = `${scrollbarGap}px`;
      body.style.overflow = "hidden";
    }

    return () => {
      // restore
      body.style.overflow = prevOverflow;
      body.style.paddingRight = prevPaddingRight;
      body.style.position = prevPosition;
      body.style.top = prevTop;

      if (isIOS) {
        // restore scroll position
        window.scrollTo(0, scrollY);
      }
    };
  }, [enabled]);
}
