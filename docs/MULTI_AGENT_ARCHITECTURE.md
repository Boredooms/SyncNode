# Multi-Agent Architecture

## Honest current state

SyncNode has a **declarative agent registry** (8 agents) with scoped tool access,
capabilities, risk class, and system prompts. A run's plan assigns each step an
`agent_key`; the orchestrator spawns (resolves) that agent, scopes its tools, and
executes its step through the shared `ExecutionEngine` and one shared
`ModelGateway` (no 12 duplicate model runtimes).

What is **implemented**:
- Agent registry + capability-based resolution (`agent_registry.spawn`).
- Per-agent tool scoping (`tool_registry.schemas_for_agent`).
- Shared model gateway + GPU-aware inference profiles.
- Resource locks so agents cannot conflict over the desktop/app/file.
- Supervisor role (workflow control), writer, document, office, computer,
  browser, verifier, recovery.

What is **NOT yet implemented** (stated plainly):
- The orchestration is a wired **sequential** engine, not a LangGraph
  `StateGraph`. LangGraph 1.2.11 is installed but not the execution graph.
- **Parallel agent subgraphs** are not wired; steps run sequentially. The
  building blocks for safe parallelism (resource locks, single model queue) are
  present, but branch fan-out/join is not.
- The 8 registry agents cover the logical roles; a full 11–12-agent split
  (separate TaskUnderstanding / ContextKnowledge / ModelRouting / AuditLearning
  agents) is not realized as distinct runtime agents — those responsibilities
  currently live in orchestrator stages (intent engine, `_retrieve_knowledge`,
  inference profiles, audit + workflow memory).

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| supervisor | workflow control, approval, replan | workflow.* |
| writer | generate text content | writer.generate_paragraph |
| document | Word/docx + filesystem | document.*, filesystem.* |
| office | Excel + PowerPoint | excel.*, powerpoint.* |
| computer | Windows shell / UIA | computer.* (incl. windows_search) |
| browser | web + email compose | browser.* |
| verifier | evidence-based verification | verify.*, inspect, screenshot |
| recovery | bounded recovery | screenshot, find, replan, pause |

## Recommended next step

Introduce a LangGraph `StateGraph` with a typed global `RunState`, expressing the
existing pipeline as nodes, then add parallel branches for independent
artifact-producing agents (Word / Excel / PowerPoint) with a dependency join
before the email agent. The model concurrency must stay bounded (single GPU
queue); only logical/tool parallelism should fan out.
