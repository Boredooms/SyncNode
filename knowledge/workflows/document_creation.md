---
id: document_creation
type: workflow
version: 1
trust: workflow
status: active
tags:
  - document
  - word
  - docx
  - writer
---

# Document Creation Workflow

1. Generate the content (writer agent) inside the approved workspace.
2. Create the document artifact (`document.create_docx`) using that content.
3. Verify the artifact exists, is structurally valid, and contains the content.
4. Optionally open it in Word and verify the application is running.
