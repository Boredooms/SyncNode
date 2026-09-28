import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Reveal } from "@/animations/Reveal";
import { SplitText } from "@/animations/SplitText";
import { Section, SectionLabel } from "@/components/Section";
import { useCases } from "@/data/useCases";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export default function UseCases() {
  const domains = Array.from(new Set(useCases.map((u) => u.domain)));
  const [domain, setDomain] = useState<string | null>(null);
  const filtered = domain ? useCases.filter((u) => u.domain === domain) : useCases;
  const reduced = useReducedMotion();

  return (
    <>
      <section className="relative overflow-hidden pb-14 pt-40 md:pt-52">
        <div
          aria-hidden="true"
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 55% 45% at 60% 0%, #131313 0%, #080808 60%)",
          }}
        />
        <div className="container-page relative z-10">
          <SectionLabel>USE CASES</SectionLabel>
          <h1 className="max-w-5xl text-[clamp(2.6rem,7vw,5.4rem)] font-extralight leading-[1.02] tracking-tight text-fg-primary">
            <SplitText mode="fall" stagger={0.05}>
              Work that stays
            </SplitText>
            <br />
            <span className="text-fg-dim">
              <SplitText mode="fall" stagger={0.05} delay={0.2}>
                where it belongs.
              </SplitText>
            </span>
          </h1>
          <Reveal y={18} delay={0.4} className="mt-8 max-w-2xl">
            <p className="text-[15px] leading-relaxed text-fg-mute">
              Representative workflows SyncNode can execute today — each one a
              complete loop from goal to verified artifact, on your hardware.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Domain filter */}
      <section className="border-t border-line">
        <div className="container-page py-10">
          <Reveal y={14}>
            <div className="flex flex-wrap gap-2">
              <FilterChip
                label="ALL"
                active={domain === null}
                onClick={() => setDomain(null)}
              />
              {domains.map((d) => (
                <FilterChip
                  key={d}
                  label={d}
                  active={domain === d}
                  onClick={() => setDomain(domain === d ? null : d)}
                />
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* Cases */}
      <section className="border-t border-line bg-ink-900/30">
        <div className="container-page py-16 md:py-24">
          <AnimatePresence mode="wait">
            <motion.div
              key={domain ?? "all"}
              initial={reduced ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduced ? undefined : { opacity: 0, y: -8 }}
              transition={{ duration: 0.28 }}
              className="grid gap-6 md:grid-cols-2"
            >
              {filtered.map((u, i) => (
                <Reveal key={u.id} y={30} delay={(i % 2) * 0.08} className="h-full">
                  <article className="flex h-full flex-col rounded-lg border border-line bg-ink-800 p-7 transition-colors hover:border-line-bright md:p-9">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                        {u.domain}
                      </span>
                      <span className="font-mono text-micro text-fg-faint">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                    </div>
                    <h2 className="mt-4 text-2xl font-light tracking-tight text-fg-primary">
                      {u.title}
                    </h2>
                    <p className="mt-3 text-[14px] leading-relaxed text-fg-mute">
                      {u.goal}
                    </p>
                    <ol className="mt-6 flex-1 space-y-2.5 border-t border-line pt-5">
                      {u.steps.map((s, si) => (
                        <li
                          key={si}
                          className="flex gap-3 text-[13px] leading-relaxed text-fg-dim"
                        >
                          <span className="shrink-0 font-mono text-[10px] text-fg-faint">
                            {String(si + 1).padStart(2, "0")}
                          </span>
                          {s}
                        </li>
                      ))}
                    </ol>
                    <p className="mt-6 border-t border-line pt-4 text-[13px] text-fg-body">
                      <span className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                        OUTCOME —{" "}
                      </span>
                      {u.outcome}
                    </p>
                  </article>
                </Reveal>
              ))}
            </motion.div>
          </AnimatePresence>
        </div>
      </section>
    </>
  );
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "rounded-[4px] border px-3.5 py-2 font-mono text-[11px] uppercase tracking-wider2 transition-colors",
        active
          ? "border-fg-dim bg-ink-700 text-fg-primary"
          : "border-line bg-ink-800 text-fg-dim hover:text-fg-body"
      )}
    >
      {label}
    </button>
  );
}
