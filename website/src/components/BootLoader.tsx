import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { useReducedMotion } from "@/hooks/useReducedMotion";

const SEQUENCE = [
  { label: "MODEL", value: "READY" },
  { label: "KNOWLEDGE", value: "READY" },
  { label: "EXECUTION", value: "READY" },
  { label: "VERIFICATION", value: "READY" },
];

type Props = { onComplete: () => void };

/**
 * First-visit boot sequence — a quiet system initialization.
 * Skipped entirely on repeat visits (localStorage) and reduced motion.
 */
export function BootLoader({ onComplete }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(() => {
    try {
      return !window.sessionStorage.getItem("sn_booted");
    } catch {
      return true;
    }
  });
  const reduced = useReducedMotion();

  useEffect(() => {
    if (!visible) {
      onComplete();
      return;
    }
    if (reduced) {
      // Show wordmark briefly, then release.
      const t = setTimeout(finish, 600);
      return () => clearTimeout(t);
    }

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        defaults: { ease: "power2.out" },
        onComplete: finish,
      });

      tl.fromTo(
        "[data-boot-wordmark]",
        { opacity: 0, letterSpacing: "0.6em" },
        { opacity: 1, letterSpacing: "0.42em", duration: 0.9 }
      )
        .fromTo(
          "[data-boot-line]",
          { scaleX: 0 },
          { scaleX: 1, duration: 0.7, transformOrigin: "left center" },
          "-=0.4"
        )
        .fromTo(
          "[data-boot-item]",
          { opacity: 0, y: 8 },
          { opacity: 1, y: 0, duration: 0.32, stagger: 0.28 },
          "-=0.2"
        )
        .to("[data-boot-status]", {
          opacity: 1,
          duration: 0.3,
          delay: 0.15,
        })
        .to(rootRef.current, {
          opacity: 0,
          duration: 0.6,
          delay: 0.35,
          ease: "power1.inOut",
        });
    }, rootRef);

    return () => ctx.revert();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, reduced]);

  function finish() {
    try {
      window.sessionStorage.setItem("sn_booted", "1");
    } catch {
      /* ignore */
    }
    setVisible(false);
    onComplete();
  }

  if (!visible) return null;

  return (
    <div
      ref={rootRef}
      className="fixed inset-0 z-[200] flex flex-col items-center justify-center bg-ink-950"
      role="status"
      aria-label="SyncNode initializing"
    >
      <div
        data-boot-wordmark
        className="font-sans text-2xl font-medium tracking-[0.42em] text-fg-primary"
      >
        SYNCNODE
      </div>
      <div data-boot-line className="mt-6 h-px w-40 bg-line" />

      <div className="mt-8 w-56 space-y-2">
        {SEQUENCE.map((s) => (
          <div
            key={s.label}
            data-boot-item
            className="flex items-center justify-between font-mono text-micro-sm uppercase tracking-wider2"
          >
            <span className="text-fg-dim">{s.label}</span>
            <span className="text-fg-mute">{s.value}</span>
          </div>
        ))}
      </div>

      <div
        data-boot-status
        className="mt-10 font-mono text-micro uppercase tracking-wider2 text-fg-faint opacity-0"
      >
        WORKSPACE READY
      </div>
    </div>
  );
}
