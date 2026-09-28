export type RoadmapStatus = "BUILT" | "INTEGRATING" | "PLANNED";

export type RoadmapItem = { text: string };
export type RoadmapPhase = {
  id: string;
  version: string;
  title: string;
  status: RoadmapStatus;
  focus: string;
  items: RoadmapItem[];
};

export const roadmapPhases: RoadmapPhase[] = [
  {
    id: "v1",
    version: "v1.0",
    title: "Local Core",
    status: "BUILT",
    focus: "The sovereign workbench foundation",
    items: [
      { text: "FastAPI backend with full async execution" },
      { text: "LangGraph orchestrator with DAG-based decomposition" },
      { text: "8 specialist agents — Supervisor through Recovery" },
      { text: "44 deterministic tools across 5 categories" },
      { text: "Post-condition verification engine" },
      { text: "SHA-256 immutable audit chain" },
      { text: "Human approval gate for external actions" },
      { text: "ChromaDB RAG with offline embeddings" },
      { text: "Electron desktop application with live run view" },
    ],
  },
  {
    id: "v11",
    version: "v1.1",
    title: "Agentic Workbench",
    status: "INTEGRATING",
    focus: "Reliability, polish, broader model support",
    items: [
      { text: "Ollama model switcher in the UI" },
      { text: "Smarter recovery — re-observation before re-planning" },
      { text: "OCR-based verification in screenshots" },
      { text: "Parallel tool execution in the timeline" },
      { text: "Run templates — save a goal as a reusable pattern" },
      { text: "Export audit log as PDF / JSON" },
      { text: "Installer auto-update mechanism" },
    ],
  },
  {
    id: "v12",
    version: "v1.2",
    title: "Multimodal & Knowledge",
    status: "PLANNED",
    focus: "Document intelligence depth",
    items: [
      { text: "PDF ingestion and semantic extraction into ChromaDB" },
      { text: "Local OCR for scanned documents" },
      { text: "Richer Word formatting — tables, headers, styles" },
      { text: "Excel formula support and chart generation" },
      { text: "File watcher — auto-ingest new documents" },
      { text: "Full-text search across run history" },
    ],
  },
  {
    id: "v2",
    version: "v2.0",
    title: "Sandboxed Computation",
    status: "PLANNED",
    focus: "Analysis depth for technical work",
    items: [
      { text: "Sandboxed numeric computation environment" },
      { text: "Content-aware PowerPoint layout intelligence" },
      { text: "Visual workflow builder — drag-and-drop task graphs" },
      { text: "Plugin architecture for runtime tool packages" },
      { text: "Automatic workflow optimization from memory patterns" },
    ],
  },
  {
    id: "enterprise",
    version: "v2.x",
    title: "Industrial Deployment",
    status: "PLANNED",
    focus: "Enterprise readiness",
    items: [
      { text: "PostgreSQL backend option for multi-user deployments" },
      { text: "Role-based access control" },
      { text: "Network-isolated deployment mode" },
      { text: "Multi-model routing by task type" },
      { text: "macOS and Linux support" },
    ],
  },
];

export const neverList = [
  "Cloud AI API integration — it defeats the purpose",
  "Sending email or messages without human approval",
  "Unrestricted autonomous web browsing",
  "UAC bypass or administrator elevation",
  "CAPTCHA solving or anti-bot bypass",
  "Training or fine-tuning models",
  "Cross-user desktop control",
];
