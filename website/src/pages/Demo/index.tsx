import { Reveal } from "@/animations/Reveal";
import { ChromaText } from "@/animations/SplitText";
import { Section, SectionLabel } from "@/components/Section";
import { ProductVideo } from "@/components/media/ProductVideo";
import { AmbientVideo } from "@/components/media/VideoFrame";
import { videoCatalog } from "@/data/videos";

const STORY = [
  { label: "THE TASK", note: "A goal, stated in one sentence." },
  { label: "THE PLAN", note: "Decomposed into a visible graph of steps." },
  { label: "THE AGENTS", note: "Specialists dispatched where they fit." },
  { label: "THE ACTION", note: "Typed tools execute on the real desktop." },
  { label: "THE OBSERVATION", note: "Evidence captured from actual state." },
  { label: "THE VERIFICATION", note: "Assertions confirm what happened." },
  { label: "THE RESULT", note: "Artifacts delivered, approval recorded." },
];

/**
 * VIDEO PLACEMENT (verified by frame analysis):
 * 1. TOP OF PAGE — "Prototype.mp4": "Walkthrough the Prototype" is baked in.
 *    Full-bleed at the very top with NO overlaid page text.
 * 2. INLINE — "Prototype2.0.mp4": clean title-free cut presented in a
 *    DeviceFrame with proper player controls, no duplicate wording.
 */
export default function Demo() {
  return (
    <>
      {/* ===== HERO = THE TITLED WALKTHROUGH VIDEO, FULL-BLEED, NO OVERLAY ===== */}
      <section className="relative">
        <AmbientVideo
          src={videoCatalog.prototypeTitled.src}
          poster={videoCatalog.prototypeTitled.poster}
          className="h-[92svh] min-h-[560px] w-full"
          scaleOnScroll={false}
          overlayClassName="bg-black/15"
          videoFilter="brightness(1.05)"
          cropWatermark
        />
        <div className="pointer-events-none absolute inset-x-0 bottom-8 z-10 flex justify-center">
          <div className="h-10 w-px overflow-hidden bg-line">
            <div className="h-1/2 w-full animate-pulse-soft bg-fg-mute" />
          </div>
        </div>
      </section>

      {/* Storyline */}
      <Section className="border-t border-line bg-ink-950">
        <div className="container-page">
          <SectionLabel>WHAT YOU JUST WATCHED</SectionLabel>
          <h2 className="max-w-3xl text-[clamp(1.8rem,3.8vw,3rem)] font-extralight leading-[1.2] tracking-tight text-fg-primary">
            <ChromaText>
              One goal. One plan. One verified result.
            </ChromaText>
          </h2>

          <div className="mt-14 space-y-px overflow-hidden rounded-lg border border-line bg-line">
            {STORY.map((s, i) => (
              <Reveal key={s.label} y={16} delay={i * 0.04}>
                <div className="flex flex-col gap-1.5 bg-ink-900 px-6 py-6 sm:flex-row sm:items-center sm:gap-10 md:px-10">
                  <span className="w-8 shrink-0 font-mono text-micro text-fg-faint">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="w-48 shrink-0 font-mono text-micro-sm uppercase tracking-wider2 text-fg-primary">
                    {s.label}
                  </span>
                  <span className="text-[14px] text-fg-mute">{s.note}</span>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </Section>

      {/* Clean cut with real controls */}
      <Section className="border-t border-line bg-ink-900/40">
        <div className="container-page">
          <div className="grid items-center gap-10 lg:grid-cols-[1fr_1.2fr]">
            <Reveal y={24}>
              <SectionLabel>ALTERNATE CUT</SectionLabel>
              <h2 className="text-3xl font-light leading-tight tracking-tight text-fg-primary md:text-4xl">
                The same walkthrough, quiet cut.
              </h2>
              <p className="mt-5 max-w-md text-[14px] leading-[1.85] text-fg-mute">
                The title-free version of the prototype film — playable on
                demand with full controls. Use it when the footage needs to
                speak for itself.
              </p>
              <p className="mt-6 font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                PROTOTYPE2.0 — CLEAN, NO TITLE CARD
              </p>
            </Reveal>
            <Reveal y={32} delay={0.1}>
              <ProductVideo
                src={videoCatalog.prototypeClean.src}
                poster={videoCatalog.prototypeClean.poster}
                title="Prototype walkthrough — clean cut"
                preload="none"
                className="aspect-video"
              />
            </Reveal>
          </div>
        </div>
      </Section>
    </>
  );
}
