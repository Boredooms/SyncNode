import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Reveal } from "@/animations/Reveal";
import { SplitText } from "@/animations/SplitText";
import { Section, SectionLabel } from "@/components/Section";
import { architectureNodes, type ArchNode } from "@/data/architecture";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export default function Architecture() {
  const [selected, setSelected] = useState<ArchNode>(
    architectureNodes.find((n) => n.id === "orchestrator")!
  );
  const reduced = useReducedMotion();

  const layers = useMemo(() => {
    const map = new Map<number, ArchNode[]>();
    for (const n of architectureNodes) {
      const arr = map.get(n.layer) ?? [];
      arr.push(n);
      map.set(n.layer, arr);
    }
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, []);

  return (
    <>
      <section className="relative overflow-hidden pb-14 pt-40 md:pt-52">
        <div
          aria-hidden="true"
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 55% 45% at 70% 0%, #131313 0%, #080808 60%)",
          }}
        />
        <div className="container-page relative z-10">
          <SectionLabel>ARCHITECTURE</SectionLabel>
          <h1 className="max-w-5xl text-[clamp(2.6rem,7vw,5.4rem)] font-extralight leading-[1.02] tracking-tight text-fg-primary">
            <SplitText mode="fall" stagger={0.05}>
              Schematic honesty:
            </SplitText>
            <br />
            <span className="text-fg-dim">
              <SplitText mode="fall" stagger={0.05} delay={0.2}>
                every layer, inspectable.
              </SplitText>
            </span>
          </h1>
          <Reveal y={18} delay={0.45} className="mt-8 max-w-2xl">
            <p className="text-[15px] leading-relaxed text-fg-mute">
              Select a node to inspect its role, inputs, outputs and the local
              technology behind it. The diagram mirrors the running system —
              not an aspiration.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Graph + inspector */}
      <section className="border-t border-line">
        <div className="container-page py-16 md:py-24">
          <div className="grid gap-10 lg:grid-cols-[1fr_360px]">
            {/* Graph */}
            <Reveal y={30}>
              <div className="overflow-hidden rounded-lg border border-line bg-ink-900/60">
                <div className="flex items-center justify-between border-b border-line px-5 py-3">
                  <span className="font-mono text-micro uppercase tracking-wider2 text-fg-dim">
                    SYSTEM TOPOLOGY
                  </span>
                  <span className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                    {architectureNodes.length} NODES · LOCAL
                  </span>
                </div>
                <div className="space-y-0 p-5 md:p-8">
                  {layers.map(([layer, nodes], li) => (
                    <div key={layer}>
                      {li > 0 && <LayerConnector />}
                      <div
                        className={cn(
                          "flex flex-wrap gap-2",
                          nodes.length > 1 && "sm:justify-center"
                        )}
                      >
                        {nodes.map((n) => (
                          <button
                            key={n.id}
                            onClick={() => setSelected(n)}
                            aria-pressed={selected.id === n.id}
                            className={cn(
                              "rounded-[4px] border px-3.5 py-2 font-mono text-[11px] uppercase tracking-wider2 transition-all duration-200",
                              selected.id === n.id
                                ? "border-fg-dim bg-ink-700 text-fg-primary"
                                : "border-line bg-ink-800 text-fg-mute hover:border-line-bright hover:text-fg-body"
                            )}
                          >
                            {n.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Reveal>

            {/* Inspector */}
            <div className="lg:sticky lg:top-24 lg:self-start">
              <Reveal y={30} delay={0.1}>
                <div className="overflow-hidden rounded-lg border border-line bg-ink-800">
                  <div className="flex items-center justify-between border-b border-line px-5 py-3">
                    <span className="font-mono text-micro uppercase tracking-wider2 text-fg-dim">
                      NODE INSPECTOR
                    </span>
                    <span className="font-mono text-micro text-fg-faint">
                      LAYER {selected.layer}
                    </span>
                  </div>
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={selected.id}
                      initial={reduced ? false : { opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={reduced ? undefined : { opacity: 0, y: -6 }}
                      transition={{ duration: 0.22 }}
                      className="p-6"
                    >
                      <h2 className="font-mono text-lg tracking-wider2 text-fg-primary">
                        {selected.name}
                      </h2>
                      <p className="mt-3 text-[14px] leading-relaxed text-fg-mute">
                        {selected.role}
                      </p>
                      <dl className="mt-6 space-y-4 border-t border-line pt-5">
                        <InspectorRow label="INPUT" value={selected.input} />
                        <InspectorRow label="OUTPUT" value={selected.output} />
                        <InspectorRow label="LOCAL TECHNOLOGY" value={selected.tech} />
                      </dl>
                    </motion.div>
                  </AnimatePresence>
                </div>
              </Reveal>
            </div>
          </div>
        </div>
      </section>

      {/* Flow strip */}
      <Section className="border-t border-line bg-ink-900/40">
        <div className="container-page">
          <SectionLabel>END-TO-END FLOW</SectionLabel>
          <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-4 font-mono text-[11px] uppercase tracking-wider2">
            {[
              "USER", "ELECTRON", "API", "ORCHESTRATOR", "MODEL ROUTER", "KNOWLEDGE",
              "SUPERVISOR", "AGENTS", "TOOLS", "EXECUTION", "OBSERVATION",
              "VERIFICATION", "RECOVERY", "APPROVAL", "AUDIT", "MEMORY",
            ].map((n, i, arr) => (
              <span key={n} className="flex items-center gap-3">
                <span className="text-fg-mute">{n}</span>
                {i < arr.length - 1 && (
                  <span aria-hidden="true" className="text-fg-faint">→</span>
                )}
              </span>
            ))}
          </div>
          <Reveal y={14} className="mt-8">
            <p className="max-w-2xl text-[14px] leading-relaxed text-fg-dim">
              Observation, verification, recovery, approval, audit and memory
              wrap the execution path — the model is never the final
              authority on any step.
            </p>
          </Reveal>
        </div>
      </Section>
    </>
  );
}

function InspectorRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
        {label}
      </dt>
      <dd className="mt-1 text-[13px] text-fg-body">{value}</dd>
    </div>
  );
}

function LayerConnector() {
  return (
    <div aria-hidden="true" className="flex justify-center py-3">
      <div className="h-6 w-px bg-line" />
    </div>
  );
}
