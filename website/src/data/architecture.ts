export type ArchNode = {
  id: string;
  name: string;
  role: string;
  input: string;
  output: string;
  tech: string;
  layer: number;
};

/**
 * Layered architecture. `layer` groups nodes into visual rows;
 * edges are derived from layer order for the connection lines.
 */
export const architectureNodes: ArchNode[] = [
  {
    id: "user",
    name: "USER",
    role: "States a goal in natural language and approves critical actions",
    input: "Plain-language goal",
    output: "Approved plan · decisions",
    tech: "SyncNode Workbench (Electron)",
    layer: 0,
  },
  {
    id: "workbench",
    name: "ELECTRON WORKBENCH",
    role: "Desktop surface for runs, agents, artifacts and approvals",
    input: "User goals",
    output: "Run requests · SSE event stream",
    tech: "Electron · React 18 · TypeScript",
    layer: 1,
  },
  {
    id: "api",
    name: "API",
    role: "Non-blocking HTTP surface; streams live run events",
    input: "Run requests",
    output: "Run IDs · SSE events",
    tech: "FastAPI · asyncio",
    layer: 2,
  },
  {
    id: "orchestrator",
    name: "ORCHESTRATOR",
    role: "Decomposes goals into a DAG and executes it node by node",
    input: "Validated intent",
    output: "Step dispatch · state transitions",
    tech: "LangGraph",
    layer: 3,
  },
  {
    id: "model-router",
    name: "MODEL ROUTER",
    role: "Chooses the right local model for each task and keeps outputs structured",
    input: "Step requests",
    output: "Typed model responses",
    tech: "Ollama · gemma4:e4b · gemma3:1b",
    layer: 4,
  },
  {
    id: "knowledge",
    name: "KNOWLEDGE",
    role: "Local RAG — retrieval with sources, plus workflow memory",
    input: "Queries",
    output: "Grounded context chunks",
    tech: "ChromaDB · all-MiniLM-L6-v2",
    layer: 4,
  },
  {
    id: "supervisor",
    name: "SUPERVISOR",
    role: "Coordinates the plan and dispatches specialist agents",
    input: "Grounded plan",
    output: "Agent assignments",
    tech: "LangGraph supervisor node",
    layer: 5,
  },
  {
    id: "agents",
    name: "AGENTS",
    role: "Specialists — Writer, Document, Office, Computer, Browser, Verifier, Recovery",
    input: "Step assignments",
    output: "Tool call proposals",
    tech: "Typed agent registry",
    layer: 6,
  },
  {
    id: "tools",
    name: "TOOLS",
    role: "44 schema-validated, deterministic actions",
    input: "Proposed calls",
    output: "Validated executions",
    tech: "python-docx · openpyxl · UIA · Playwright",
    layer: 7,
  },
  {
    id: "execution",
    name: "EXECUTION",
    role: "Performs the action on the real machine — files, desktop, browser",
    input: "Validated calls",
    output: "Real system effects",
    tech: "Windows · Chromium",
    layer: 8,
  },
  {
    id: "observation",
    name: "OBSERVATION",
    role: "Captures actual post-action state — paths, titles, screenshots",
    input: "System state",
    output: "Structured evidence",
    tech: "UIA tree · screenshots · fs stat",
    layer: 9,
  },
  {
    id: "verification",
    name: "VERIFICATION",
    role: "Runs post-condition assertions against the evidence",
    input: "Observations",
    output: "Pass / fail verdicts",
    tech: "Assertion engine",
    layer: 10,
  },
  {
    id: "recovery",
    name: "RECOVERY",
    role: "Re-observes, retries, or re-plans when verification fails",
    input: "Failed verdicts",
    output: "Retry · re-plan · escalate",
    tech: "Recovery agent · retry limits",
    layer: 11,
  },
  {
    id: "approval",
    name: "APPROVAL",
    role: "Pauses external/destructive steps for a human decision",
    input: "Risky step context",
    output: "Approve / reject",
    tech: "Policy classification",
    layer: 12,
  },
  {
    id: "audit",
    name: "AUDIT",
    role: "Records every event in an immutable SHA-256 chain",
    input: "All events",
    output: "Tamper-evident history",
    tech: "SHA-256 chained log",
    layer: 13,
  },
  {
    id: "memory",
    name: "MEMORY",
    role: "Retains successful workflow patterns for future runs",
    input: "Completed plans",
    output: "Reusable patterns",
    tech: "ChromaDB collections",
    layer: 13,
  },
];

/** Sequential main flow used for the animated chain on other pages. */
export const mainChain = [
  "USER",
  "ELECTRON",
  "API",
  "ORCHESTRATOR",
  "MODEL ROUTER",
  "KNOWLEDGE",
  "SUPERVISOR",
  "AGENTS",
  "TOOLS",
  "EXECUTION",
  "OBSERVATION",
  "VERIFICATION",
  "RECOVERY",
  "APPROVAL",
  "AUDIT",
  "MEMORY",
] as const;
