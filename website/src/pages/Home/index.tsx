import { Download, Github, ArrowRight } from "lucide-react";
import { Reveal } from "@/animations/Reveal";
import { SplitText, ChromaText } from "@/animations/SplitText";
import {
  Section,
  SectionLabel,
  SectionHeading,
} from "@/components/Section";
import { MagneticButton } from "@/components/MagneticButton";
import { Hero } from "@/components/home/Hero";
import { GITHUB_URL } from "@/data/videos";

const PRINCIPLE_STAGES = [
  { label: "UNDERSTAND", note: "The goal becomes a structured intent." },
  { label: "PLAN", note: "Work decomposes into a visible graph." },
  { label: "AUTHORIZE", note: "Policy and you decide what is permitted." },
  { label: "ACT", note: "Typed tools touch the real machine." },
  { label: "OBSERVE", note: "Reality is captured, not assumed." },
  { label: "VERIFY", note: "Assertions run against the result." },
];

const THINK_ACT_PROVE = [
  {
    id: "think",
    label: "THINK",
    title: "Local model reasoning, local knowledge",
    body: "Gemma 4 runs on your GPU through Ollama. Your documents are embedded into a local vector store. Reasoning and retrieval never leave the machine.",
    points: ["gemma4:e4b · 128k context", "ChromaDB local RAG", "No API keys, no metered tokens"],
  },
  {
    id: "act",
    label: "ACT",
    title: "Specialist agents, controlled tools, real execution",
    body: "A supervisor dispatches specialists — Writer, Document, Office, Computer, Browser. Every action is a schema-validated tool call against your actual desktop.",
    points: ["8 agent types on a LangGraph DAG", "44 deterministic tools", "Files, Windows, Office, Chromium"],
  },
  {
    id: "prove",
    label: "PROVE",
    title: "Observation, verification, approval, audit",
    body: "After every action the runtime asserts against real state. External actions stop for your approval. Every event lands in a SHA-256 chain.",
    points: ["Post-condition assertions", "Human approval gate", "Immutable audit trail"],
  },
];

const FLOW_NODES = [
  "USER GOAL", "CONTEXT", "INTENT", "PLAN", "AGENTS", "TOOLS",
  "EXECUTION", "OBSERVATION", "VERIFICATION", "RESULT",
];

const REAL_WORK = [
  { label: "CREATE", text: "DOCX · XLSX · PPTX" },
  { label: "ANALYZE", text: "LOCAL DATA · DOCUMENTS" },
  { label: "AUTOMATE", text: "WINDOWS · BROWSER" },
  { label: "VERIFY", text: "RESULT · FILE · STATE" },
  { label: "AUDIT", text: "FULL EXECUTION HISTORY" },
];

