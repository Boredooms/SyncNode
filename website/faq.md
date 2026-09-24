# Frequently Asked Questions

## General

### What is SyncNode?

SyncNode is a local AI automation workbench for Windows. You give it a natural-language goal — "create a quarterly report and prepare an email with the files attached" — and it executes that goal using specialized AI agents, real Windows automation tools, and a local LLM running on your GPU. Nothing leaves your machine.

### Does it require an internet connection?

Only for the initial model download via Ollama. Once the models are downloaded, SyncNode runs entirely offline. All inference, file operations, and automation are local.

### Is it free?

The software is currently proprietary. Check the [GitHub releases page](https://github.com/Boredooms/SyncNode/releases) for the current distribution terms.

### What Windows versions does it support?

Windows 10 x64 and Windows 11 x64. Windows 11 is recommended for the best Windows UI Automation coverage.

---

## Hardware and models

### What GPU do I need?

Any GPU works — SyncNode falls back to CPU if no GPU is available. For a usable experience, an NVIDIA GPU with 4 GB+ VRAM is recommended. An RTX 2050 or better handles the default `gemma4:e4b` model well.

### What model does SyncNode use?

The default is `gemma4:e4b` — Google's Gemma 4 model, 8 billion parameters, quantized to Q4_K_M, running via Ollama. It has a 128,000 token context window, vision support, and structured output capability.

A smaller `gemma3:1b` model is used for enrichment and summarization tasks.

### Can I use a different model?

Yes. SyncNode's model gateway is provider-agnostic. Any model available in your local Ollama instance can be configured via the `.env` file (`SYNCNODE_MODEL_ID`). The model needs structured output support for the planner to work correctly.

### How much storage does it need?

The Gemma 4 model is ~9.6 GB. The application itself and its dependencies are under 1 GB. Allow 20 GB total for models, dependencies, and working data.

### How long does it take to run a workflow?

Depends on the GPU and the complexity of the goal. A simple 3-step document creation workflow typically takes 2-4 minutes on an RTX 2050. A complex 12-step workflow with Office automation and browser control takes 8-15 minutes.

---

## Privacy and security

### Does SyncNode send any data to external servers?

No. When Ollama is configured for local-only operation (the default), all model inference is local. The application itself makes no outbound network requests. Your goals, documents, and run history stay on your machine.

### Can the AI send emails or delete files without my permission?

No. SyncNode has a mandatory approval gate for any action classified as `EXTERNAL_COMMUNICATION` (sending messages, emails) or `DESTRUCTIVE_LOCAL` (deleting files). When the workflow reaches such a step, it pauses and presents you with a summary. You must explicitly approve before execution continues.

### Is there an audit log?

Yes. Every event — intent extraction, tool call, verification result, approval decision — is recorded in an immutable audit chain with SHA-256 hashes linking each event to the previous one. You can query the full audit history via the frontend or the API.

### Can the AI access any file on my machine?

SyncNode's system tools can read and write files. The scope is controlled by the tool policy configuration. By default, tools operate within the configured workspace root. Sensitive operations follow the same approval policy as other high-risk actions.

---

## How it works

### What is a "run"?

A run is one execution of a goal. It has an ID, a status, a set of steps, and an audit log. Runs are durable — they survive application restarts. You can view all past runs, their steps, artifacts, and audit events in the frontend.

### What is "verification"?

After every tool call, SyncNode runs assertions against the real system state. For example, after creating a Word document, it checks that the file exists on disk and is non-empty. After opening an application, it checks that the process is running and the window title is present. If an assertion fails, the step is marked failed — not silently retried.

### What happens when a step fails?

The Recovery agent re-observes the actual state of the system and decides whether to retry with the same approach, retry with a modified approach, or escalate to a re-plan. There are explicit retry limits — no infinite loops.

### What is "workflow memory"?

When a run completes successfully, SyncNode records the plan pattern in its local ChromaDB knowledge base. Future runs on similar goals can retrieve this pattern and use it to plan more efficiently. This is entirely local and private.

### What is LangGraph?

[LangGraph](https://github.com/langchain-ai/langgraph) is the execution engine SyncNode uses for its orchestrator. It models the workflow as a directed graph where each node is a step (intent extraction, planning, agent dispatch, verification, etc.) and edges represent transitions between states. This enables parallel execution of independent steps and conditional branching for recovery.

---

## Troubleshooting

### The model takes a long time to load

On the first call after startup, the model needs to load into GPU memory. This can take 30-60 seconds on a cold start. The `OLLAMA_LOAD_TIMEOUT=300s` environment variable (set automatically by the startup scripts) gives it enough time.

### I see "GPU discovery watchdog timed out"

This usually happens on systems with both a discrete NVIDIA GPU and an Intel integrated GPU. The startup scripts set `CUDA_VISIBLE_DEVICES=0` and `OLLAMA_IGPU_ENABLE=0` to resolve this. If you're starting Ollama manually, set those environment variables yourself.

### A run is stuck in "planning" status

Check the backend logs. The most common cause is the model producing malformed JSON. The repair loop retries up to 3 times. If all attempts fail, the run is marked failed with a `StructuredOutputError` message.

### The browser automation isn't working

Make sure Playwright's Chromium is installed: `playwright install chromium`. The browser tools require Chromium to be available.

### Where are my generated files?

By default, all run artifacts are saved to `C:\syncnode\workspace\`. You can configure this with `SYNCNODE_WORKSPACE_ROOT` in your `.env` file.
