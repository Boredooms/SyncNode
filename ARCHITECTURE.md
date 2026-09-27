# SyncNode — Architecture

> **Think locally. Act intelligently.**
> v1.0.23 · Windows · Ollama · gemma4:e4b · Electron + React

---

## System overview

```
┌────────────────────────────────────────────────────────────────────┐
│                      Electron Frontend                              │
│  React 18 · TypeScript · Tailwind · Framer Motion · Vite           │
│                                                                      │
│  Splash → Workbench shell                                           │
│  ├── Home      (goal composer · model switcher · doc upload)        │
│  ├── Runs      (run list · active run · approval panels)            │
│  │   ├── Overview · Automation · Intent · Plan · Agents             │
│  │   ├── Timeline · Desktop · Tools · Artifacts · Evidence          │
│  │   └── Approvals · Audit                                          │
│  ├── Chat      (agentic chat · tool execution · file attach)        │
│  ├── Knowledge (ChromaDB RAG browser · document upload)             │
│  ├── Learning  (workflow memory candidates)                          │
│  └── Settings  (model · GPU · appearance)                           │
└──────────────────────┬─────────────────────────────────────────────┘
                       │  HTTP + SSE  localhost:8000
┌──────────────────────▼─────────────────────────────────────────────┐
│                    FastAPI Backend                                   │
│  Python 3.12 · asyncio · aiosqlite · SQLite                        │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  Orchestrator (LangGraph)                    │   │
│  │  Enrich → Intent → Plan → Sanitize → Wave execution         │   │
│  │  _resolve_step_inputs → Tool → Verify → Recover → Audit     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Tool Registry (44 tools)                                           │
│  ├── document.*   (7)   Word · filesystem · writer                  │
│  ├── computer.*   (9)   Windows UIA · screenshot · launch           │
│  ├── browser.*    (8)   Playwright Chromium                         │
│  ├── excel.*      (6)   openpyxl + write_range + auto-resolve       │
│  ├── powerpoint.* (3)   python-pptx                                 │
│  └── system.*    (12)   PowerShell · process · clipboard · env      │
│                                                                      │
│  Verification Engine · Recovery Engine · Audit Chain (SHA-256)      │
│  Approval Gateway · Policy Engine · Artifact Registry               │
│  Knowledge (ChromaDB + MiniLM) · Learning (workflow memory)         │
└──────────────────────┬─────────────────────────────────────────────┘
                       │  HTTP  localhost:11434
┌──────────────────────▼─────────────────────────────────────────────┐
│                       Ollama (local)                                 │
│  gemma4:e4b  — primary   (GPU · Q4_K_M · 8B · 128k ctx · vision)   │
│  gemma3:1b   — enricher  (CPU · 999M · keep_alive=0)               │
└────────────────────────────────────────────────────────────────────┘
```

---

## Execution pipeline (one run, end to end)

```
User goal (natural language)
        │
        ▼
┌─────────────────────────────────────────────┐
│  Step -1: Prompt Enrichment (gemma3:1b CPU)  │
│  Extracts: recipient_email, subject,          │
│  body_hint, save_filename                     │
│  Model unloads immediately (keep_alive=0)     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 0: Conditional RAG                     │
│  ChromaDB semantic search over knowledge     │
│  base — injects relevant context if found    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 1: Intent Extraction (gemma4:e4b GPU)  │
│  Output: StructuredIntent                    │
│    goal_type: COMPOSITE | DOCUMENT | EMAIL…  │
│    tasks: [str]                              │
│    capabilities: [str]                       │
│    constraints: [str]                        │
│    recipient, subject_hint, body_hint        │
│    save_filename                             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 2: Plan Generation (gemma4:e4b GPU)    │
│  Output: ExecutionPlan (DAG)                 │
│  Each PlanStep has:                          │
│    step_key, agent_key, action, description  │
│    dependencies: [step_key]                  │
│    inputs: dict                              │
│    postconditions: [Postcondition]           │
│    retry_policy, timeout_seconds             │
│    requires_approval: bool                   │
│  Profile: num_ctx=16384, max_tokens=6144     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 3: Plan Sanitization                   │
│  - Drop unknown tool names                   │
│  - Enforce launch_app depends on create_docx │
│  - Block steps after workflow.pause          │
│  - Strip requires_approval from browser ops  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 4: LangGraph Wave Execution            │
│  g_next_wave() → parallel batch of steps    │
│  Each step: _execute_step()                  │
│    → _resolve_step_inputs()  (inject paths)  │
│    → ExecutionEngine.run()                   │
│       PROPOSED → VALIDATED → AUTHORIZED      │
│       → LOCKED → EXECUTING → OBSERVING       │
│       → VERIFYING → PASSED | FAILED          │
│    → _capture_artifacts()  (register output) │
│    → RecoveryEngine if FAILED                │
└──────────────────┬──────────────────────────┘
                   │ (all waves complete)
                   ▼
┌─────────────────────────────────────────────┐
│  Step 5: Approval Gate                       │
│  _external_send_pending() → if email run:    │
│  pause, emit approval.requested SSE          │
│  Human clicks Approve in Electron UI         │
│  → _click_gmail_send() → Send button clicked │
│  → run.status = completed                    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 6: Workflow Memory                     │
│  Records trajectory → ChromaDB              │
│  Future similar runs get faster planning     │
└────────────────────────────────────────────┘
```

