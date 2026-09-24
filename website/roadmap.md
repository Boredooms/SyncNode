# SyncNode Roadmap

## Current release — v1.0 (2026)

The first public release establishes the core sovereign AI workbench.

### What shipped in v1.0

**Runtime**
- [x] FastAPI backend with full async execution
- [x] LangGraph orchestrator with DAG-based task decomposition
- [x] Intent extraction with structured output validation
- [x] Multi-agent registry (Supervisor, Writer, Document, Office, Computer, Browser, Verifier, Recovery)
- [x] 44 deterministic tools across 5 categories
- [x] Post-condition verification engine with real assertions
- [x] SHA-256 audit chain (immutable event log)
- [x] Human approval gate for external/destructive actions
- [x] Recovery and re-planning after tool failures
- [x] Workflow memory and learning layer
- [x] ChromaDB RAG with offline embeddings

**Model layer**
- [x] Ollama adapter (provider-agnostic model gateway)
- [x] Gemma 4 (gemma4:e4b) as primary model
- [x] Vision support for screenshot observation
- [x] Structured output with repair loop (up to 3 attempts)
- [x] Token budget management and context compaction

**Desktop**
- [x] Windows UIA desktop control
- [x] Playwright-based Chromium automation
- [x] Word, Excel, PowerPoint generation tools
- [x] System tools (shell, process, filesystem)

**Frontend**
- [x] Electron desktop application
- [x] React 18 + TypeScript + Tailwind
- [x] Live SSE run streaming
- [x] Workbench layout with left rail + inspector
- [x] Run creation, history, and detail views
- [x] Agent timeline and tool lifecycle view
- [x] Artifact evidence chain
- [x] Approval panels
- [x] Knowledge base browser
- [x] Audit event explorer
- [x] Settings screen

---

## Near-term — v1.1 (Q4 2026)

Focus: **reliability, polish, and broader model support**

- [ ] Ollama model switcher in the UI (switch between local models without restarting)
- [ ] Improved recovery strategies — smarter re-observation before re-planning
- [ ] Richer verification — OCR-based text verification in screenshots
- [ ] Parallel tool execution display in the timeline
- [ ] Better empty/error states throughout the frontend
- [ ] Keyboard-first navigation improvements
- [ ] Run templates — save a goal as a reusable template
- [ ] Export audit log as PDF/JSON
- [ ] Windows installer auto-update mechanism

---

## Medium-term — v1.2 (Q1 2027)

Focus: **knowledge work depth and document intelligence**

- [ ] PDF ingestion and semantic extraction into ChromaDB
- [ ] Local OCR for scanned documents (Tesseract integration)
- [ ] Richer Word document formatting (tables, headers, styles)
- [ ] Excel formula support and chart generation
- [ ] PowerPoint layout intelligence (content-aware slide design)
- [ ] File watcher — auto-ingest new documents into knowledge base
- [ ] Full-text search across run history and artifacts

---

## Longer-term — v2.0

Focus: **multi-workspace, network isolation, and enterprise readiness**

- [ ] PostgreSQL backend option for multi-user/server deployments
- [ ] Role-based access control (admin, operator, reviewer, viewer)
- [ ] Network-isolated deployment mode (no localhost assumptions)
- [ ] Multi-model routing — route different task types to different local models
- [ ] Visual workflow builder — construct task graphs with drag-and-drop
- [ ] Plugin architecture — load additional tool packages at runtime
- [ ] Automatic workflow optimization based on memory patterns
- [ ] macOS and Linux support (via cross-platform Playwright + UIA alternatives)

---

## Never (out of scope)

These are explicitly not planned:

- Cloud AI API integration (this defeats the purpose)
- Sending emails or messages without human approval
- Unrestricted autonomous web browsing
- UAC bypass or administrator elevation
- CAPTCHA solving or anti-bot bypass
- Training or fine-tuning models locally
- Cross-user desktop control

---

## Feedback

The roadmap is shaped by real use. If you have a use case that SyncNode almost handles but doesn't quite, open an issue or discussion on [GitHub](https://github.com/Boredooms/SyncNode).
