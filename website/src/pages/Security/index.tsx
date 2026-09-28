import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Reveal } from "@/animations/Reveal";
import { SplitText, ChromaText } from "@/animations/SplitText";
import { Section, SectionLabel } from "@/components/Section";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

gsap.registerPlugin(ScrollTrigger);

const TRACE = [
  { label: "INPUT", value: "goal + local documents" },
  { label: "MODEL", value: "gemma4:e4b — local inference" },
  { label: "SOURCE", value: "ChromaDB retrieval, attributed" },
  { label: "TOOL", value: "schema-validated tool call" },
  { label: "ACTION", value: "executed on local machine" },
  { label: "OBSERVATION", value: "real state captured as evidence" },
  { label: "VERIFICATION", value: "post-condition assertions" },
  { label: "OUTPUT", value: "artifact + proof" },
  { label: "AUDIT HASH", value: "SHA-256 chained event" },
];

const STATUS = [
  { k: "EXTERNAL AI API", v: "NOT REQUIRED", tone: "warn" },
  { k: "LOCAL PROCESSING", v: "ACTIVE", tone: "ok" },
  { k: "CONTROLLED TOOLS", v: "ACTIVE", tone: "ok" },
  { k: "AUDIT TRAIL", v: "ACTIVE", tone: "ok" },
] as const;

export default function Security() {
  const traceRef = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) return;
    const root = traceRef.current;
    if (!root) return;

    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>("[data-trace-row]").forEach((row) => {
        gsap.fromTo(
          row,
          { opacity: 0.18 },
          {
            opacity: 1,
            duration: 0.5,
            ease: "power1.out",
            scrollTrigger: { trigger: row, start: "top 78%", once: true },
          }
        );
        const line = row.querySelector("[data-trace-line]");
        if (line) {
          gsap.fromTo(
            line,
            { scaleX: 0 },
            {
              scaleX: 1,
              duration: 0.6,
              ease: "power1.inOut",
              transformOrigin: "left center",
              scrollTrigger: { trigger: row, start: "top 78%", once: true },
            }
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
        <div className="container-page relative z-10">
          <SectionLabel>SECURITY</SectionLabel>
          <h1 className="max-w-5xl text-[clamp(2.6rem,7vw,5.4rem)] font-extralight leading-[1.04] tracking-tight text-fg-primary">
            <SplitText mode="fall" stagger={0.05}>
              Sovereignty is an
            </SplitText>
            <br />
            <span className="text-fg-dim">
              <SplitText mode="fall" stagger={0.05} delay={0.2}>
                execution property.
              </SplitText>
            </span>
          </h1>
          <Reveal y={18} delay={0.45} className="mt-8 max-w-2xl">
            <p className="text-[15px] leading-relaxed text-fg-mute">
              Security here is not a badge or a certificate. It is where the
              computation physically happens, who may authorize an action, and
              whether the result can be proven afterwards.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Chain */}
      <Section className="border-t border-line">
        <div className="container-page">
          <SectionLabel>THE SOVEREIGN CHAIN</SectionLabel>
          <div className="mt-4 grid gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-4 lg:grid-cols-7">
            {["LOCAL MODEL", "LOCAL KNOWLEDGE", "LOCAL TOOL", "LOCAL EXECUTION", "OBSERVATION", "VERIFICATION", "AUDIT"].map(
              (s, i) => (
                <Reveal key={s} y={16} delay={i * 0.04}>
                  <div className="flex h-full flex-col gap-8 bg-ink-900 p-4">
                    <span className="font-mono text-micro text-fg-faint">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="font-mono text-[10px] uppercase tracking-wider2 text-fg-body">
                      {s}
                    </span>
                  </div>
                </Reveal>
              )
            )}
          </div>
          <Reveal y={14} className="mt-6">
            <p className="max-w-2xl text-[14px] leading-relaxed text-fg-dim">
              Every link runs on infrastructure you own. The model is local,
              the knowledge is local, the tools act locally — and the record of
              all three never leaves the machine.
            </p>
          </Reveal>
        </div>
      </Section>

      {/* Evidence trace */}
      <Section className="border-t border-line bg-ink-900/40">
        <div className="container-page">
          <div className="grid gap-12 lg:grid-cols-[1.3fr_1fr]">
            <div ref={traceRef}>
              <SectionLabel>EVIDENCE TRACE</SectionLabel>
              <p className="mb-8 max-w-md text-[14px] leading-relaxed text-fg-dim">
                A single workflow step, traced from goal to audit event.
              </p>
              <div className="space-y-0 overflow-hidden rounded-lg border border-line bg-ink-950">
                {TRACE.map((t, i) => (
                  <div
                    key={t.label}
                    data-trace-row
                    className={cn(
                      "border-b border-line px-5 py-4 last:border-b-0",
                      i === TRACE.length - 1 && "bg-ink-800"
                    )}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <span className="font-mono text-[11px] uppercase tracking-wider2 text-fg-primary">
                        {t.label}
                      </span>
                      <span className="font-mono text-[10px] uppercase tracking-wider2 text-fg-dim">
                        {t.value}
                      </span>
                    </div>
                    <div
                      data-trace-line
                      aria-hidden="true"
                      className="mt-3 h-px w-full bg-gradient-to-r from-line-bright to-transparent"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Status panel */}
            <div>
              <SectionLabel>SYSTEM POSTURE</SectionLabel>
              <div className="space-y-3">
                {STATUS.map((s, i) => (
                  <Reveal key={s.k} y={18} delay={i * 0.06}>
                    <div className="flex items-center justify-between rounded-lg border border-line bg-ink-800 px-5 py-4">
                      <span className="font-mono text-[11px] uppercase tracking-wider2 text-fg-mute">
                        {s.k}
                      </span>
                      <span
                        className={cn(
                          "font-mono text-[11px] uppercase tracking-wider2",
                          s.tone === "ok" ? "text-ok" : "text-warn"
                        )}
                      >
                        {s.v}
                      </span>
                    </div>
                  </Reveal>
                ))}
              </div>
              <Reveal y={16} className="mt-8">
                <div className="rounded-lg border border-line bg-ink-900 p-6">
                  <div className="eyebrow mb-3">HONEST SCOPE</div>
                  <p className="text-[13px] leading-relaxed text-fg-dim">
                    SyncNode is designed to operate without external AI APIs,
                    with local-only inference by default and a policy-driven
                    approval gate. No system can promise absolute security;
                    SyncNode gives you control, observation and proof instead.
                  </p>
                </div>
              </Reveal>
            </div>
          </div>
        </div>
      </Section>

      {/* Statement */}
      <Section className="border-t border-line bg-ink-950">
        <div className="container-page text-center">
          <h2 className="mx-auto max-w-3xl text-[clamp(1.7rem,3.6vw,2.8rem)] font-extralight leading-[1.25] tracking-tight">
            <ChromaText>
              What cannot be proven did not happen. What can be proven did.
            </ChromaText>
          </h2>
        </div>
      </Section>
    </>
  );
}