---

## AI / ML substrate (`ai_ml/`)

### Model Gateway (`syncnode_ai/gateway/`)

The single boundary between all cognition code and the model runtime.

| Class | Role |
|---|---|
| `ModelGateway` | Enforces local-only inference, structured output repair loop (up to 2 repairs), streaming, telemetry |
| `OllamaAdapter` | Speaks Ollama HTTP API (`/api/tags`, `/api/chat`). Handles tool payloads, vision images, thinking mode |
| `ModelRequest` | num_ctx, num_gpu, keep_alive, temperature, max_tokens, tools, output_schema |
| `ModelStreamEvent` | delta / tool_call / done event types |

**Invariant MG-01**: No request may target a cloud model (`:cloud` suffix is rejected).

**Invariant MG-03**: Structured output repair loop ≤ 2 attempts after initial generation.

### Multimodal support

Gemma 4 (`gemma4:e4b`) is a **vision + audio + thinking** model:

```python
ModelCapabilities(
    vision=True,        # accepts base64 screenshot images
    audio=True,
    tools=True,         # native function calling
    thinking=True,      # internal chain-of-thought
    context_window=131072,
    parameter_size="8.0B",
    quantization="Q4_K_M",
)
```

Vision is used by:
- Computer agent observing screenshots after UIA actions
- Verifier agent visually confirming desktop state
- Chat sessions with attached images

### Inference Profiles (`syncnode_ai/routing/profiles.py`)

| Profile | num_ctx | max_tokens | temp | Use |
|---|---|---|---|---|
| `FAST_SIMPLE` | 4096 | 512 | 0.4 | writer.generate_paragraph |
| `FAST_STRUCTURED` | 12288 | 2048 | 0.0 | intent extraction |
| `NORMAL_REASONING` | 12288 | 3072 | 0.2 | general reasoning |
| `PLANNER` | 16384 | 6144 | 0.0 | DAG generation |
| `VISION` | 8192 | 512 | 0.0 | screenshot analysis |

### Intent Engine (`syncnode_ai/intent/`)

`IntentEngine.extract(goal)` → `StructuredIntent`

```python
class StructuredIntent:
    goal_type: GoalType          # DOCUMENT | EMAIL_DRAFT | COMPOSITE | SEARCH ...
    goal_summary: str
    tasks: list[str]
    capabilities: list[str]
    constraints: list[str]
    recipient: Optional[str]
    subject_hint: Optional[str]
    body_hint: Optional[str]
    save_filename: Optional[str]
    requires_approval: bool
```

### Planner (`syncnode_ai/planner/`)

`Planner.plan(intent)` → `ExecutionPlan`

```python
class PlanStep:
    step_key: str
    agent_key: str              # writer | document | office | computer | browser | system | supervisor
    action: str                 # e.g. "document.create_docx"
    description: str
    dependencies: list[str]
    inputs: dict
    postconditions: list[Postcondition]
    retry_policy: RetryPolicy
    timeout_seconds: int
    requires_approval: bool

class Postcondition:
    assertion_type: str         # file_exists | content_generated | application_running | ...
    target: str
    expected: Any
    description: str
```

