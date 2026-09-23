---
id: workspace_rules
type: policy
version: 1
trust: authoritative_policy
status: active
tags:
  - workspace
  - filesystem
  - security
---

# Workspace Rules

All document artifacts must be created inside the approved SyncNode workspace.
Files must never be written outside the workspace root. Model-supplied paths are
resolved relative to the workspace and validated before any write.

- The demo workspace is the canonical location for golden-demo artifacts.
- Path traversal (`..`) and absolute paths outside the workspace are rejected.
- Every created artifact is hashed (SHA-256) and structurally verified.
