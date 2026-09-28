import { Download, Check, ArrowRight } from "lucide-react";
import { Reveal } from "@/animations/Reveal";
import { ChromaText } from "@/animations/SplitText";
import { Section, SectionLabel } from "@/components/Section";
import { MagneticButton } from "@/components/MagneticButton";
import { AmbientVideo } from "@/components/media/VideoFrame";
import { videoCatalog } from "@/data/videos";
import { featureFamilies } from "@/data/features";
import { cn } from "@/lib/utils";

/**
 * VIDEO PLACEMENT (verified by frame analysis):
 * 1. TOP OF PAGE — "Features.mp4": "Features" is baked into the footage.
 *    Full-bleed at the very top, NO overlaid page text.
 * 2. CLOSING — "Features2.0.mp4": title-free fog used as the ambient
 *    background under the closing statement (site owns the words).
 */
export default function Features() {
  return (
    <>
      {/* ===== HERO = THE TITLED FEATURES VIDEO, FULL-BLEED, NO OVERLAY ===== */}
      <section className="relative">
        <AmbientVideo
          src={videoCatalog.featuresTitled.src}
          poster={videoCatalog.featuresTitled.poster}
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

      {/* Intro statement */}
      <Section className="border-t border-line bg-ink-950">
        <div className="container-page">
          <div className="mx-auto max-w-3xl text-center">
            <Reveal y={16}>
              <div className="eyebrow mb-8">CAPABILITIES</div>
            </Reveal>
            <h2 className="text-[clamp(1.8rem,3.8vw,3rem)] font-extralight leading-[1.25] tracking-tight text-fg-primary">
              <ChromaText>
                Six families of capability — from local inference to the audit
                chain. Each exists to make the others trustworthy.
              </ChromaText>
            </h2>
          </div>
        </div>
      </Section>

      {/* Feature families — alternating editorial rows */}
      <div className="border-t border-line">
        {featureFamilies.map((f, i) => (
          <section
            key={f.id}
            id={f.id}
            className={cn(
              "border-b border-line py-20 md:py-28",
              i % 2 === 1 && "bg-ink-900/40"
            )}
          >
            <div className="container-page">
              <div className="grid gap-12 md:grid-cols-12 md:gap-16">
                <Reveal className="md:col-span-5" y={28}>
                  <div className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                    {String(i + 1).padStart(2, "0")} — {f.label}
                  </div>
                  <h2 className="mt-5 text-3xl font-light leading-tight tracking-tight text-fg-primary md:text-4xl">
                    {f.title}
                  </h2>
                  <p className="mt-5 text-[15px] leading-[1.85] text-fg-mute">
                    {f.summary}
                  </p>
                  <p className="mt-6 border-l-2 border-line pl-4 text-[13px] leading-relaxed text-fg-dim">
                    {f.why}
                  </p>
                  <div className="mt-6 font-mono text-micro-sm uppercase tracking-wider2 text-fg-faint">
                    {f.detail}
                  </div>
                </Reveal>

                <Reveal className="md:col-span-6 md:col-start-7" y={28} delay={0.1}>
                  <div className="rounded-lg border border-line bg-ink-800 p-7 md:p-9">
                    <div className="eyebrow mb-5">CAPABILITIES</div>
                    <ul className="space-y-3.5">
                      {f.capabilities.map((c) => (
                        <li key={c} className="flex items-start gap-3 text-[14px] text-fg-body">
                          <Check
                            className="mt-0.5 h-3.5 w-3.5 shrink-0 text-fg-dim"
                            aria-hidden="true"
                          />
                          {c}
                        </li>
                      ))}
                    </ul>
                    <div className="mt-7 border-t border-line pt-5 text-[13px] leading-relaxed text-fg-dim">
                      <span className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                        HOW —{" "}
                      </span>
                      {f.how}
                    </div>
                  </div>
                </Reveal>
              </div>
            </div>
          </section>
        ))}
      </div>

      {/* Closing statement — over the CLEAN features video */}
      <section className="relative border-t border-line">
        <AmbientVideo
          src={videoCatalog.featuresClean.src}
          poster={videoCatalog.featuresClean.poster}
          className="absolute inset-0"
          scaleOnScroll={false}
          overlayClassName="bg-ink-950/70"
        />
        <div className="container-page relative z-10 py-32 text-center md:py-40">
          <h2 className="mx-auto max-w-4xl text-[clamp(1.8rem,4vw,3.2rem)] font-extralight leading-[1.2] tracking-tight text-fg-primary">
            <ChromaText>
              Every capability answers one question: can you trust what the
              system just did?
            </ChromaText>
          </h2>
          <Reveal y={16} delay={0.1} className="mt-12">
            <div className="flex flex-wrap items-center justify-center gap-4">
              <MagneticButton to="/download" variant="primary" size="lg">
                <Download className="h-4 w-4" />
                DOWNLOAD FOR WINDOWS
              </MagneticButton>
              <MagneticButton to="/security" variant="secondary" size="lg">
                HOW TRUST IS ENFORCED
                <ArrowRight className="h-4 w-4" />
              </MagneticButton>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
