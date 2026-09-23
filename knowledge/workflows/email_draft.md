---
id: email_draft
type: workflow
version: 1
trust: workflow
status: active
tags:
  - email
  - browser
  - draft
  - approval
---

# Email Draft Workflow

1. Open the compose page in the browser.
2. Fill recipient, subject, and body.
3. Attach the required document (the created artifact).
4. Verify recipient value, attachment present, and that the message is NOT sent.
5. STOP at the human-approval boundary. The Send control must never be clicked
   without explicit approval (see `approval_rules`).
