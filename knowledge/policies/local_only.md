---
id: local_only
type: policy
version: 1
trust: authoritative_policy
status: active
tags:
  - inference
  - local
  - security
---

# Local-Only Inference

All model inference must run against the local Ollama endpoint on loopback.
Cloud model tags (suffixed `:cloud`) are rejected. No project code, secrets, or
user data is transmitted to third-party inference endpoints.
