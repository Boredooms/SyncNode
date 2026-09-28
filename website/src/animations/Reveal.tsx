import { useEffect, useRef, type ReactNode, type ElementType } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/hooks/useReducedMotion";

gsap.registerPlugin(ScrollTrigger);

type Direction = "rise" | "fall" | "left" | "right" | "none";

type RevealProps = {
  children: ReactNode;
  className?: string;
  /** Starting offset in px */
  y?: number;
  direction?: Direction;
  delay?: number;
  duration?: number;
  stagger?: number;
  as?: ElementType;
  start?: string;
  once?: boolean;
};

/**
 * Scroll-entrance wrapper. Animates children in when the element enters the viewport.
 * Honors prefers-reduced-motion by rendering children immediately.
 */
export function Reveal({
  children,
  className,
  y = 40,
  direction = "rise",
  delay = 0,
  duration = 1.0,
  stagger = 0,
  as: Tag = "div",
  start = "top 85%",
  once = true,
}: RevealProps) {
  const ref = useRef<HTMLElement | null>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el || reduced) return;

    const from: gsap.TweenVars = { opacity: 0 };
    if (direction === "rise") from.y = y;
    if (direction === "fall") from.y = -y;
    if (direction === "left") from.x = -y;
    if (direction === "right") from.x = y;

    const targets = stagger > 0 ? el.children : [el];
    gsap.set(targets, { ...from, scale: direction === "none" ? 1 : 0.985 });

    const ctx = gsap.context(() => {
      gsap.to(targets, {
        opacity: 1,
        x: 0,
        y: 0,
        scale: 1,
        duration,
        delay,
        stagger,
        ease: "power3.out",
        scrollTrigger: {
          trigger: el,
          start,
          once,
        },
      });
    }, el);

    return () => ctx.revert();
  }, [reduced, direction, y, delay, duration, stagger, start, once]);

  return (
    <Tag ref={ref} className={className}>
      {children}
    </Tag>
  );
}

/** Fades an element in with a slight upward drift — the quiet default. */
export function FadeIn({
  children,
  className,
  delay = 0,
  y = 24,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  y?: number;
}) {
  return (
    <Reveal className={cn(className)} direction="rise" y={y} delay={delay}>
      {children}
    </Reveal>
  );
}
