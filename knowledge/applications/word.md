---
id: word
type: application
version: 1
trust: reference
status: active
tags:
  - microsoft
  - office
  - word
  - docx
---

# Microsoft Word

Preferred opening: the computer runtime `computer.launch_app` with `executable`
= "word" and the document path as an argument.

Fallback: Windows UIA to locate the window.

Required verification after launch:
- process exists (WINWORD.EXE)
- expected window title present
- the saved artifact exists on disk with real content

Known failure: Word not on PATH.
Recovery: resolve the install path via the Windows App Paths registry before
launching.
