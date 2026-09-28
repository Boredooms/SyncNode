import { useRef, type ReactNode, type MouseEvent } from "react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/hooks/useReducedMotion";

type Props = {
  children: ReactNode;
  to?: string;
  href?: string;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost";
  size?: "md" | "lg";
  className?: string;
  external?: boolean;
  ariaLabel?: string;
};

/** Button / link with subtle magnetic pull (max ~10px). */
export function MagneticButton({
  children,
  to,
  href,
  onClick,
  variant = "primary",
  size = "md",
  className,
  external,
  ariaLabel,
}: Props) {
  const ref = useRef<HTMLAnchorElement & HTMLButtonElement>(null);
  const reduced = useReducedMotion();

  const handleMove = (e: MouseEvent) => {
    if (reduced || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = e.clientX - (rect.left + rect.width / 2);
    const y = e.clientY - (rect.top + rect.height / 2);
    const dx = Math.max(-10, Math.min(10, x * 0.18));
    const dy = Math.max(-10, Math.min(10, y * 0.28));
    ref.current.style.transform = `translate(${dx}px, ${dy}px)`;
  };

  const handleLeave = () => {
    if (!ref.current) return;
    ref.current.style.transform = "translate(0px, 0px)";
  };

  const cls = cn(
    variant === "primary" && "btn-primary",
    variant === "secondary" && "btn-secondary",
    variant === "ghost" && "btn-ghost",
    size === "lg" ? "btn-lg" : "btn-md",
    "transition-transform duration-300 ease-out will-change-transform",
    className
  );

  if (to) {
    return (
      <Link
        ref={ref as never}
        to={to}
        className={cls}
        aria-label={ariaLabel}
        onMouseMove={handleMove}
        onMouseLeave={handleLeave}
      >
        {children}
      </Link>
    );
  }

  if (href) {
    return (
      <a
        ref={ref as never}
        href={href}
        target={external ? "_blank" : undefined}
        rel={external ? "noreferrer noopener" : undefined}
        className={cls}
        aria-label={ariaLabel}
        onMouseMove={handleMove}
        onMouseLeave={handleLeave}
      >
        {children}
      </a>
    );
  }

  return (
    <button
      ref={ref as never}
      onClick={onClick}
      className={cls}
      aria-label={ariaLabel}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
    >
      {children}
    </button>
  );
}
