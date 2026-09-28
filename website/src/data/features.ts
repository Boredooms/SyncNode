export type FeatureFamily = {
  id: string;
  label: string;
  title: string;
  summary: string;
  why: string;
  how: string;
  detail: string;
  capabilities: string[];
};

export const featureFamilies: FeatureFamily[] = [
  {
    id: "local-intelligence",
    label: "LOCAL INTELLIGENCE",
    title: "A model that lives on your GPU",
    summary:
      "SyncNode runs Google Gemma 4 locally through Ollama — a quantized 8B model with a 128k context window, vision support and structured output. No API key, no metered tokens.",
    why: "Confidential reasoning should never depend on someone else's uptime — or someone else's log retention.",
    how: "The model gateway is provider-agnostic. Any model in your local Ollama instance can be configured; the planner only asks for structured output support.",
    detail: "gemma4:e4b · Q4_K_M · 128k context · CPU fallback",
    capabilities: [
      "Local inference via Ollama",
      "Model routing by task type",
      "128,000-token context window",
      "Vision — reads screenshots and UI state",
      "Structured JSON output with repair loop",
    ],
  },
  {
    id: "local-knowledge",
    label: "LOCAL KNOWLEDGE",
    title: "RAG that never phones home",
    summary:
      "Documents are embedded and indexed into a local ChromaDB vector store. Retrieval happens on your disk, with source attribution on every answer.",
    why: "A knowledge base you cannot audit is a knowledge base you cannot trust.",
    how: "all-MiniLM-L6-v2 embeddings run locally. Queries return the most relevant chunks with their sources, and the model grounds its answer in them.",
    detail: "ChromaDB · all-MiniLM-L6-v2 · offline indexing",
    capabilities: [
      "Offline document ingestion",
      "Local vector search with sources",
      "Grounded answers, less hallucination",
      "Workflow memory — successful patterns are retained",
    ],
  },
  {
    id: "agentic-work",
    label: "AGENTIC WORK",
    title: "Specialists, not a monolith",
    summary:
      "A supervisor decomposes your goal and dispatches specialist agents — Writer, Document, Office, Computer, Browser, Verifier, Recovery. Independent steps run in parallel.",
    why: "One model wearing every hat makes every mistake. Specialists keep each step small, testable and recoverable.",
    how: "A LangGraph DAG models the workflow. Nodes execute in waves; edges carry state; conditional branches handle recovery.",
    detail: "LangGraph DAG · 8 agent types · parallel waves",
    capabilities: [
      "Supervisor planning and dispatch",
      "Parallel execution of independent steps",
      "Typed agent responsibilities",
      "Re-planning when conditions change",
    ],
  },
  {
    id: "real-execution",
    label: "REAL EXECUTION",
    title: "44 typed tools. Real desktop.",
    summary:
      "Every action is a schema-validated tool — Word, Excel, PowerPoint, Windows UI automation, Chromium, PowerShell. The model proposes a call; the runtime executes it.",
    why: "Free-form shell access is how agents break machines. Typed tools make every action inspectable before it happens.",
    how: "Tools validate arguments against schemas, run deterministically, and return structured observations the model can reason over.",
    detail: "python-docx · openpyxl · UIA · Playwright",
    capabilities: [
      "Office documents — Word, Excel, PowerPoint",
      "Windows UI automation (UIA tree)",
      "Browser automation (Playwright / Chromium)",
      "System tools — shell, processes, filesystem",
    ],
  },
  {
    id: "trust",
    label: "TRUST",
    title: "Verification, approval, audit",
    summary:
      "After every tool call the runtime asserts against the real system state. External or destructive actions pause for your approval. Every event lands in a SHA-256 audit chain.",
    why: "The failure mode that matters is not a wrong answer — it is a false success.",
    how: "Post-condition assertions check files, processes, UI state and pages. The approval gate classifies risky steps and stops. The audit chain makes tampering detectable.",
    detail: "SHA-256 chained events · approval gate · assertions",
    capabilities: [
      "Post-condition verification on every step",
      "Recovery agent — retry, re-observe, re-plan",
      "Human approval gate for external actions",
      "Immutable SHA-256 audit trail",
    ],
  },
];
