import { Download } from "lucide-react";
import { Reveal } from "@/animations/Reveal";
import { SplitText, ChromaText } from "@/animations/SplitText";
import { Section, SectionLabel, ProseBlock } from "@/components/Section";
import { MagneticButton } from "@/components/MagneticButton";
import { AmbientVideo } from "@/components/media/VideoFrame";
import { videoCatalog } from "@/data/videos";

/**
 * VIDEO PLACEMENT (verified by frame analysis):
 * 1. TOP OF PAGE — "About the Project.mp4": self-contained title card with the
 *    words "About the Project" baked in. It is shown FULL-WIDTH at the very top
 *    with NO overlaid page text. The header simply floats above it.
 * 2. MID PAGE — "About the project 2.0.mp4": title-free animated fog, used as
 *    an ambient background beneath the trust-principle statement (site owns
 *    the words, so no duplication).
 */
export default function About() {
  return (
    <>
      {/* ===== HERO = THE TITLED VIDEO ITSELF, FULL-BLEED, NO OVERLAY TEXT ===== */}
      <section className="relative">
        <AmbientVideo
          src={videoCatalog.aboutTitled.src}
          poster={videoCatalog.aboutTitled.poster}
          className="h-[92svh] min-h-[560px] w-full"
          scaleOnScroll={false}
          overlayClassName="bg-black/15"
          videoFilter="brightness(1.05)"
          cropWatermark
        />
        {/* Quiet scroll cue only — no words competing with the baked-in title */}
        <div className="pointer-events-none absolute inset-x-0 bottom-8 z-10 flex justify-center">
          <div className="h-10 w-px overflow-hidden bg-line">
            <div className="h-1/2 w-full animate-pulse-soft bg-fg-mute" />
          </div>
        </div>
      </section>

      {/* What SyncNode is */}
      <ProseBlock label="WHAT IT IS" title="A workbench, not a window.">
        <p>
          SyncNode is a sovereign AI workbench: a place where real work gets
          done, not just questions answered. You give it a goal in plain
          language. It understands the intent, grounds it in your local
          documents, plans the work as a graph of steps, and executes those
          steps through typed tools against your actual machine.
        </p>
        <p>
          Chat tools stop at the answer. RPA tools follow scripts. SyncNode
          combines the intelligence of the first with the determinism of the
          second — then adds the layer both lack: verification.
        </p>
      </ProseBlock>

      {/* Why local */}
      <Section className="border-t border-line bg-ink-900/40">
        <div className="container-page">
          <div className="grid gap-10 md:grid-cols-12 md:gap-16">
            <Reveal className="md:col-span-5">
              <SectionLabel>WHY LOCAL</SectionLabel>
              <h2 className="text-3xl font-light leading-tight tracking-tight text-fg-primary md:text-4xl">
                Serious work has a jurisdiction problem.
              </h2>
            </Reveal>
            <Reveal className="md:col-span-7" y={24} delay={0.1}>
              <div className="space-y-5 text-[15px] leading-[1.85] text-fg-mute">
                <p>
                  Legal files. Medical records. Engineering documentation.
                  Procurement submissions. This work carries obligations —
                  confidentiality, compliance, professional liability — that a
                  public AI endpoint cannot share. The moment your document
                  leaves your machine, you rely on someone else's retention
                  policy, security posture, and goodwill.
                </p>
                <p>
                  Local AI changes the equation. Modern quantized models reason
                  well enough for real knowledge work. Running them on your own
                  GPU means the analysis happens where the data already lives —
                  with no new copies, no new custodians, and no metered tokens.
                </p>
                <p className="text-fg-body">
                  But local inference alone solves only half the problem.
                </p>
              </div>
            </Reveal>
          </div>
        </div>
      </Section>

      {/* Why existing AI stops too early */}
      <Section className="border-t border-line bg-ink-950">
        <div className="container-page">
          <SectionLabel>THE GAP</SectionLabel>
          <h2 className="max-w-4xl text-[clamp(1.9rem,4vw,3.2rem)] font-extralight leading-[1.15] tracking-tight text-fg-primary">
            <ChromaText>
              Existing AI stops exactly where the work begins.
            </ChromaText>
          </h2>

          <div className="mt-16 space-y-px overflow-hidden rounded-lg border border-line bg-line">
            {[
              ["CHAT", "Answers questions. Cannot touch a file."],
              ["RAG", "Reads documents. Cannot produce anything."],
              ["AGENTS", "Can plan actions. Nobody checks the result."],
              ["EXECUTION", "Can act. Often without permission or proof."],
              ["VERIFIED EXECUTION", "Plans, acts, observes, verifies, asks. This is SyncNode."],
            ].map(([stage, note], i) => (
              <Reveal key={stage} y={18} delay={i * 0.05}>
                <div
                  className={
                    "flex flex-col gap-2 px-6 py-7 sm:flex-row sm:items-center sm:gap-10 md:px-10 " +
                    (stage === "VERIFIED EXECUTION"
                      ? "bg-ink-700"
                      : "bg-ink-900")
                  }
                >
                  <span className="w-44 shrink-0 font-mono text-micro-sm uppercase tracking-wider2 text-fg-primary">
                    {stage}
                  </span>
                  <span className="text-[14px] text-fg-mute">{note}</span>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </Section>

      {/* Trust principle — over the CLEAN 2.0 video (no baked-in title → safe) */}
      <section className="relative border-t border-line">
        <AmbientVideo
          src={videoCatalog.aboutClean.src}
          poster={videoCatalog.aboutClean.poster}
          className="absolute inset-0"
          scaleOnScroll={false}
          overlayClassName="bg-ink-950/70"
        />
        <div className="container-page relative z-10 py-32 text-center md:py-44">
          <Reveal y={20}>
            <p className="mx-auto max-w-4xl text-[clamp(1.6rem,3.5vw,2.8rem)] font-extralight leading-[1.3] tracking-tight text-fg-primary">
              "The model proposes. Deterministic infrastructure validates,
              authorizes, executes and verifies."
            </p>
          </Reveal>
          <Reveal y={14} delay={0.15}>
            <p className="mt-6 font-mono text-micro uppercase tracking-wider2 text-fg-faint">
              THE CENTRAL TRUST PRINCIPLE
            </p>
          </Reveal>
        </div>
      </section>

      {/* What "act" means */}
      <Section className="border-t border-line bg-ink-900/40">
        <div className="container-page">
          <div className="grid gap-12 md:grid-cols-12 md:gap-16">
            <Reveal className="md:col-span-5">
              <SectionLabel>WHAT "ACT" MEANS</SectionLabel>
              <h2 className="text-3xl font-light leading-tight tracking-tight text-fg-primary md:text-4xl">
                Controlled action, with receipts.
              </h2>
            </Reveal>
            <Reveal className="md:col-span-7" y={24} delay={0.1}>
              <div className="space-y-5 text-[15px] leading-[1.85] text-fg-mute">
                <p>
                  Acting means creating the Word document, filling the workbook,
                  opening the application, completing the form — and then
                  proving each of those things happened. Post-condition
                  assertions check the file exists and is non-empty, the window
                  is present, the field holds the expected value. If a step
                  fails, it is marked failed. Recovery re-observes and re-plans.
                  Nothing is silently retried with fingers crossed.
                </p>
                <p>
                  When an action leaves the machine — an email, a submission —
                  the run stops and waits for you. The decision is recorded
                  either way, in a hash-chained audit log.
                </p>
              </div>
            </Reveal>
          </div>
        </div>
      </Section>

      {/* The complete loop */}
      <Section className="border-t border-line bg-ink-950">
        <div className="container-page">
          <SectionLabel>THE COMPLETE LOOP</SectionLabel>
          <div className="mt-4 grid gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-3 lg:grid-cols-6">
            {["UNDERSTAND", "PLAN", "AUTHORIZE", "ACT", "OBSERVE", "VERIFY"].map(
              (s, i) => (
                <Reveal key={s} y={16} delay={i * 0.05}>
                  <div className="flex h-full flex-col gap-8 bg-ink-900 p-5">
                    <span className="font-mono text-micro text-fg-faint">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="font-mono text-[11px] uppercase tracking-wider2 text-fg-body">
                      {s}
                    </span>
                  </div>
                </Reveal>
              )
            )}
          </div>
          <Reveal y={16} className="mt-6">
            <p className="max-w-xl text-[14px] leading-relaxed text-fg-dim">
              The loop never runs unattended at the edges. Authorization and
              verification are structural, not optional.
            </p>
          </Reveal>
        </div>
      </Section>

      {/* CTA */}
      <section className="border-t border-line">
        <div className="container-page flex flex-col items-center py-28 text-center md:py-36">
          <h2 className="max-w-3xl text-[clamp(2rem,4.5vw,3.6rem)] font-extralight leading-[1.08] tracking-tight text-fg-primary">
            Run it yourself.
          </h2>
          <div className="mt-10">
            <MagneticButton to="/download" variant="primary" size="lg">
              <Download className="h-4 w-4" />
              DOWNLOAD FOR WINDOWS
            </MagneticButton>
          </div>
        </div>
      </section>
    </>
  );
}
