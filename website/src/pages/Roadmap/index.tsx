import { Check, Loader, CircleDashed, Ban } from "lucide-react";
import { Reveal } from "@/animations/Reveal";
import { SplitText } from "@/animations/SplitText";
import { Section, SectionLabel } from "@/components/Section";
import { roadmapPhases, neverList, type RoadmapStatus } from "@/data/roadmap";
import { cn } from "@/lib/utils";

const STATUS_META: Record<
  RoadmapStatus,
  { icon: typeof Check; cls: string }
> = {
  BUILT: { icon: Check, cls: "text-ok" },
  INTEGRATING: { icon: Loader, cls: "text-warn" },
  PLANNED: { icon: CircleDashed, cls: "text-fg-dim" },
};

export default function Roadmap() {
  return (
    <>
      <section className="relative overflow-hidden pb-14 pt-40 md:pt-52">
        <div
          aria-hidden="true"
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 55% 45% at 55% 0%, #131313 0%, #080808 60%)",
          }}
        />
        <div className="container-page relative z-10">
          <SectionLabel>ROADMAP</SectionLabel>
          <h1 className="max-w-5xl text-[clamp(2.6rem,7vw,5.4rem)] font-extralight leading-[1.02] tracking-tight text-fg-primary">
            <SplitText mode="fall" stagger={0.05}>
              Built honestly,
            </SplitText>
            <br />
            <span className="text-fg-dim">
              <SplitText mode="fall" stagger={0.05} delay={0.2}>
                shipped incrementally.
              </SplitText>
            </span>
          </h1>
          <Reveal y={18} delay={0.4} className="mt-8 max-w-2xl">
            <p className="text-[15px] leading-relaxed text-fg-mute">
              What has shipped, what is integrating, and what is planned —
              kept strictly separate so the roadmap describes reality.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Timeline */}
      <Section className="border-t border-line">
        <div className="container-page">
          <div className="relative space-y-12 before:absolute before:bottom-0 before:left-[7px] before:top-2 before:w-px before:bg-line md:before:left-[9px]">
            {roadmapPhases.map((phase, i) => {
              const meta = STATUS_META[phase.status];
              const Icon = meta.icon;
              return (
                <Reveal key={phase.id} y={28} delay={i * 0.04}>
                  <div className="relative pl-10 md:pl-14">
                    <span
                      aria-hidden="true"
                      className="absolute left-0 top-1 flex h-4 w-4 items-center justify-center rounded-full border border-line bg-ink-950"
                    >
                      <span className={cn("h-1.5 w-1.5 rounded-full", meta.cls.replace("text-", "bg-"))} />
                    </span>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                      <span className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                        {phase.version}
                      </span>
                      <span className="flex items-center gap-1.5 font-mono text-micro uppercase tracking-wider2">
                        <Icon className={cn("h-3 w-3", meta.cls)} aria-hidden="true" />
                        <span className={meta.cls}>{phase.status}</span>
                      </span>
                      <span className="text-[13px] text-fg-faint">{phase.focus}</span>
                    </div>

                    <h2 className="mt-3 text-2xl font-light tracking-tight text-fg-primary md:text-3xl">
                      {phase.title}
                    </h2>

                    <ul className="mt-5 grid gap-x-10 gap-y-2.5 sm:grid-cols-2">
                      {phase.items.map((item) => (
                        <li
                          key={item.text}
                          className="flex gap-2.5 text-[13px] leading-relaxed text-fg-mute"
                        >
                          <span
                            aria-hidden="true"
                            className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-fg-faint"
                          />
                          {item.text}
                        </li>
                      ))}
                    </ul>
                  </div>
                </Reveal>
              );
            })}
          </div>
        </div>
      </Section>

      {/* Never list */}
      <Section className="border-t border-line bg-ink-900/40">
        <div className="container-page">
          <div className="grid gap-10 md:grid-cols-12">
            <Reveal className="md:col-span-4" y={20}>
              <SectionLabel>OUT OF SCOPE — BY DESIGN</SectionLabel>
              <h2 className="text-3xl font-light tracking-tight text-fg-primary">
                Never.
              </h2>
              <p className="mt-4 text-[14px] leading-relaxed text-fg-dim">
                Product boundaries are commitments. These are stated so you
                never have to wonder.
              </p>
            </Reveal>
            <Reveal className="md:col-span-7 md:col-start-6" y={20} delay={0.1}>
              <ul className="space-y-px overflow-hidden rounded-lg border border-line bg-line">
                {neverList.map((t) => (
                  <li
                    key={t}
                    className="flex items-center gap-4 bg-ink-900 px-6 py-4"
                  >
                    <Ban className="h-3.5 w-3.5 shrink-0 text-fg-faint" aria-hidden="true" />
                    <span className="text-[13px] text-fg-mute">{t}</span>
                  </li>
                ))}
              </ul>
            </Reveal>
          </div>
        </div>
      </Section>
    </>
  );
}
