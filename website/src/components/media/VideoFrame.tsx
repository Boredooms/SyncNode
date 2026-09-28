import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

type AmbientVideoProps = {
  src: string;
  className?: string;
  /** Poster frame URL — shown until the first video frame decodes. */
  poster?: string;
  /** Scroll-linked slow scale (disabled on reduced motion). */
  scaleOnScroll?: boolean;
  /** Additional overlay tint. Default is a light 20% black wash. */
  overlayClassName?: string;
  /** Filter applied to the video itself, e.g. "brightness(1.08)". */
  videoFilter?: string;
  /**
   * Fade the bottom of the frame into ink-950 via a CSS mask (soft, cheap,
   * no extra paint layer) so content below transitions seamlessly.
   */
  bottomFade?: boolean;
  /**
   * Zoom-crops ~8% off each edge to hide the footage's baked-in top-left
   * watermark. Centered embedded titles remain fully visible.
   */
  cropWatermark?: boolean;
  /** Small caption chip (bottom-left) identifying the footage. */
  brand?: string;
  children?: React.ReactNode;
};

/**
 * Cinematic ambient video — muted, looping, lazily attached when scrolled
 * near. Kept visually bright: a single light wash plus a mask-based bottom
 * fade integrate it into the page without crushing the image.
 */
export function AmbientVideo({
  src,
  className,
  poster,
  scaleOnScroll = true,
  overlayClassName,
  videoFilter,
  bottomFade = false,
  cropWatermark = false,
  brand,
  children,
}: AmbientVideoProps) {
  const ref = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [attach, setAttach] = useState(false);
  const [ready, setReady] = useState(false);
  const reduced = useReducedMotion();

  // Attach the source only when the frame is near the viewport.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setAttach(true);
          io.disconnect();
        }
      },
      { rootMargin: "400px" }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  // Pause when off-screen to save bandwidth/CPU.
  useEffect(() => {
    const el = ref.current;
    const v = videoRef.current;
    if (!el || !v) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (reduced) return;
        if (entries[0].isIntersecting) v.play().catch(() => {});
        else v.pause();
      },
      { threshold: 0.15 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [attach, reduced]);

  const fadeMask = bottomFade
    ? {
        maskImage:
          "linear-gradient(to bottom, black 0%, black 72%, rgba(0,0,0,0.55) 88%, transparent 100%)",
        WebkitMaskImage:
          "linear-gradient(to bottom, black 0%, black 72%, rgba(0,0,0,0.55) 88%, transparent 100%)",
      }
    : undefined;

  return (
    <div ref={ref} className={cn("relative overflow-hidden bg-ink-950", className)}>
      {/* Poster frame — visible until the first video frame decodes */}
      {poster && (
        <img
          src={poster}
          alt=""
          aria-hidden="true"
          className={cn(
            "absolute inset-0 h-full w-full object-cover transition-opacity duration-700",
            cropWatermark && "scale-[1.18]",
            ready && "opacity-0"
          )}
        />
      )}
      {attach && (
        <video
          ref={videoRef}
          src={src}
          poster={poster}
          muted
          loop
          playsInline
          autoPlay={!reduced}
          preload="metadata"
          aria-hidden="true"
          onPlaying={() => setReady(true)}
          className={cn(
            "absolute inset-0 h-full w-full object-cover",
            cropWatermark && "scale-[1.18]",
            scaleOnScroll && !reduced && "will-change-transform"
          )}
          style={videoFilter ? { filter: videoFilter } : undefined}
        />
      )}
      <div
        aria-hidden="true"
        className={cn("absolute inset-0 bg-black/20", overlayClassName)}
        style={fadeMask}
      />
      {brand && (
        <div
          aria-hidden="true"
          className={cn(
            "absolute left-6 top-6 z-10 hidden items-center gap-2 font-mono text-micro uppercase tracking-wider2 text-white/45 md:left-10 md:top-24 md:flex",
            "animate-pulse-soft"
          )}
        >
          <span className="h-1 w-1 rounded-full bg-white/60" />
          {brand}
        </div>
      )}
      {children}
    </div>
  );
}
