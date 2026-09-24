# SyncNode Features

## Core capabilities

### Fully offline — no cloud required

SyncNode runs entirely on your local machine. After the initial model download, it operates with zero internet connectivity. Your goals, your documents, your conversation history, and your execution logs never leave your device.

No API keys. No subscriptions. No data retention policies to read. No usage logs on a remote server.

### Local model inference (Ollama + Gemma 4)

SyncNode uses [Ollama](https://ollama.com) to run Google Gemma 4 locally. The default model — `gemma4:e4b` — is a quantized 8B-parameter model that runs well on a mid-range NVIDIA GPU (4 GB+ VRAM recommended).

- **128,000 token context window** — handles long documents and multi-step workflows
- **Vision support** — can observe screenshots and describe UI state
- **Structured output** — produces typed JSON for every planning and tool-calling step
- **Q4_K_M quantization** — ~9.6 GB download, balanced quality and speed
- **CPU fallback** — runs on any machine, GPU just makes it faster

### Multi-agent coordination

SyncNode doesn't use one monolithic agent. It spawns specialized agents for different parts of a workflow:

| Agent | Responsibility |
|---|---|
| **Supervisor** | Coordinates the overall plan, dispatches to specialists |
| **Writer** | Generates document content, paragraphs, summaries |
| **Document** | Creates and manages Word/Excel/PowerPoint files |
| **Office** | Live interaction with open Office applications |
| **Computer** | Windows UI Automation — taskbar, apps, controls |
| **Browser** | Playwright-based web navigation and form filling |
| **Verifier** | Post-condition assertions on every completed step |
| **Recovery** | Re-observation, retry, and re-planning after failures |

Agents run in parallel where dependencies allow. The LangGraph DAG executes waves of independent steps simultaneously.

### 44 deterministic tools

Every action the AI wants to take is implemented as a typed, schema-validated tool:

**Document tools** — create Word documents with real paragraphs, formatting, and styles; read existing files; write and append content; list directories.

**Excel tools** — create workbooks, add named sheets, write header rows and data rows, format cells, verify content.

**PowerPoint tools** — create presentations, add title slides, content slides, and summary slides; format text and layout.

**Computer tools** — search the Windows taskbar, open applications, click UI elements by role or name, type text into active windows, take screenshots, read clipboard.

**Browser tools** — navigate Chromium, fill form fields by label or role, click buttons, attach local files to upload inputs, read page content, take browser screenshots.

**System tools** — run PowerShell commands, list running processes, read environment variables, search the filesystem, read file content.

### Post-condition verification

After every tool call, SyncNode runs assertions against the real system state:

- **File assertions** — does the file exist? Does it have the expected content? Is the size non-zero?
- **Process assertions** — is the application running? Is the expected window title present?
- **UI assertions** — is the control visible? Does the field contain the expected value?
- **Browser assertions** — did the page load? Is the form field filled? Is the attachment present?

If an assertion fails, the step is marked failed — not retried with fingers crossed. The recovery agent re-observes the actual state and decides whether to retry, re-plan, or surface the failure to you.

### SHA-256 audit chain

Every event in SyncNode — every intent extraction, every tool call, every verification result, every approval decision — is written to an immutable audit log with a SHA-256 hash chained to the previous event.

You can prove:
- What goal was submitted
- What the AI planned
- Which tools were called and with what arguments
- What the tools returned
- Whether verification passed or failed
- Who approved what and when
- The final outcome

This is not a log file that can be quietly edited. The hash chain makes tampering detectable.

### Human approval gate

SyncNode will not send an email, delete a file, or take any external/destructive action without pausing and asking you first.

When the workflow reaches a step classified as `EXTERNAL_COMMUNICATION` or `DESTRUCTIVE_LOCAL`, it stops, presents you with:
- A summary of what it wants to do
- The target (recipient, file path, etc.)
- The full context of what led to this point
- The artifacts it has prepared

You can approve or reject. If you reject, the run records your decision and stops cleanly.

### Workflow memory and learning

When a run completes successfully, SyncNode records the workflow pattern in its local knowledge base. Future runs on similar goals can reference these patterns to plan more efficiently and avoid previously-seen failure modes.

This is local, private, and audited. No cloud sync, no anonymous telemetry.

### Electron desktop app

SyncNode ships as a full desktop application built on Electron + React 18:

- **Workbench layout** — left rail navigation, primary work surface, right inspector panel
- **Live run view** — watch the agent execute step by step in real time via SSE
- **Agent inspector** — see which agents are active, what they're doing, their tool calls and results
- **Artifact evidence** — every generated file traced back to the step and agent that created it
- **Approval panels** — review and decide on approval requests without leaving the app
- **Knowledge base** — browse, search, and inspect your local RAG index
- **Audit explorer** — filter and search the full event history for any run
- **Settings** — configure model, GPU, paths, and appearance

---

## Technical highlights

- **FastAPI + asyncio** — non-blocking request handling for long-running workflows
- **LangGraph** — directed graph execution with node-level retries and conditional edges
- **aiosqlite** — durable async SQLite for all run state
- **ChromaDB** — local vector store for offline RAG with `all-MiniLM-L6-v2` embeddings
- **Playwright** — headless and headed Chromium automation
- **pywin32 / UIAutomation** — Windows UIA tree traversal for desktop control
- **python-docx / openpyxl / python-pptx** — deterministic Office document generation
- **PyInstaller** — packages the entire backend into a standalone Windows executable
- **NSIS via Electron Builder** — single-file Windows installer

---

## What SyncNode does not do

Being honest about scope is part of building trust:

- Does not train or fine-tune models
- Does not browse arbitrary websites autonomously (Playwright is used for specific, planned navigation)
- Does not bypass UAC, handle CAPTCHAs, or take actions requiring administrator elevation
- Does not control another user's desktop
- Does not send emails or messages without your explicit approval
- Does not require or use any cloud AI API
- Does not collect usage data or telemetry to any external service
