import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Reveal } from "@/animations/Reveal";
import { SplitText } from "@/animations/SplitText";
import { SectionLabel, Section } from "@/components/Section";
import { MagneticButton } from "@/components/MagneticButton";
import { ArrowRight } from "lucide-react";
import { workflowStages } from "@/data/workflow";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

gsap.registerPlugin(ScrollTrigger);

export default function Workflow() {
  const rootRef = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) return;
    const root = rootRef.current;
    if (!root) return;

    const ctx = gsap.context(() => {
      // Each stage: node illuminates → line draws → label rises → body appears.
      gsap.utils.toArray<HTMLElement>("[data-stage]").forEach((stage) => {
        const node = stage.querySelector("[data-node]");
        const connector = stage.querySelector("[data-connector]");
        const label = stage.querySelector("[data-label]");
        const body = stage.querySelector("[data-body]");

        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: stage,
            start: "top 70%",
            once: true,
          },
        });

        if (node) {
          tl.fromTo(
            node,
            { opacity: 0.15, scale: 0.7 },
            { opacity: 1, scale: 1, duration: 0.5, ease: "power2.out" }
          );
        }
        if (connector) {
          tl.fromTo(
            connector,
            { scaleY: 0 },
            { scaleY: 1, duration: 0.5, ease: "power1.inOut", transformOrigin: "top center" },
            "-=0.2"
          );
        }
        if (label) {
          tl.fromTo(
            label,
            { opacity: 0, y: 24 },
            { opacity: 1, y: 0, duration: 0.55, ease: "power3.out" },
            "-=0.35"
          );
        }
        if (body) {
          tl.fromTo(
            body,
            { opacity: 0, y: 14 },
            { opacity: 1, y: 0, duration: 0.45, ease: "power2.out" },
            "-=0.3"
          );
        }
      });
    }, root);

    return () => ctx.revert();
  }, [reduced]);

  return (
    <>
      <section className="relative overflow-hidden pb-16 pt-40 md:pt-52">
        <div
          aria-hidden="true"
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 55% 45% at 50% 0%, #131313 0%, #080808 60%)",
          }}
        />
        <div className="container-page relative z-10 text-center">
          <SectionLabel className="justify-center">WORKFLOW</SectionLabel>
          <h1 className="mx-auto max-w-4xl text-[clamp(2.6rem,7vw,5.6rem)] font-extralight leading-[1.02] tracking-tight text-fg-primary">
            <SplitText mode="fall" stagger={0.05}>
              A system coming alive,
            </SplitText>
            <br />
            <span className="text-fg-dim">
              <SplitText mode="fall" stagger={0.05} delay={0.2}>
                one stage at a time.
              </SplitText>
            </span>
          </h1>
          <Reveal y={18} delay={0.5} className="mx-auto mt-8 max-w-xl">
            <p className="text-[15px] leading-relaxed text-fg-mute">
              Twelve stages take a goal from a sentence to a verified,
              auditable result. Scroll — each node activates as the system
              reaches it.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Stage sequence */}
      <div ref={rootRef} className="relative border-t border-line">
        {/* Progress rail */}
        <div
          aria-hidden="true"
          className="absolute bottom-0 left-6 top-0 hidden w-px bg-line md:left-1/2 md:block"
        />

        {workflowStages.map((stage, i) => {
          const left = i % 2 === 0;
          return (
            <section
              key={stage.id}
              data-stage
              className="relative border-b border-line py-16 last:border-b-0 md:py-24"
            >
              <div className="container-page">
                <div className="grid items-start gap-8 md:grid-cols-2 md:gap-24">
                  {/* Node marker on the rail */}
                  <div
                    aria-hidden="true"
                    className="absolute left-6 top-20 hidden h-3 w-3 -translate-x-1/2 rounded-full border border-fg-dim bg-ink-950 md:left-1/2 md:block"
                  />

                  <div className={cn(left ? "md:pr-16 md:text-right" : "md:order-2 md:pl-16")}>
                    <Reveal y={14}>
                      <div className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                        STAGE {stage.index}
                      </div>
                      <h2
                        data-label
                        className="mt-3 text-4xl font-extralight tracking-tight text-fg-primary md:text-5xl"
                      >
                        {stage.title}
                      </h2>
                    </Reveal>
                  </div>

                  <div className={cn(!left && "md:order-1 md:pr-16")}>
                    <div data-body>
                      <p className="font-mono text-micro-sm uppercase tracking-wider2 text-fg-body">
                        {stage.line}
                      </p>
                      <p className="mt-4 max-w-md text-[14px] leading-[1.85] text-fg-mute">
                        {stage.body}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* connector to next node */}
              {i < workflowStages.length - 1 && (
                <div
                  data-connector
                  aria-hidden="true"
                  className="absolute bottom-0 left-6 top-full hidden h-24 w-px bg-gradient-to-b from-line-bright to-line md:left-1/2 md:block"
                />
              )}
            </section>
          );
        })}
      </div>

      {/* Closing */}
      <Section className="bg-ink-950">
        <div className="container-page flex flex-col items-center text-center">
          <h2 className="max-w-3xl text-[clamp(1.9rem,4vw,3.2rem)] font-extralight leading-[1.1] tracking-tight text-fg-primary">
            The loop ends where trust begins — at verified delivery.
          </h2>
          <div className="mt-10">
            <MagneticButton to="/architecture" variant="secondary" size="lg">
              SEE THE ARCHITECTURE
              <ArrowRight className="h-4 w-4" />
            </MagneticButton>
          </div>
        </div>
      </Section>
    </>
  );
}