### Agent Registry (`syncnode_ai/agents/`)

| Agent | Capabilities | Allowed tools |
|---|---|---|
| `writer` | paragraph_writing | writer.generate_paragraph |
| `document` | document_creation, document_inspection | document.*, filesystem.* |
| `office` | spreadsheet_creation, presentation_creation | excel.*, powerpoint.* |
| `computer` | uia_control, window_management, screenshot_capture, process_launch | computer.* |
| `browser` | browser_navigation, dom_interaction, file_attachment, email_draft | browser.* |
| `system` | filesystem, shell, system_access, clipboard, registry | system.* |
| `verifier` | file_verification, uia_verification, dom_verification | verify.*, computer.screenshot, document.inspect_docx |
| `recovery` | failure_analysis, retry_management, replan_proposal | computer.screenshot, filesystem.find, workflow.* |
| `supervisor` | orchestration, approval | workflow.* |

---

## Tool Registry (44 tools)

Every tool is a `ToolDefinition` with:
- `key` — namespaced string (`excel.write_range`)
- `input_schema` — typed parameter map
- `arg_aliases` — model hallucination tolerance (maps synonyms to real params)
- `drop_decorative_args` — silently drops unknown kwargs
- `risk_class` — low | medium | high | external
- `side_effect_type` — READ_ONLY | REVERSIBLE_LOCAL | IDEMPOTENT_LOCAL | DESTRUCTIVE_LOCAL | EXTERNAL_COMMUNICATION
- `verification_strategy` — always | never
- `resource_locks` — desktop | excel | powerpoint (prevents concurrent UI access)
- `handler` — the actual async Python function

### Document tools (7)

| Key | What it does |
|---|---|
| `writer.generate_paragraph` | Generates prose via local model. Aliases: `content_prompt→topic`, `writing_prompt→topic` |
| `document.create_docx` | Creates `.docx` with content via python-docx. Auto-generates content from title if empty |
| `document.inspect_docx` | Returns paragraph structure, word count, sha256 |
| `document.read_docx` | Returns full text |
| `filesystem.write` | Writes text file inside workspace |
| `filesystem.find` | Glob search inside workspace |
| `filesystem.hash` | SHA-256 a file |

### Computer / UIA tools (9)

| Key | What it does |
|---|---|
| `computer.windows_search` | Windows taskbar search OR direct file open (fast path via `cmd start ""`) |
| `computer.launch_app` | Launches Word/Excel/PowerPoint/Notepad. Smart path detection: pass `.xlsx` path → auto-maps to Excel. Blocks on workspace scan for docx if parallel wave race detected |
| `computer.find_window` | Find top-level window by title/class |
| `computer.uia_find` | Find UIA control by AutomationId/Name |
| `computer.uia_type` | Type text into live app window. Strips `.docx` extension before searching. Polls 3s for window readiness |
| `computer.uia_click` | Click UIA control by name/AutomationId |
| `computer.key_press` | Send keyboard shortcut. **BLOCKS `{Ctrl}w`** — crashes Electron |
| `computer.screenshot` | Full desktop screenshot |
| `computer.get_active_window` | Returns focused window info |

### Browser tools (8) — Playwright Chromium

| Key | What it does |
|---|---|
| `browser.navigate` | Navigate to URL. Mail-compose URLs auto-redirect to local compose fixture |
| `browser.type` | Fill form field by label/role/selector. Semantic field routing: `body`/`message` → `#body`, `subject` → `#subject`, `to`/`recipient` → `#to` |
| `browser.click` | Click element by role/label/text |
| `browser.attach_file` | Set file input. Accepts `path1|path2|path3` for multi-file |
| `browser.find_element` | Find element, return visibility |
| `browser.screenshot` | Browser viewport screenshot |
| `browser.get_url` | Current URL + title |
| `browser.get_dom_text` | Inner text of page or element |

### Excel tools (6)

