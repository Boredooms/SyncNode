import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/hooks/useReducedMotion";

gsap.registerPlugin(ScrollTrigger);

type Mode = "fall" | "rise" | "blur" | "track";

type SplitTextProps = {
  children: string;
  className?: string;
  mode?: Mode;
  /** split by "words" | "chars" */
  by?: "words" | "chars";
  stagger?: number;
  delay?: number;
  start?: string;
  as?: "h1" | "h2" | "h3" | "p" | "span" | "div";
};

const DISPLAY: Record<SplitTextProps["as"], string> = {
  h1: "block",
  h2: "block",
  h3: "block",
  p: "block",
  div: "block",
  span: "inline",
};

/**
 * Splits text into words (or chars) and animates them in on scroll.
 *
 * Every word sits inside its own overflow-hidden mask, so words *emerge*
 * through a hard edge — the crisp editorial reveal motion.dev uses — rather
 * than floating in over surrounding content.
 *
 * The mask carries a small padding-bottom (compensated by a negative margin)
 * so descenders (p, y, g) are never clipped by the mask edge, while layout
 * line spacing stays tight.
 *
 * The root element keeps its natural display (block for headings, inline for
 * spans), so margins like `mb-16` on section headings actually apply — this
 * previously rendered as `inline`, silently dropping the gap below headings
 * and letting cards overlap the text.
 */
export function SplitText({
  children,
  className,
  mode = "rise",
  by = "words",
  stagger = 0.045,
  delay = 0,
  start = "top 85%",
  as: Tag = "span",
}: SplitTextProps) {
  const ref = useRef<HTMLElement | null>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el || reduced) return;

    const parts = Array.from(el.querySelectorAll<HTMLElement>("[data-part]"));

    const ctx = gsap.context(() => {
      switch (mode) {
        case "fall":
          gsap.set(parts, { yPercent: -130, opacity: 0 });
          break;
        case "rise":
          gsap.set(parts, { yPercent: 130, opacity: 0 });
          break;
        case "blur":
          gsap.set(parts, { opacity: 0, filter: "blur(14px)", y: 18 });
          break;
        case "track":
          gsap.set(parts, { opacity: 0, letterSpacing: "0.35em" });
          break;
      }

      gsap.to(parts, {
        yPercent: 0,
        y: 0,
        opacity: 1,
        filter: "blur(0px)",
        letterSpacing: mode === "track" ? "0.14em" : "0em",
        duration: mode === "track" ? 1.1 : 0.9,
        ease: mode === "fall" ? "power4.out" : "power3.out",
        stagger,
        delay,
        scrollTrigger: { trigger: el, start, once: true },
      });
    }, el);

    return () => ctx.revert();
  }, [mode, by, stagger, delay, start, reduced]);

  const words = children.split(" ");

  return (
    <Tag
      ref={ref as never}
      className={cn(DISPLAY[Tag], className)}
      aria-label={children}
    >
      {words.map((word, wi) => (
        <span
          key={wi}
          aria-hidden="true"
          className="inline-block overflow-hidden pb-[0.12em] -mb-[0.12em] align-bottom"
          style={{ whiteSpace: "pre-wrap" }}
        >
          {by === "chars" ? (
            <>
              {Array.from(word).map((ch, ci) => (
                <span
                  key={ci}
                  data-part
                  className="inline-block will-change-transform"
                >
                  {ch}
                </span>
              ))}
            </>
          ) : (
            <span data-part className="inline-block will-change-transform">
              {word}
            </span>
          )}
          {wi < words.length - 1 ? " " : ""}
        </span>
      ))}
    </Tag>
  );
}

/**
 * ChromaText — restrained monochrome luminosity shift: text brightens from
 * dim grey to full white as it crosses the viewport. Grayscale only.
 */
export function ChromaText({
  children,
  className,
  as: Tag = "span",
}: {
  children: string;
  className?: string;
  as?: "span" | "div" | "p";
}) {
  const ref = useRef<HTMLElement | null>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el || reduced) return;

    const parts = Array.from(el.querySelectorAll<HTMLElement>("[data-part]"));

    const ctx = gsap.context(() => {
      gsap.fromTo(
        parts,
        { color: "#3a3a3a" },
        {
          color: "#F2F2F2",
          ease: "none",
          stagger: 0.06,
          scrollTrigger: {
            trigger: el,
            start: "top 80%",
            end: "top 30%",
            scrub: true,
          },
        }
      );
    }, el);

    return () => ctx.revert();
  }, [reduced]);

  const words = children.split(" ");

  return (
    <Tag ref={ref as never} className={cn("inline", className)} aria-label={children}>
      {words.map((w, i) => (
        <span key={i} aria-hidden="true" style={{ whiteSpace: "pre-wrap" }}>
          <span data-part>{w}</span>
          {i < words.length - 1 ? " " : ""}
        </span>
      ))}
    </Tag>
  );
}
