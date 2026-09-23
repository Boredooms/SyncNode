# Structured-Output Optimization

Measured optimization of the structured-output prompt payload for local
`gemma4:e4b`. Goal: **less prompt + less output at the same correctness**.

## Problem

`generate_structured` embedded the full `pydantic.model_json_schema()` (with
`title` on every field, long `description`s, and `$defs`/`$ref` indirection)
into the prompt. For the intent and plan schemas this was ~1k tokens each of
pure schema boilerplate, on every intent and plan call.

## Approach

`ai_ml/.../gateway/_schema.py::compact_schema_text` inlines `$ref`/`$defs`
(bounded depth) and emits a compact JSON shape that keeps only what actually
constrains the output:

- field names,
- types,
- required vs optional (`name?`),
- `enum` / `const` values,
- array/object structure.

It drops `title` and long `description` noise. Validation is still performed
against the **full** pydantic schema and the provider `format` is still the full
schema, so correctness is unchanged — only the prompt hint is smaller.

Enabled by default (`ModelGateway(compact_schema=True)`); set `False` to A/B
against the full-schema behaviour.

## Measured reduction

`python scripts/measure_schema.py` (approx tokens at ~4 chars/token):

| Schema | Full | Compact | Reduction |
|--------|-----:|--------:|----------:|
| StructuredIntent | 4144 chars (~1036 tok) | 831 chars (~207 tok) | **80%** |
| ExecutionPlan (`_PlannerOutput`) | 3786 chars (~946 tok) | 655 chars (~163 tok) | **83%** |

That is ~1.6k prompt tokens removed across a single intent + plan pair.

## Correctness

- Gate B `test_structured_output` passes with the compact hint.
- Structured intent + plan still validate in the golden E2E.
- Bounded repair (≤ 2, MG-03) and deterministic parsing are unchanged.

## Per-step tool-schema scoping

The planner emits `allowed_tools` per step; the orchestrator validates each
step's action against the tool registry and drops hallucinated tools. Tool
schemas are **not** dumped into every model call — a step's model context is
scoped to the tools that step may use (see the tool registry
`tools_for_agent` / `schemas_for_agent` helpers and `docs/PROMPT_TOOL_REGISTRY`).

## Not done (deliberately)

- Native provider grammar (`format = <full schema>`) was left off the hot path:
  the compact-hint + `format:"json"` approach is fast and valid, and a large
  compiled grammar previously hurt planning latency. Revisit only with a
  measured win.
