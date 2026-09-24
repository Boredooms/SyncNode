# SyncNode Press Kit

## One-line description

SyncNode is a sovereign, fully offline AI automation workbench for Windows that turns natural-language goals into verified, audited workflows — running entirely on your GPU.

## Short description (50 words)

SyncNode is a local-first AI workbench for Windows. Give it a goal in plain language and it plans, executes, verifies, and audits the entire workflow — creating documents, controlling your desktop, automating browsers, and composing emails — without sending a single byte to the cloud.

## Long description (150 words)

SyncNode is a sovereign AI automation workbench built for Windows. It runs entirely on your local machine, powered by Google Gemma 4 via Ollama, with no cloud dependencies, no API keys, and no data leaving your device.

You give SyncNode a natural-language goal. It extracts your intent, decomposes it into steps using a LangGraph execution engine, dispatches specialized agents (Writer, Document, Computer, Browser, Verifier), and executes 44 typed tools against your real Windows desktop. After every action, it verifies the result with post-condition assertions. If a step fails, the Recovery agent re-plans. When a workflow reaches an external action — like sending an email — it stops and waits for your approval.

Every event is recorded in an immutable SHA-256 audit chain. Every generated file is traced back to the step and agent that created it.

Think locally. Act intelligently.

---

## Taglines

- Think locally. Act intelligently.
- Your AI. Your machine. Your data.
- Sovereign AI automation for Windows.
- The model proposes. You decide.
- Local inference. Real automation. Full audit.
- Zero cloud. Full control.
- AI that acts, not just answers.

---

## Key facts

| Fact | Value |
|---|---|
| Platform | Windows 10 / 11 x64 |
| Model | Google Gemma 4 (local, via Ollama) |
| Context window | 128,000 tokens |
| Tool count | 44 deterministic tools |
| Agent types | 8 specialized agents |
| Cloud dependencies | None |
| API keys required | None |
| Audit mechanism | SHA-256 chained event log |
| License | Proprietary |
| Year | 2026 |

---

## Technology stack

**Backend:** Python 3.12, FastAPI, LangGraph, aiosqlite, ChromaDB, Playwright, pywin32, python-docx, openpyxl, python-pptx

**Frontend:** Electron, React 18, TypeScript, Tailwind CSS, Framer Motion, Vite

**AI runtime:** Ollama, Gemma 4 (Q4_K_M), all-MiniLM-L6-v2 (embeddings)

**Distribution:** PyInstaller (backend executable), Electron Builder / NSIS (Windows installer)

---

## What makes it different

| Feature | SyncNode | Cloud AI assistants | Local LLM chat tools | RPA tools |
|---|---|---|---|---|
| Fully offline | Yes | No | Yes | Yes |
| Multi-step workflows | Yes | Partial | No | Yes |
| Post-condition verification | Yes | No | No | Partial |
| Immutable audit chain | Yes | No | No | Partial |
| Human approval gate | Yes | Sometimes | No | Sometimes |
| Real desktop automation | Yes | No | No | Yes |
| Local model inference | Yes | No | Yes | No |
| Natural language goals | Yes | Yes | Yes | No |
| Open file access | Yes | No | No | Yes |

---

## Screenshots and assets

Hero image: `application_hero.png` in the repository root.

Additional screenshots of the workbench, run timeline, and agent inspector are available on the [GitHub releases page](https://github.com/Boredooms/SyncNode/releases).

---

## Contact

GitHub: [github.com/Boredooms/SyncNode](https://github.com/Boredooms/SyncNode)