| Key | What it does |
|---|---|
| `excel.create` | Create workbook with `rows` (2D list) + `headers`. Workspace-scoped |
| `excel.write_cell` | Write single cell. Auto-resolves bare filename from workspace. Handles Permission Denied via auto-close + retry (3 attempts) |
| `excel.write_range` | Write multiple rows from `start_cell`. Same auto-resolve + retry. Falls back to `worksheets[0]` if `sheet_name` not found |
| `excel.read_cell` | Read single cell value |
| `excel.read_range` | Read rectangular range as 2D list |
| `excel.inspect` | Sheet names, dimensions, non-empty cell count |

### PowerPoint tools (3)

| Key | What it does |
|---|---|
| `powerpoint.create` | Create presentation with title slide + optional `slides` list |
| `powerpoint.add_slide` | Append title+content slide |
| `powerpoint.inspect` | Slide count, per-slide text |

### System tools (12)

| Key | What it does |
|---|---|
| `system.fs_read` | Read any file — no workspace restriction |
| `system.fs_list` | List directory |
| `system.fs_search` | Recursive file search by name/content. Result captured as `doc_path`/`excel_path`/`powerpoint_path` for downstream open steps |
| `system.fs_write` | Write file (blocks system dirs) |
| `system.fs_delete` | Delete file — DRY RUN by default |
| `system.shell` | Run PowerShell command. Blocked patterns: format, shutdown, bootloader, mass-delete |
| `system.process_list` | List running processes |
| `system.process_kill` | Kill process — DRY RUN by default |
| `system.clipboard_get` | Read clipboard |
| `system.clipboard_set` | Set clipboard |
| `system.env_get` | Read environment variable |
| `system.registry_get` | Read Windows registry value |

---

## Verification Engine

After every tool call, `VerificationEngine.verify_step()` runs all postconditions.

### Assertion types (50+ registered + aliases)

| Category | Types |
|---|---|
| File | `file_exists`, `file_non_empty`, `file_hash_match`, `artifact_structure_valid` |
| Content | `content_generated` — reads scratch file + tool_result["content"] |
| Office | `xlsx_structure_valid`, `pptx_structure_valid` |
| UIA / command | `command_succeeded` — reads `typed`/`clicked`/`sent`/`exit_code` from tool output |
| Application | `application_running` — checks process existence via psutil |
| Browser | `page_loaded`, `field_value`, `attachment_present`, `not_sent` |
| Search | `search_result_found` |

### Alias normalization

`_normalize_assertion_type()` maps 100+ model-hallucinated assertion names to real handlers:
- `ui_element_contains` → `command_succeeded`
- `file_saved` → `file_exists`
- `content_typed` → `command_succeeded`
- `approval_requested` → `command_succeeded`
- Any `element`/`uia`/`typed`/`keys` keyword → `command_succeeded`

### Failure and recovery

```
VERIFICATION_FAILED
    → RecoveryEngine.decide()
    → RETRY (max 3 attempts, exponential backoff 250/1000/4000ms)
    → REOBSERVE (re-screenshot, re-check state)
    → FALLBACK (try alternative tool)
    → REPLAN (generate new sub-plan)
    → ESCALATE → step marked failed → run.failed
```

Circuit breaker: after 3 failures of the same (step, error_class) pair → ESCALATE immediately.

---

## Orchestrator — `_resolve_step_inputs()` (critical data flow)

Before every tool invocation, `_resolve_step_inputs` injects correct values:

| Situation | What it does |
|---|---|
| `document.create_docx` with placeholder `content` | Injects `self._artifacts["content"]` from writer step |
| `computer.uia_type` with placeholder `text` | Same injection + sets `clear_first=True` to avoid Word duplicate |
| `computer.launch_app` for Word/Excel with no `args` | Polls run directory for `.docx`/`.xlsx`/`.pptx` file (up to 40 scans while create runs in parallel) |
| `computer.windows_search` for doc open | Injects `file_path` from artifacts — never leaves it as bare filename (would open Bing) |
| `browser.attach_file` | Overrides all paths with all run-produced artifact paths joined by `\|` |
| `computer.key_press` {Ctrl}s | Pre-fills `file_saved` postcondition target with actual artifact path |
| `_is_placeholder()` | Catches `$`, `{{}}`, `<>`, `[]`, `[[]]`, `()` — forces injection |