export default function Home() {
  return (
    <>
      {/* ============ HERO ============
          Fully choreographed (components/home/Hero.tsx): the intro film is a
          self-contained title card — "SyncNode / Think Locally, Act
          Intelligently" is baked into the footage. The page frames it with
          site-owned typography above and a transactional CTA band below. */}
      <Hero />

      {/* ============ INTRO STATEMENT (first scroll section) ============ */}
      <Section className="border-t border-line bg-ink-950">
        <div className="container-page">
          <div className="mx-auto max-w-3xl text-center">
            <Reveal y={16}>
              <div className="eyebrow mb-8">WHAT IS SYNCNODE</div>
            </Reveal>
            <h2 className="text-[clamp(1.8rem,3.8vw,3rem)] font-extralight leading-[1.25] tracking-tight text-fg-primary">
              <ChromaText>
                A sovereign AI workbench for confidential work — designed to
                understand locally, execute through controlled tools, verify
                outcomes, and keep sensitive work inside the environment you
                control.
              </ChromaText>
            </h2>
            <Reveal y={16} delay={0.15} className="mt-10">
              <MagneticButton to="/about" variant="secondary">
                EXPLORE SYNCNODE
                <ArrowRight className="h-4 w-4" />
              </MagneticButton>
            </Reveal>
          </div>
        </div>
      </Section>

      {/* ============ THE PROBLEM ============ */}
      <Section className="border-t border-line bg-ink-900/40">
        <div className="container-page">
          <SectionLabel>THE PROBLEM</SectionLabel>

          <h2 className="max-w-4xl text-[clamp(2rem,4.5vw,3.8rem)] font-extralight leading-[1.12] tracking-tight text-fg-primary">
            <ChromaText>
              Confidential work was never designed for a public AI endpoint.
            </ChromaText>
          </h2>

          <Reveal className="mt-8 max-w-2xl" y={20}>
            <p className="text-[15px] leading-[1.85] text-fg-mute">
              You type a question. It travels to a server farm in another
              jurisdiction. A model you don't control reads it — and a log of
              your most sensitive work sits on someone else's machine,
              indefinitely. For casual use, that's a trade-off. For
              engineering, legal, medical and project work, it isn't.
            </p>
          </Reveal>

          {/* Contrast diagram */}
          <div className="mt-20 grid gap-10 md:grid-cols-2 md:gap-16">
            <Reveal y={30} className="rounded-lg border border-line bg-ink-900/60 p-8 md:p-10">
              <div className="eyebrow mb-8 text-fg-faint">THE USUAL PATH</div>
              <div className="space-y-4 font-mono text-[13px] uppercase tracking-wider2">
                <div className="text-fg-mute">CONFIDENTIAL DATA</div>
                <FlowArrow />
                <div className="text-fg-mute">REMOTE AI</div>
                <FlowArrow />
                <div className="text-warn">LOSS OF CONTROL</div>
              </div>
            </Reveal>

            <Reveal
              y={30}
              delay={0.12}
              className="rounded-lg border border-line bg-ink-800 p-8 md:p-10"
            >
              <div className="eyebrow mb-8 text-fg-dim">THE SYNCNODE PATH</div>
              <div className="space-y-4 font-mono text-[13px] uppercase tracking-wider2">
                <div className="text-fg-mute">CONFIDENTIAL DATA</div>
                <FlowArrow />
                <div className="text-fg-primary">SYNCNODE</div>
                <FlowArrow />
                <div className="text-ok">LOCAL INTELLIGENCE</div>
              </div>
            </Reveal>
          </div>
        </div>
      </Section>

      {/* ============ CORE PRINCIPLE ============ */}
      <Section className="border-t border-line bg-ink-950">
        <div className="container-page">
          <div className="grid gap-16 lg:grid-cols-2">
            <div>
              <SectionLabel>THE CORE PRINCIPLE</SectionLabel>
              <h2 className="text-[clamp(2.2rem,5vw,4.2rem)] font-extralight leading-[1.05] tracking-tight text-fg-primary">
                <SplitText mode="rise">The model proposes.</SplitText>
                <br />
                <span className="text-fg-dim">
                  <SplitText mode="rise" delay={0.2}>
                    The system proves.
                  </SplitText>
                </span>
              </h2>
              <Reveal y={20} className="mt-8 max-w-lg">
                <p className="text-[15px] leading-[1.85] text-fg-mute">
                  The AI never writes to disk directly, never clicks a button,
                  never sends an email. It proposes a structured action.
                  SyncNode's runtime validates it, authorizes it, executes it
                  with a typed tool, observes the real result — and verifies.
                </p>
              </Reveal>
            </div>

            <div className="flex flex-col justify-center">
              {PRINCIPLE_STAGES.map((stage, i) => (
                <Reveal key={stage.label} y={18} delay={i * 0.06}>
                  <div className="group border-b border-line py-5">
                    <div className="flex items-baseline justify-between gap-6">
                      <span className="font-mono text-sm tracking-wider2 text-fg-primary">
                        {stage.label}
                      </span>
                      <span className="text-right text-[13px] text-fg-dim transition-colors group-hover:text-fg-mute">
                        {stage.note}
                      </span>
                    </div>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* ============ THINK / ACT / PROVE ============ */}
      <Section className="border-t border-line bg-ink-900/40">
        <div className="container-page">
          <SectionLabel>PRODUCT DIFFERENCE</SectionLabel>
          <SectionHeading className="mb-16 max-w-3xl text-[clamp(2rem,4vw,3.5rem)] font-extralight leading-[1.15] tracking-tight text-fg-primary">
            One workbench. Three disciplines.
          </SectionHeading>

          <div className="grid gap-6 lg:grid-cols-3">
            {THINK_ACT_PROVE.map((m, i) => (
              <Reveal key={m.id} y={48} delay={i * 0.12} className="h-full">
                <article className="group relative flex h-full flex-col rounded-lg border border-line bg-ink-800 p-8 transition-all duration-300 hover:-translate-y-1 hover:border-line-bright hover:bg-ink-700 md:p-10">
                  <div className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                    {String(i + 1).padStart(2, "0")} — {m.label}
                  </div>
                  <h3 className="mt-6 text-2xl font-light leading-snug tracking-tight text-fg-primary">
                    {m.title}
                  </h3>
                  <p className="mt-4 flex-1 text-[14px] leading-[1.8] text-fg-mute">
                    {m.body}
                  </p>
                  <ul className="mt-8 space-y-2.5 border-t border-line pt-6">
                    {m.points.map((p) => (
                      <li
                        key={p}
                        className="flex items-center gap-2.5 font-mono text-micro-sm uppercase tracking-wider2 text-fg-dim"
                      >
                        <svg
                          className="h-3 w-3 text-fg-mute"
                          viewBox="0 0 12 12"
                          fill="none"
                          aria-hidden="true"
                        >
                          <path d="M2 6.2 4.8 9 10 3.4" stroke="currentColor" strokeWidth="1.4" />
                        </svg>
                        {p}
                      </li>
                    ))}
                  </ul>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </Section>

      {/* ============ FROM GOAL TO RESULT ============ */}
      <Section className="border-t border-line bg-ink-950">
        <div className="container-page">
          <SectionLabel>THE WORKFLOW</SectionLabel>
          <SectionHeading className="mb-16 max-w-3xl text-[clamp(2rem,4vw,3.5rem)] font-extralight leading-[1.15] tracking-tight text-fg-primary">
            From a sentence to real work.
          </SectionHeading>

          <div className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-5">
            {FLOW_NODES.map((node, i) => (
              <Reveal key={node} y={20} delay={i * 0.05}>
                <div className="flex h-full flex-col justify-between gap-6 bg-ink-900 p-5 transition-colors duration-300 hover:bg-ink-700 md:p-6">
                  <span className="font-mono text-micro text-fg-faint">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="font-mono text-[11px] uppercase tracking-wider2 text-fg-body">
                    {node}
                  </span>
                </div>
              </Reveal>
            ))}
          </div>

          <Reveal y={16} className="mt-8">
            <p className="max-w-xl text-[14px] leading-relaxed text-fg-dim">
              Each stage is explicit, observable and recoverable. The full
              twelve-step sequence lives on the{" "}
              <a href="/workflow" className="text-fg-body underline-offset-4 hover:underline">
                workflow page
              </a>
              .
            </p>
          </Reveal>
        </div>
      </Section>

      {/* ============ LOCAL AI ============ */}
      <Section className="border-t border-line bg-ink-900/40">
        <div className="container-page">
          <div className="grid items-center gap-14 lg:grid-cols-2">
            <div>
              <SectionLabel>LOCAL INTELLIGENCE</SectionLabel>
              <SectionHeading className="mb-8 text-[clamp(2rem,4vw,3.2rem)] font-extralight leading-[1.12] tracking-tight text-fg-primary">
                Your AI. Your machine. Your data.
              </SectionHeading>
              <Reveal y={20} className="max-w-lg">
                <p className="text-[15px] leading-[1.85] text-fg-mute">
                  SyncNode is designed to operate without external AI APIs.
                  Inference happens on your hardware; retrieval happens on your
                  disk; the audit trail lives in your database.
                </p>
              </Reveal>
              <Reveal y={16} delay={0.1} className="mt-10 space-y-3">
                {[
                  ["LOCAL MODEL", "gemma4:e4b"],
                  ["LOCAL RUNTIME", "OLLAMA"],
                  ["CLOUD AI", "NOT REQUIRED"],
                ].map(([k, v]) => (
                  <div
                    key={k}
                    className="flex items-center justify-between border-b border-line pb-3 font-mono text-micro-sm uppercase tracking-wider2"
                  >
                    <span className="text-fg-dim">{k}</span>
                    <span className="text-fg-primary">{v}</span>
                  </div>
                ))}
              </Reveal>
            </div>

            <Reveal y={40} delay={0.1}>
              <div className="rounded-lg border border-line bg-ink-900 p-8 md:p-10">
                <div className="eyebrow mb-8">RUNTIME MAP</div>
                <div className="space-y-5 font-mono text-[12px]">
                  <div className="flex items-center gap-3">
                    <span className="h-2 w-2 rounded-full bg-fg-primary" aria-hidden="true" />
                    <span className="tracking-wider2 text-fg-primary">SYNCNODE</span>
                  </div>
                  <div className="ml-3 space-y-4 border-l border-line pl-6">
                    {["OLLAMA — LOCAL INFERENCE", "LOCAL DB — RUN STATE", "CHROMADB — KNOWLEDGE", "LOCAL FILES — ARTIFACTS"].map(
                      (s) => (
                        <div key={s} className="flex items-center gap-3">
                          <span className="h-1.5 w-1.5 rounded-full bg-fg-mute" aria-hidden="true" />
                          <span className="tracking-wider2 text-fg-mute">{s}</span>
                        </div>
                      )
                    )}
                    <div className="flex items-center gap-3 pt-2">
                      <span className="font-mono text-warn">✕</span>
                      <span className="tracking-wider2 text-fg-faint line-through">
                        EXTERNAL AI API
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </Reveal>
          </div>
        </div>
      </Section>

      {/* ============ REAL WORK ============ */}
      <Section className="border-t border-line bg-ink-950">
        <div className="container-page">
          <SectionLabel>REAL WORK</SectionLabel>
          <SectionHeading className="mb-16 max-w-3xl text-[clamp(2rem,4vw,3.5rem)] font-extralight leading-[1.15] tracking-tight text-fg-primary">
            Not answers. Artifacts.
          </SectionHeading>

          <div className="space-y-px overflow-hidden rounded-lg border border-line bg-line">
            {REAL_WORK.map((w, i) => (
              <Reveal key={w.label} y={20} delay={i * 0.05}>
                <div className="group flex flex-col gap-3 bg-ink-900 px-6 py-7 transition-colors hover:bg-ink-800 sm:flex-row sm:items-center sm:gap-8 md:px-10">
                  <span className="w-28 shrink-0 font-mono text-micro-sm uppercase tracking-wider2 text-fg-primary">
                    {w.label}
                  </span>
                  <span className="font-mono text-micro-sm uppercase tracking-wider2 text-fg-dim">
                    {w.text}
                  </span>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </Section>

      {/* ============ INDUSTRIAL CONTEXT ============ */}
      <Section className="border-t border-line bg-ink-900/40">
        <div className="container-page">
          <SectionLabel>INDUSTRIAL CONTEXT</SectionLabel>
          <h2 className="max-w-4xl text-[clamp(1.9rem,4vw,3.4rem)] font-extralight leading-[1.15] tracking-tight text-fg-primary">
            <ChromaText>
              Built for work where "just upload it" is not an option.
            </ChromaText>
          </h2>
          <Reveal y={20} className="mt-8 max-w-2xl">
            <p className="text-[15px] leading-[1.85] text-fg-mute">
              Engineering documentation. Inspection records. Project packages.
              Procurement submissions. Internal manuals. The work that powers
              real organizations is exactly the work that cannot be pasted into
              a public chat box.
            </p>
          </Reveal>

          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              ["Engineering", "Inspection data, calculations, technical reports"],
              ["Maintenance", "History review, corrective-action preparation"],
              ["Projects", "Packages, progress analysis, engineering notes"],
              ["Procurement", "Specification comparison, submission review"],
              ["R&D", "Data analysis, sandboxed calculation"],
              ["Document work", "Word, Excel, PowerPoint — generated and verified"],
            ].map(([t, d], i) => (
              <Reveal key={t} y={24} delay={i * 0.05}>
                <div className="h-full rounded-lg border border-line bg-ink-900 p-6 transition-colors hover:border-line-bright">
                  <div className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
                    {String(i + 1).padStart(2, "0")}
                  </div>
                  <div className="mt-3 text-[15px] text-fg-primary">{t}</div>
                  <div className="mt-1.5 text-[13px] leading-relaxed text-fg-dim">{d}</div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </Section>

      {/* ============ FINAL CTA ============ */}
      <section className="relative overflow-hidden border-t border-line">
        <div
          aria-hidden="true"
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 70% 55% at 50% 100%, #161616 0%, #080808 65%)",
          }}
        />
        <div className="container-page relative z-10 py-32 text-center md:py-44">
          <h2 className="text-[clamp(2.4rem,6vw,5rem)] font-extralight leading-[1.04] tracking-tight text-fg-primary">
            <SplitText mode="rise">Give local AI a way to act.</SplitText>
          </h2>
          <Reveal y={18} className="mx-auto mt-7 max-w-xl">
            <p className="text-[15px] leading-relaxed text-fg-mute">
              Run SyncNode on Windows and bring local intelligence, controlled
              execution and verification into one workbench.
            </p>
          </Reveal>
          <Reveal y={18} delay={0.1} className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <MagneticButton to="/download" variant="primary" size="lg">
              <Download className="h-4 w-4" />
              DOWNLOAD FOR WINDOWS
            </MagneticButton>
            <MagneticButton href={GITHUB_URL} external variant="secondary" size="lg">
              <Github className="h-4 w-4" />
              VIEW ON GITHUB
            </MagneticButton>
          </Reveal>
        </div>
      </section>
    </>
  );
}

function FlowArrow() {
  return (
    <div aria-hidden="true" className="flex items-center gap-3 text-fg-faint">
      <span className="h-px w-10 bg-line" />
      <span className="text-[10px]">↓</span>
      <span className="h-px flex-1 bg-line" />
    </div>
  );
}
