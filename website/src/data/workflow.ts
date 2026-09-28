export type WorkflowStage = {
  index: string;
  id: string;
  title: string;
  line: string;
  body: string;
};

export const workflowStages: WorkflowStage[] = [
  {
    index: "01",
    id: "understand",
    title: "UNDERSTAND",
    line: "The goal is parsed into a structured intent.",
    body: "Your sentence becomes typed parameters — entities, constraints, deliverables. The model extracts intent with structured output; malformed plans are repaired, not guessed.",
  },
  {
    index: "02",
    id: "retrieve",
    title: "RETRIEVE",
    line: "Local knowledge is pulled into context.",
    body: "The RAG layer searches your local ChromaDB index and returns relevant chunks with sources. The model grounds its plan in your documents, not its imagination.",
  },
  {
    index: "03",
    id: "plan",
    title: "PLAN",
    line: "The supervisor decomposes work into a DAG.",
    body: "The goal becomes a directed graph of steps with explicit dependencies. Independent steps are marked for parallel execution. The plan is visible before anything runs.",
  },
  {
    index: "04",
    id: "select",
    title: "SELECT",
    line: "The right specialist takes each step.",
    body: "Each step is matched to an agent — Writer for prose, Document for Office files, Computer for the desktop, Browser for the web. Every tool call is typed and schema-validated.",
  },
  {
    index: "05",
    id: "authorize",
    title: "AUTHORIZE",
    line: "Policy decides what is permitted.",
    body: "Steps classified as external communication or destructive local action stop here. You see the full context — what, where, why — and you decide.",
  },
  {
    index: "06",
    id: "execute",
    title: "EXECUTE",
    line: "Typed tools act on the real machine.",
    body: "The runtime executes validated tool calls — creating files, opening applications, filling forms. The model never touches the machine directly; the executor does.",
  },
  {
    index: "07",
    id: "observe",
    title: "OBSERVE",
    line: "Reality is recorded, not assumed.",
    body: "After each action the runtime captures the actual state — file paths and sizes, process lists, window titles, screenshots, page state. Observation is evidence.",
  },
  {
    index: "08",
    id: "verify",
    title: "VERIFY",
    line: "Assertions run against what actually happened.",
    body: "Post-conditions check that the file exists and is non-empty, that the window is present, that the form field holds the expected value. Failure is marked honestly.",
  },
  {
    index: "09",
    id: "recover",
    title: "RECOVER",
    line: "Failures trigger re-observation, not hope.",
    body: "If verification fails, the recovery agent re-reads the real state and chooses: retry as-is, retry modified, or escalate to re-plan. Retry limits prevent loops.",
  },
  {
    index: "10",
    id: "approve",
    title: "APPROVE",
    line: "You sign off before anything leaves.",
    body: "At the approval gate the run pauses with a complete summary — target, attachments, context. Approve, or reject; the decision is recorded either way.",
  },
  {
    index: "11",
    id: "deliver",
    title: "DELIVER",
    line: "Artifacts are traced to their origin.",
    body: "Every generated file links back to the step and agent that created it. You receive the deliverable plus the evidence that it is what was asked for.",
  },
  {
    index: "12",
    id: "remember",
    title: "REMEMBER",
    line: "Successful patterns are kept locally.",
    body: "Completed workflows are recorded as patterns in local memory. Future runs on similar goals start smarter — and the memory itself stays private and auditable.",
  },
];