**plan dependency enforcement** (`_sanitize_plan`):
- `computer.launch_app` for word → forced dependency on `document.create_docx`
- `computer.launch_app` for excel → forced dependency on `excel.create`
- Drops all steps after `workflow.pause`

---

## Approval gate

Two paths to `waiting_approval`:

1. **Step-level**: a step with `requires_approval=True` raises `ApprovalRequiredSignal`
2. **Policy boundary**: after all steps complete, if `_external_send_pending()` is True (goal mentions email + browser steps ran) — always enforced regardless of plan

After `POST /api/v1/runs/{id}/approvals/{id}/decide`:
- `_click_gmail_send()` tries 6 selectors on the open Playwright page (`#send-button`, `button[aria-label='Send']`, etc.) — fast timeout (800ms each)
- `run.status = "completed"` + all running steps marked completed
- `run.completed` SSE emitted

---

## Agentic Chat

Chat uses the same tool registry as workflows with an extended system prompt teaching:
- How to open files by absolute path (3 methods)
- Close-before-write pattern for locked Excel files
- Correct sheet name from run context artifacts

**`<tool_code>` XML extraction**: When Gemma outputs tool calls as `<tool_code>fn(args)</tool_code>` text instead of native function call events, the streaming loop buffers all deltas, detects the XML after the full round completes, parses it with `ast.literal_eval` (handles nested `rows=[[...]]`), strips the XML from the displayed response, and executes the parsed tool calls. Client never sees raw XML.

---

## Compose page (local Gmail fixture)

`tests/fixtures/web/compose.html` — a real, drivable DOM that looks like Gmail:

- `#to` — email input with recipient chip
- `#subject` — subject text input  
- `#body` — textarea for email body
- `#attachment` — file input (polls every 250ms to render chips)
- `#send-button` — triggers `data-sent=true` + shows "Sent" text

Pre-filled from URL params: `?to=...&subject=...&body=...` (Gmail uses `su=` for subject — mapped automatically). Also filled by `_fill_compose_fields_after_navigate()` directly via Playwright after navigation.

---

## Data layer

| Store | What it holds |
|---|---|
| SQLite (`data/syncnode.db`) | Runs, RunSteps, ToolCalls, Observations, VerificationResults, Approvals, Artifacts, AuditEvents, ChatSessions, ChatMessages |
| ChromaDB (`data/rag_index`) | Knowledge base chunks + embeddings (all-MiniLM-L6-v2, offline) |
| Workspace (`workspace/`) | All generated files, run-scoped directories, screenshots |
| Knowledge (`knowledge/`) | Markdown knowledge base with YAML front matter |

### Artifact registry (per-run)

Every created file is registered in `RunArtifactRegistry`:
- `kind`: word | excel | powerpoint | screenshot
- `path`: absolute, run-scoped (`workspace/demo/runs/{run_id}/word/filename.docx`)
- `sha256`, `size_bytes`, `verified`, `mime_type`

Run isolation: all artifacts scoped to `workspace/demo/runs/{run_id}/` — no run can read another's artifacts.

---

## API surface (`/api/v1/`)

| Endpoint | Description |
|---|---|
| `POST /api/v1/runs` | Create run, returns `run_id` |
| `GET /api/v1/runs` | List all runs |
| `GET /api/v1/runs/{id}` | Run status + metadata |
| `GET /api/v1/runs/{id}/steps` | Plan steps with status |
| `GET /api/v1/runs/{id}/events` | SSE stream |
| `GET /api/v1/runs/{id}/artifacts` | Produced artifacts |
| `GET /api/v1/runs/{id}/audit` | SHA-256 audit chain events |
| `POST /api/v1/runs/{id}/approvals/{aid}/decide` | Approve / reject |
| `GET /api/v1/models` | List all local Ollama models |
| `GET /api/v1/models/active` | Get active model |
| `POST /api/v1/models/active` | Hot-swap active model (no restart) |
| `POST /api/v1/documents/upload` | Upload + parse + ingest file to RAG |
| `POST /api/v1/documents/parse` | Parse file, return text |
| `GET /api/v1/documents/status` | ChromaDB collection stats |
| `POST /api/v1/chat/sessions` | Create chat session |
| `POST /api/v1/chat/sessions/{id}/stream` | Agentic chat SSE stream |
| `GET /health/ready` | Full readiness check (model + db + rag) |

