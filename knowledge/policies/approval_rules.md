---
id: approval_rules
type: policy
version: 1
trust: authoritative_policy
status: active
tags:
  - approval
  - email
  - external
  - security
---

# Approval Rules

Any action that communicates externally requires explicit human approval before
it executes. The workflow must STOP at the approval boundary and never send.

- Sending an email, submitting a form, or clicking a Send control is
  EXTERNAL_COMMUNICATION and requires approval.
- Creating an email DRAFT (recipient, subject, body, attachment) is allowed
  without approval; only the send is gated.
- Destructive local actions (bulk delete, overwrite outside workspace) require
  approval.
- The model's own claim that an action is safe is never sufficient; the policy
  layer decides, and the approval boundary is enforced by the backend.
