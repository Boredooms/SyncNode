# Final E2E Workflow

## Verified golden run (model-driven)

Test: `tests/golden/test_true_desktop_office_email_e2e.py` — **PASSES**.

Observed step sequence (from a passing run, `ollama ps` GPU-resident):

```
generate_syncnode_content   writer.generate_paragraph   PASS  (content_generated)
create_docx_document        document.create_docx         PASS  (file_exists, run-scoped path)
search_for_word             computer.windows_search      PASS  (search_result_found)  <- Win+S, type, open
launch_word_application      computer.launch_app         PASS  (application_running: WINWORD.EXE)
navigate_to_email_client     browser.navigate            PASS  (page_loaded, local compose fixture)
type_recipient_email         browser.type                PASS  (field_value)
attach_document_to_email     browser.attach_file         PASS  (attachment_present, run-scoped docx)
<external-send>              policy approval gate         -> WAITING_APPROVAL (send NOT executed)
```

Evidence asserted by the test:
- final status == `waiting_approval`
- run-scoped artifact `workspace/demo/runs/<run_id>/word/SyncNode_Word_<id>.docx`
  with `run_id` in the path (no stale reuse)
- RAG required == true with provenance documents (approval_rules, workspace_rules,
  word, email_draft, document_creation)
- verifications persisted, all PASS
- audit chain present (74 events in one run)
- approval requested; send tool never executed
- model is local (not `:cloud`)

## Deterministic cross-application workflow

Test: `tests/golden/test_office_artifact_workflow.py` — **PASSES**. Excel
workbook → data flows into a Word report → PowerPoint summary, each verified by
`file_exists` + structure assertions, including model-style assertion synonyms
(`file_existence`, `spreadsheet_valid`).

## Failure injection

Test: `tests/golden/test_failure_injection_e2e.py` — **PASSES**. A false
model-success claim is caught by verification and the run is marked `failed`.

## Reproduce

```powershell
python scripts/start_server.py --port 8000    # in a terminal
python -m pytest tests/golden -v -s
```

Between runs: close Word and stray Playwright Chrome (run-scoped artifacts avoid
the previous docx-lock hazard, but Word may hold its own new file open).
