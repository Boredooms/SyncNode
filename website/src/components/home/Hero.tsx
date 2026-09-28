import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { Download, Github } from "lucide-react";
import { AmbientVideo } from "@/components/media/VideoFrame";
import { MagneticButton } from "@/components/MagneticButton";
import { videoCatalog, GITHUB_URL } from "@/data/videos";
import { useReducedMotion } from "@/hooks/useReducedMotion";

/** Signature ease — fast start, long settle. */
const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];

function isFirstVisit(): boolean {
  try {
    return !window.sessionStorage.getItem("sn_booted");
  } catch {
    return false;
  }
}

/**
 * HOME HERO — nothing but the film and two buttons.
 *
 * The intro video IS the title card: "SyncNode — Think Locally, Act
 * Intelligently" is baked into the footage, so the page adds no words of its
 * own. The entrance is a cinematic resolve (blur + slow zoom settle), the
 * exit is a scroll-scrubbed parallax, and the only UI is the CTA pair.
 */
export function Hero() {
  const ref = useRef<HTMLElement>(null);
  const reduced = useReducedMotion();
  const hero = videoCatalog.hero;
  const t0 = !reduced && isFirstVisit() ? 2.5 : 0.15;

  // Scroll-scrubbed exit choreography.
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const videoY = useTransform(scrollYProgress, [0, 1], ["0%", "12%"]);
  const videoScale = useTransform(scrollYProgress, [0, 1], [1, 1.08]);
  const exitDim = useTransform(scrollYProgress, [0, 1], [0, 0.45]);
  const ctaOpacity = useTransform(scrollYProgress, [0, 0.22], [1, 0]);
  const ctaY = useTransform(scrollYProgress, [0, 0.22], [0, 26]);

  return (
    <section
      ref={ref}
      className="relative h-[100svh] min-h-[640px] overflow-hidden bg-ink-950"
      aria-label="SyncNode — Think Locally, Act Intelligently"
    >
      {/* The film — cinematic resolve on load, parallax on exit */}
      <motion.div
        className="absolute inset-0"
        initial={reduced ? false : { opacity: 0, filter: "blur(18px)", scale: 1.05 }}
        animate={{ opacity: 1, filter: "blur(0px)", scale: 1 }}
        transition={{ duration: 1.6, ease: EASE, delay: t0 * 0.55 }}
        style={reduced ? undefined : { y: videoY, scale: videoScale }}
      >
        <AmbientVideo
          src={hero.src}
          poster={hero.poster}
          className="h-full w-full"
          overlayClassName="bg-black/10"
        />
      </motion.div>

      {/* Exit dim — transparent at rest, deepens as the card leaves */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-ink-950 opacity-0"
        style={reduced ? undefined : { opacity: exitDim }}
      />

      {/* Whisper of bottom scrim — keeps the buttons legible over the fog */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 bottom-0 h-44 bg-gradient-to-t from-ink-950/85 via-ink-950/30 to-transparent"
      />

      {/* Hidden heading for document outline / SEO — the film carries the visible title */}
      <h1 className="sr-only">
        SyncNode — a sovereign AI workbench for confidential work
      </h1>

      {/* The only UI: two buttons, centered at the base of the frame */}
      <motion.div
        className="absolute inset-x-0 bottom-0 z-10"
        style={
          reduced
            ? undefined
            : { opacity: ctaOpacity, y: ctaY }
        }
      >
        <div className="container-page flex justify-center pb-10 pt-6">
          <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
            <motion.div
              initial={reduced ? false : { opacity: 0, y: 26 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, ease: EASE, delay: t0 + 0.9 }}
            >
              <MagneticButton
                to="/download"
                variant="primary"
                size="lg"
                className="shadow-[0_10px_40px_rgba(0,0,0,0.45)]"
              >
                <Download className="h-4 w-4" />
                DOWNLOAD FOR WINDOWS
              </MagneticButton>
            </motion.div>
            <motion.div
              initial={reduced ? false : { opacity: 0, y: 26 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, ease: EASE, delay: t0 + 1.05 }}
            >
              <MagneticButton
                href={GITHUB_URL}
                external
                variant="secondary"
                size="lg"
                className="border-white/25 bg-ink-950/35 backdrop-blur-sm hover:border-white/45 hover:bg-ink-950/60"
              >
                <Github className="h-4 w-4" />
                GITHUB
              </MagneticButton>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
