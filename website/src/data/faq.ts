export type FaqItem = { q: string; a: string };
export type FaqGroup = { group: string; items: FaqItem[] };

export const faqGroups: FaqGroup[] = [
  {
    group: "General",
    items: [
      {
        q: "What is SyncNode?",
        a: "SyncNode is a local AI automation workbench for Windows. You give it a natural-language goal — \"create a quarterly report and prepare an email with the files attached\" — and it executes that goal using specialized AI agents, real Windows automation tools, and a local LLM running on your GPU. Nothing leaves your machine.",
      },
      {
        q: "Does it require an internet connection?",
        a: "Only for the initial model download via Ollama. Once the models are downloaded, SyncNode runs entirely offline. All inference, file operations, and automation are local.",
      },
      {
        q: "Is it free?",
        a: "The software is currently proprietary. Check the GitHub releases page for the current distribution terms.",
      },
      {
        q: "What Windows versions does it support?",
        a: "Windows 10 x64 and Windows 11 x64. Windows 11 is recommended for the best Windows UI Automation coverage.",
      },
    ],
  },
  {
    group: "Hardware & models",
    items: [
      {
        q: "What GPU do I need?",
        a: "Any GPU works — SyncNode falls back to CPU if no GPU is available. For a usable experience, an NVIDIA GPU with 4 GB+ VRAM is recommended. An RTX 2050 or better handles the default gemma4:e4b model well.",
      },
      {
        q: "What model does SyncNode use?",
        a: "The default is gemma4:e4b — Google's Gemma 4 model, 8 billion parameters, quantized to Q4_K_M, running via Ollama. It has a 128,000-token context window, vision support, and structured output capability. A smaller gemma3:1b model handles enrichment and summarization.",
      },
      {
        q: "Can I use a different model?",
        a: "Yes. The model gateway is provider-agnostic. Any model available in your local Ollama instance can be configured. The model needs structured output support for the planner to work correctly.",
      },
      {
        q: "How much storage does it need?",
        a: "The Gemma 4 model is ~9.6 GB. The application itself and its dependencies are under 1 GB. Allow 20 GB total for models, dependencies, and working data.",
      },
      {
        q: "How long does a workflow take?",
        a: "Depends on the GPU and the complexity of the goal. A simple 3-step document creation workflow typically takes 2–4 minutes on an RTX 2050. A complex 12-step workflow with Office automation and browser control takes 8–15 minutes.",
      },
    ],
  },
  {
    group: "Privacy & security",
    items: [
      {
        q: "Does SyncNode send any data to external servers?",
        a: "No. When Ollama is configured for local-only operation (the default), all model inference is local. The application itself makes no outbound network requests. Your goals, documents, and run history stay on your machine.",
      },
      {
        q: "Can the AI send emails or delete files without my permission?",
        a: "No. SyncNode has a mandatory approval gate for any action classified as EXTERNAL_COMMUNICATION (sending messages, emails) or DESTRUCTIVE_LOCAL (deleting files). When the workflow reaches such a step, it pauses and presents you with a summary. You must explicitly approve before execution continues.",
      },
      {
        q: "Is there an audit log?",
        a: "Yes. Every event — intent extraction, tool call, verification result, approval decision — is recorded in an immutable audit chain with SHA-256 hashes linking each event to the previous one. You can query the full audit history from the frontend or the API.",
      },
      {
        q: "Can the AI access any file on my machine?",
        a: "SyncNode's system tools can read and write files. The scope is controlled by the tool policy configuration. By default, tools operate within the configured workspace root. Sensitive operations follow the same approval policy as other high-risk actions.",
      },
    ],
  },
  {
    group: "How it works",
    items: [
      {
        q: "What is a \"run\"?",
        a: "A run is one execution of a goal. It has an ID, a status, a set of steps, and an audit log. Runs are durable — they survive application restarts. You can view all past runs, their steps, artifacts, and audit events in the frontend.",
      },
      {
        q: "What is \"verification\"?",
        a: "After every tool call, SyncNode runs assertions against the real system state. After creating a Word document, it checks that the file exists on disk and is non-empty. After opening an application, it checks that the process is running and the window title is present. If an assertion fails, the step is marked failed — not silently retried.",
      },
      {
        q: "What happens when a step fails?",
        a: "The Recovery agent re-observes the actual state of the system and decides whether to retry with the same approach, retry with a modified approach, or escalate to a re-plan. There are explicit retry limits — no infinite loops.",
      },
      {
        q: "What is \"workflow memory\"?",
        a: "When a run completes successfully, SyncNode records the plan pattern in its local ChromaDB knowledge base. Future runs on similar goals can retrieve this pattern and plan more efficiently. This is entirely local and private.",
      },
      {
        q: "What is LangGraph?",
        a: "LangGraph is the execution engine behind SyncNode's orchestrator. It models the workflow as a directed graph where each node is a step and edges represent transitions between states. This enables parallel execution of independent steps and conditional branching for recovery.",
      },
    ],
  },
  {
    group: "Troubleshooting",
    items: [
      {
        q: "The model takes a long time to load",
        a: "On the first call after startup, the model needs to load into GPU memory. This can take 30–60 seconds on a cold start. The startup scripts set OLLAMA_LOAD_TIMEOUT=300s to give it enough time.",
      },
      {
        q: "I see \"GPU discovery watchdog timed out\"",
        a: "This usually happens on systems with both a discrete NVIDIA GPU and an Intel integrated GPU. The startup scripts set CUDA_VISIBLE_DEVICES=0 and OLLAMA_IGPU_ENABLE=0 to resolve this. If you're starting Ollama manually, set those environment variables yourself.",
      },
      {
        q: "A run is stuck in \"planning\" status",
        a: "Check the backend logs. The most common cause is the model producing malformed JSON. The repair loop retries up to 3 times. If all attempts fail, the run is marked failed with a StructuredOutputError message.",
      },
      {
        q: "The browser automation isn't working",
        a: "Make sure Playwright's Chromium is installed: playwright install chromium. The browser tools require Chromium to be available.",
      },
      {
        q: "Where are my generated files?",
        a: "By default, all run artifacts are saved to C:\\syncnode\\workspace\\. You can configure this with SYNCNODE_WORKSPACE_ROOT in your .env file.",
      },
    ],
  },
];
