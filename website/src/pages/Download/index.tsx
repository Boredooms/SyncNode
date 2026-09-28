import { Download as DownloadIcon, Github, Monitor, Cpu, HardDrive, ShieldCheck, ArrowUpRight } from "lucide-react";
import { Reveal } from "@/animations/Reveal";
import { SplitText } from "@/animations/SplitText";
import { Section, SectionLabel } from "@/components/Section";
import { MagneticButton } from "@/components/MagneticButton";
import { GITHUB_URL, GITHUB_RELEASES_URL } from "@/data/videos";

const REQUIREMENTS = [
  { icon: Monitor, k: "OPERATING SYSTEM", v: "Windows 10 / 11 x64" },
  { icon: Cpu, k: "GPU", v: "NVIDIA 4GB+ VRAM recommended · CPU fallback" },
  { icon: HardDrive, k: "STORAGE", v: "~20 GB (models, dependencies, workspace)" },
  { icon: ShieldCheck, k: "AI RUNTIME", v: "Ollama — local inference, no cloud" },
];

export default function Download() {
  return (
    <>
      <section className="relative overflow-hidden pb-14 pt-40 md:pt-52">
        <div
          aria-hidden="true"
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 55% 45% at 50% 0%, #131313 0%, #080808 60%)",
          }}
        />
        <div className="container-page relative z-10 text-center">
          <SectionLabel className="justify-center">DOWNLOAD</SectionLabel>
          <h1 className="mx-auto max-w-4xl text-[clamp(2.6rem,7vw,5.4rem)] font-extralight leading-[1.02] tracking-tight text-fg-primary">
            <SplitText mode="fall" stagger={0.05}>
              Run SyncNode locally.
            </SplitText>
          </h1>
          <Reveal y={18} delay={0.4} className="mx-auto mt-8 max-w-xl">
            <p className="text-[15px] leading-relaxed text-fg-mute">
              Windows desktop application. Local AI. Local workflows. Your
              data never leaves the machine.
            </p>
          </Reveal>
        </div>
      </section>

      <Section className="border-t border-line">
        <div className="container-page">
          <div className="mx-auto max-w-2xl">
            {/* Download card */}
            <Reveal y={40}>
              <div className="overflow-hidden rounded-xl border border-line bg-gradient-to-b from-ink-800 to-ink-900">
                <div className="border-b border-line px-8 py-6 md:px-10">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-micro uppercase tracking-wider2 text-fg-dim">
                      SYNCNODE FOR WINDOWS
                    </span>
                    <span className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                      DESKTOP · x64
                    </span>
                  </div>
                  <p className="mt-4 text-xl font-light tracking-tight text-fg-primary">
                    Sovereign local AI workbench
                  </p>
                </div>

                <div className="px-8 py-8 md:px-10">
                  <div className="grid grid-cols-3 gap-3 text-center">
                    {["WINDOWS", "DESKTOP", "LOCAL AI"].map((t) => (
                      <div
                        key={t}
                        className="rounded-[4px] border border-line bg-ink-950 px-2 py-3 font-mono text-[10px] uppercase tracking-wider2 text-fg-mute"
                      >
                        {t}
                      </div>
                    ))}
                  </div>

                  <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                    {/* Points to the real releases page — never a fabricated .exe */}
                    <MagneticButton href={GITHUB_RELEASES_URL} external variant="primary" size="lg" className="flex-1">
                      <DownloadIcon className="h-4 w-4" />
                      DOWNLOAD
                    </MagneticButton>
                    <MagneticButton href={GITHUB_URL} external variant="secondary" size="lg" className="flex-1">
                      <Github className="h-4 w-4" />
                      VIEW SOURCE ON GITHUB
                    </MagneticButton>
                  </div>

                  <div className="mt-6 flex items-center justify-center gap-2 font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                    <ArrowUpRight className="h-3 w-3" aria-hidden="true" />
                    LATEST RELEASE · OPEN SOURCE DISTRIBUTION VIA GITHUB
                  </div>
                </div>
              </div>
            </Reveal>

            {/* Requirements */}
            <Reveal y={24} delay={0.1} className="mt-10">
              <div className="space-y-px overflow-hidden rounded-lg border border-line bg-line">
                {REQUIREMENTS.map((r) => (
                  <div
                    key={r.k}
                    className="flex items-center gap-5 bg-ink-900 px-6 py-5"
                  >
                    <r.icon className="h-4 w-4 shrink-0 text-fg-dim" aria-hidden="true" />
                    <span className="w-40 shrink-0 font-mono text-micro uppercase tracking-wider2 text-fg-dim">
                      {r.k}
                    </span>
                    <span className="text-[13px] text-fg-body">{r.v}</span>
                  </div>
                ))}
              </div>
            </Reveal>

            <Reveal y={16} delay={0.15} className="mt-8">
              <p className="text-center font-mono text-micro uppercase leading-loose tracking-wider2 text-fg-faint">
                AFTER INSTALL — DOWNLOAD THE GEMMA 4 MODEL VIA OLLAMA (~9.6 GB).
                <br />
                THE APPLICATION RUNS FULLY OFFLINE ONCE MODELS ARE LOCAL.
              </p>
            </Reveal>
          </div>
        </div>
      </Section>
    </>
  );
}
