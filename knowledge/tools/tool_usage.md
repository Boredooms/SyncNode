---
id: tool_usage
type: tool
version: 1
trust: reference
status: active
tags:
  - tools
  - registry
  - usage
---

# Tool Usage

Tools are authoritative: a step may only use a tool that is registered and that
its agent is permitted to call. Tool arguments must match the tool's declared
schema; only explicitly declared aliases (e.g. `filename` -> `path`) are
normalized. Unknown arguments and unknown tools fail closed.

Prefer the smallest set of tools for a step. The planner declares each step's
`allowed_tools`; the model receives only those tool schemas, not the whole
catalog.
