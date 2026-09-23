# Parallel Execution & Resource-Aware Scheduling

## Logical vs physical parallelism

SyncNode separates **logical** parallelism (independent agents/branches may run
concurrently) from **physical** concurrency limits (a 4 GB RTX 2050 runs one
local generation at a time; SQLite has one writer).

- **Logical:** the planner produces a DAG; `g_next_wave` computes the next
  runnable wave — steps whose dependencies are all satisfied. Independent steps
  (e.g. `excel.create`, `powerpoint.create`) share a wave; at most one step per
  exclusive resource (`desktop`, `browser`) is placed in a wave.
- **Physical:** the `ResourceScheduler` bounds model inference to
  `model_concurrency` (default 1) and tools to `tool_concurrency` (default 3);
  the `ResourceLockManager` grants exclusive leases on desktop / app / file.

## Proven parallelism

`backend/tests/unit/test_graph_parallel.py`:
- `test_langgraph_branches_overlap` — 3 LangGraph branches reach an
  `asyncio.Barrier(3)` **simultaneously** (a sequential loop would deadlock),
  proving real fan-out.
- `test_scheduler_bounds_model_concurrency` — 4 model calls, peak concurrency 1.
- `test_tool_concurrency_allows_overlap` — independent tools overlap.

## Physical execution policy (SQLite)

On the current single-node SQLite deployment, **step execution within a wave is
serialized** (`g_run_wave`) to avoid SQLite write contention (concurrent writers
raise "database is locked"; WAL + busy_timeout are enabled but a stronger store
is required for true concurrent step writes). The graph, wave computation, and
scheduler still model parallelism, and `g_run_wave` switches to `asyncio.gather`
automatically for a concurrent-capable store (`"sqlite" not in database_url`).

This is an honest constraint: **logical/graph parallelism is real and tested;
physical concurrent step execution is enabled only on a non-SQLite store.** For
Postgres (already supported by the settings/DSN), set `DATABASE_URL` to a
`postgresql+asyncpg://…` DSN and wave steps execute concurrently.

## Wave example (three-artifact run, observed)

```
WAVE 1: search_word(desktop), create_excel, create_pptx, navigate_email(browser)
WAVE 2: launch_word(desktop), type_subject(browser)
WAVE 3: create_docx, attach_files
WAVE 4: verify/approval  -> WAITING_APPROVAL
```