---

## Frontend architecture

```
Electron Main Process
  └── secure IPC bridge (contextIsolation: true, nodeIntegration: false)
       └── Preload: exposes window.api.window.{minimize, maximize, close}
            └── React Renderer
                 ├── zustand stores: runStore · healthStore · uiStore
                 ├── SSE manager (per-run stream, reconnect, dedup)
                 ├── REST client (normalizeRun · normalizeStep · normalizeArtifact)
                 └── Routes: / → /runs/:id/{overview,timeline,agents,artifacts,approvals,...}
```

### SSE event vocabulary (40+ types)

`stream.connected` → `run.created` → `intent.completed` → `plan.created` → `plan.wave_dispatched` → `agent.spawned` → `tool.proposed` → `tool.authorized` → `tool.started` → `tool.completed` → `observation.captured` → `verification.passed|failed` → `recovery.started` → `approval.requested` → `approval.decided` → `run.waiting_approval` → `run.completed|failed`

---

## Network Monitor (`scripts/network_monitor.py`)

Demo tool that proves SyncNode is fully sovereign:

```powershell
python scripts/network_monitor.py --all --loopback
```

- Captures all TCP connections in real time via `psutil`
- Classifies: `LOCAL (SyncNode)` (green) · `LAN` (yellow) · `[!] EXTERNAL [!]` (red)
- On `Ctrl+C` prints final verdict: **"ZERO external connections — SOVEREIGN"**

---

## GPU configuration (RTX 2050 optimized)

```
CUDA_VISIBLE_DEVICES=0      # force discrete GPU, skip Intel iGPU
OLLAMA_IGPU_ENABLE=0        # disable Intel Vulkan probe
OLLAMA_LOAD_TIMEOUT=300s    # allow CUDA init time
OLLAMA_MAX_LOADED_MODELS=1  # prevent parallel CUDA deadlock
OLLAMA_KEEP_ALIVE=30m       # keep model warm (0.01s warm vs 11-19s cold)
num_gpu=99                   # all layers to GPU (~3.8x faster than auto)
num_ctx=8192                 # bounded to keep model GPU-resident
```

---

## Release history

| Tag | Key changes |
|---|---|
| v1.0.1 | Initial release |
| v1.0.2 | README + hero image + website/ docs |
| v1.0.3 | Open-file bug fix · multi-model router · document parser · network monitor |
| v1.0.4 | ChromaDB singleton — fix Knowledge Base "unavailable" on splash |
| v1.0.5 | Document upload on Home · file attachment in Chat |
| v1.0.6 | `ui_element_contains` alias · uia_type window poll · planner forbidden assertions |
| v1.0.7 | Chat open-file: smart path detection · correct system prompt |
| v1.0.8 | `save_word_report` verify fix · double-content fix · post-approval Send · pause last-step |
| v1.0.9 | Planner `StructuredOutputError` — num_ctx 16384 |
| v1.0.10 | Approval stuck in running · subject regex · compose fill |
| v1.0.11 | Syntax fix in runs.py |
| v1.0.12 | Approval completion + send timeout + session.commit |
| v1.0.13 | `excel.write_range` · subject quotes · chat ctx 16384 |
| v1.0.14 | `writer.generate_paragraph` `content_prompt` alias |
| v1.0.15 | Excel Permission Denied + Chat blank bubble |
| v1.0.16 | Ctrl+W blocks · async wait for docx |
| v1.0.17 | Word blank — poll for docx before launch (parallel wave race) |
| v1.0.18 | SyntaxError: await outside async — time.sleep in sync method |
| v1.0.19 | Block Ctrl+W + async wait in _execute_step |
| v1.0.20 | Writer paragraph in email body + Word plan dependency |
| v1.0.21 | tool_code XML parsing + chat overflow + excel sheet |
| v1.0.22 | Streaming buffer — XML stripped before client sees it |
| v1.0.23 | **ast.literal_eval** parser for nested tool_code args |
