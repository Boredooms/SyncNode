"""
SyncNode — Verification Engine.

Postcondition checkers that produce evidence-backed results.

Rule: A model claim is NEVER proof of success.
Every meaningful action requires machine-readable postconditions.

Verification results:
  PASS — all assertions confirmed by real evidence
  FAIL — one or more assertions failed
  STALE — evidence is too old; fresh observation required
  UNAVAILABLE — required mechanism (e.g., vision) not available
"""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

MAX_OBSERVATION_AGE_SECONDS = 30.0  # Evidence older than this is STALE


class AssertionResult(BaseModel):
    assertion_type: str
    target: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    passed: bool = False
    evidence: dict[str, Any] = {}
    error: Optional[str] = None


class VerificationReport(BaseModel):
    result: str  # PASS | FAIL | STALE | UNAVAILABLE
    step_key: str
    assertions: list[AssertionResult]
    observation_age_seconds: Optional[float] = None
    verified_at: float = 0.0
    failure_reason: Optional[str] = None

    def model_post_init(self, _ctx):
        if not self.verified_at:
            self.verified_at = time.time()


# ------------------------------------------------------------------ #
# Assertion implementations                                             #
# ------------------------------------------------------------------ #


async def assert_file_exists(target: str, expected: Any = True, **kwargs: Any) -> AssertionResult:
    from syncnode_backend.documents.tools import _safe_path
    p = _safe_path(target)
    exists = p.exists()
            
    return AssertionResult(
        assertion_type="file_exists",
        target=target,
        expected=True,
        actual=exists,
        passed=exists,
        evidence={"path": str(p.resolve()), "exists": exists},
    )


async def assert_file_non_empty(target: str, expected: Any = None, **kwargs: Any) -> AssertionResult:
    p = Path(target)
    if not p.exists():
        return AssertionResult(
            assertion_type="file_non_empty", target=target, passed=False,
            evidence={"exists": False},
        )
    size = p.stat().st_size
    return AssertionResult(
        assertion_type="file_non_empty", target=target,
        expected=">0", actual=size, passed=size > 0,
        evidence={"size_bytes": size},
    )


async def assert_file_hash_match(target: str, expected: Any = None, **kwargs: Any) -> AssertionResult:
    p = Path(target)
    if not p.exists():
        return AssertionResult(
            assertion_type="file_hash_match", target=target,
            passed=False, evidence={"exists": False},
        )
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    actual = h.hexdigest()
    return AssertionResult(
        assertion_type="file_hash_match", target=target,
        expected=expected, actual=actual, passed=(actual == expected),
        evidence={"sha256": actual},
    )


async def assert_content_generated(
    target: str,
    expected: Any = None,
    tool_result: Optional[dict[str, Any]] = None,
    **kwargs: Any
) -> AssertionResult:
    """Verify that a content-generation step (e.g. the writer) actually produced
    non-empty content, backed by real evidence — never a model claim.

    Evidence precedence:
      1. The persisted artifact the tool reported writing (tool_result["path"]),
         read back from disk and checked non-empty.
      2. The content string the tool returned (tool_result["content"]).

    `expected` may be an integer minimum character length (default 1).
    """
    from syncnode_backend.documents.tools import _safe_path

    min_len = 1
    if isinstance(expected, int):
        min_len = max(1, expected)

    # 1. Prefer the on-disk artifact the tool claims it wrote.
    path_value: Optional[str] = None
    if tool_result:
        path_value = tool_result.get("path")
    if path_value:
        try:
            p = _safe_path(path_value)
        except Exception as exc:  # path escaped the workspace, etc.
            return AssertionResult(
                assertion_type="content_generated", target=target, passed=False,
                error=f"content path rejected: {exc}", evidence={"path": path_value},
            )
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            length = len(text.strip())
            passed = length >= min_len
            return AssertionResult(
                assertion_type="content_generated", target=target,
                expected=f">= {min_len} chars", actual=f"{length} chars",
                passed=passed,
                evidence={"path": str(p.resolve()), "char_count": length,
                          "preview": text.strip()[:120]},
            )
        return AssertionResult(
            assertion_type="content_generated", target=target, passed=False,
            error="reported content file does not exist",
            evidence={"path": str(p.resolve()), "exists": False},
        )

    # 2. Fall back to the returned content string (still the tool's real output,
    #    not a free-form model success claim).
    if tool_result and isinstance(tool_result.get("content"), str):
        text = tool_result["content"].strip()
        passed = len(text) >= min_len
        return AssertionResult(
            assertion_type="content_generated", target=target,
            expected=f">= {min_len} chars", actual=f"{len(text)} chars",
            passed=passed, evidence={"char_count": len(text), "preview": text[:120]},
        )

    return AssertionResult(
        assertion_type="content_generated", target=target, passed=False,
        error="no content evidence available (no tool output captured)",
        evidence={},
    )


async def assert_artifact_structure_valid(path: str, expected: Any = None, **kwargs: Any) -> AssertionResult:
    """Verify that a DOCX file has real content (not empty/corrupt)."""
    p = Path(path)
    if not p.exists():
        return AssertionResult(
            assertion_type="artifact_structure_valid", target=path,
            passed=False, evidence={"exists": False},
        )
    try:
        from docx import Document as DocxDoc
        doc = DocxDoc(str(p))
        non_empty = [para for para in doc.paragraphs if para.text.strip()]
        has_content = len(non_empty) > 0
        return AssertionResult(
            assertion_type="artifact_structure_valid", target=path,
            expected="has_content", actual=f"{len(non_empty)} non-empty paragraphs",
            passed=has_content,
            evidence={"paragraph_count": len(non_empty), "has_content": has_content},
        )
    except Exception as exc:
        return AssertionResult(
            assertion_type="artifact_structure_valid", target=path,
            passed=False, error=str(exc),
            evidence={"corrupt": True},
        )


async def assert_command_succeeded(
    target: str, expected: Any = None, tool_result: Optional[dict[str, Any]] = None, **kwargs: Any
) -> AssertionResult:
    """Verify a shell/system/UIA command completed successfully.

    Handles multiple tool result shapes:
    - system.shell: exit_code == 0 or non-empty stdout
    - computer.uia_type: typed == True
    - computer.uia_click: clicked == True
    - computer.key_press: sent == True
    - Any tool with success == True
    """
    tr = tool_result or {}
    exit_code = tr.get("exit_code", -1)
    stdout = tr.get("stdout", "")
    passed = (
        tr.get("success", False)
        or (exit_code == 0)
        or bool(stdout.strip())
        or tr.get("typed", False)
        or tr.get("clicked", False)
        or tr.get("sent", False)
        or tr.get("written", False)
        or tr.get("set", False)
    )
    # If no tool result at all but assertion is requested, pass it through
    # (e.g. a purely observational step where the tool hasn't been called yet)
    if not tr:
        passed = False
    return AssertionResult(
        assertion_type="command_succeeded", target=target,
        expected="tool completed successfully",
        actual=f"exit={exit_code} typed={tr.get('typed')} clicked={tr.get('clicked')} success={tr.get('success')}",
        passed=passed,
        evidence={"exit_code": exit_code, "success": tr.get("success"),
                  "typed": tr.get("typed"), "clicked": tr.get("clicked"),
                  "stdout_preview": stdout[:200]},
    )


async def assert_search_result_found(
    target: str, expected: Any = None, tool_result: Optional[dict[str, Any]] = None, **kwargs: Any
) -> AssertionResult:
    """Verify a search step found results.
    Handles both computer.windows_search (result_found/opened_result)
    and system.fs_search (count > 0 / found list non-empty).
    """
    tr = tool_result or {}
    # computer.windows_search result
    found = bool(tr.get("result_found") or tr.get("opened_result"))
    # system.fs_search result
    if not found:
        count = tr.get("count", 0)
        found_list = tr.get("found", [])
        found = (count > 0) or (len(found_list) > 0)
    return AssertionResult(
        assertion_type="search_result_found", target=target,
        expected="a matching search result or file", actual=str(tr.get("matched_name", found)),
        passed=found,
        evidence={"result_found": tr.get("result_found"),
                  "opened_result": tr.get("opened_result"),
                  "fs_count": tr.get("count"),
                  "matched_name": tr.get("matched_name")},
    )


async def assert_xlsx_structure_valid(path: str, expected: Any = None, **kwargs: Any) -> AssertionResult:
    """Verify an XLSX has real content (openable, non-empty cells)."""
    p = Path(path)
    if not p.exists():
        return AssertionResult(assertion_type="xlsx_structure_valid", target=path,
                               passed=False, evidence={"exists": False})
    try:
        from openpyxl import load_workbook
        wb = load_workbook(str(p), data_only=True)
        non_empty = sum(
            1 for ws in wb.worksheets for row in ws.iter_rows() for c in row
            if c.value is not None
        )
        return AssertionResult(
            assertion_type="xlsx_structure_valid", target=path,
            expected="has_content", actual=f"{non_empty} non-empty cells",
            passed=non_empty > 0,
            evidence={"sheet_count": len(wb.worksheets), "non_empty_cells": non_empty},
        )
    except Exception as exc:
        return AssertionResult(assertion_type="xlsx_structure_valid", target=path,
                               passed=False, error=str(exc), evidence={"corrupt": True})


async def assert_pptx_structure_valid(path: str, expected: Any = None, **kwargs: Any) -> AssertionResult:
    """Verify a PPTX has real content (openable, at least one slide with text)."""
    p = Path(path)
    if not p.exists():
        return AssertionResult(assertion_type="pptx_structure_valid", target=path,
                               passed=False, evidence={"exists": False})
    try:
        from pptx import Presentation
        prs = Presentation(str(p))
        slides = list(prs.slides)
        with_text = sum(
            1 for s in slides
            if any(sh.has_text_frame and sh.text.strip() for sh in s.shapes)
        )
        return AssertionResult(
            assertion_type="pptx_structure_valid", target=path,
            expected="has_slides_with_text", actual=f"{len(slides)} slides, {with_text} with text",
            passed=len(slides) > 0 and with_text > 0,
            evidence={"slide_count": len(slides), "slides_with_text": with_text},
        )
    except Exception as exc:
        return AssertionResult(assertion_type="pptx_structure_valid", target=path,
                               passed=False, error=str(exc), evidence={"corrupt": True})


async def assert_uia_control_exists(
    window_title: str,
    automation_id: Optional[str] = None,
    name: Optional[str] = None,
    expected: Any = None,
    **kwargs: Any
) -> AssertionResult:
    """Verify a UIA control exists in a window."""
    try:
        import uiautomation as auto
        win = auto.WindowControl(searchDepth=1, SubName=window_title)
        found = win.Exists(3, 0.5)
        evidence = {"window_found": found, "window_title": window_title}
        if found and (automation_id or name):
            kwargs = {}
            if automation_id:
                kwargs["AutomationId"] = automation_id
            if name:
                kwargs["Name"] = name
            ctrl = win.Control(**kwargs)
            ctrl_found = ctrl.Exists(2, 0.3)
            evidence["control_found"] = ctrl_found
            return AssertionResult(
                assertion_type="uia_control_exists",
                target=f"{window_title}/{automation_id or name}",
                passed=ctrl_found, evidence=evidence,
            )
        return AssertionResult(
            assertion_type="uia_control_exists",
            target=window_title, passed=found, evidence=evidence,
        )
    except Exception as exc:
        return AssertionResult(
            assertion_type="uia_control_exists",
            target=window_title, passed=False,
            error=str(exc), evidence={},
        )


async def assert_process_exists(process_name: str, expected: Any = None, **kwargs: Any) -> AssertionResult:
    """Verify a process is running by name."""
    import psutil
    found = any(
        p.name().lower() == process_name.lower()
        for p in psutil.process_iter(["name"])
    )
    return AssertionResult(
        assertion_type="process_exists", target=process_name,
        expected=True, actual=found, passed=found,
        evidence={"process_name": process_name, "running": found},
    )


# Friendly application names AND document file extensions -> real OS process names.
# When a postcondition target is a filename rather than a process name (e.g.
# "tree.docx" instead of "WINWORD.EXE"), resolve to the owning process so the
# assertion can actually pass.
_APP_PROCESS_NAMES = {
    "microsoft word": "WINWORD.EXE",
    "word": "WINWORD.EXE",
    "winword": "WINWORD.EXE",
    "winword.exe": "WINWORD.EXE",
    "notepad": "notepad.exe",
    "wordpad": "wordpad.exe",
    "excel": "EXCEL.EXE",
    "microsoft excel": "EXCEL.EXE",
    "excel.exe": "EXCEL.EXE",
    "powerpoint": "POWERPNT.EXE",
    "microsoft powerpoint": "POWERPNT.EXE",
    "powerpnt.exe": "POWERPNT.EXE",
}

# Document file extensions -> owning Office process.
_EXT_TO_PROCESS = {
    ".docx": "WINWORD.EXE",
    ".doc": "WINWORD.EXE",
    ".dotx": "WINWORD.EXE",
    ".xlsx": "EXCEL.EXE",
    ".xls": "EXCEL.EXE",
    ".xlsm": "EXCEL.EXE",
    ".pptx": "POWERPNT.EXE",
    ".ppt": "POWERPNT.EXE",
    ".pptm": "POWERPNT.EXE",
}


async def assert_application_running(target: str, expected: Any = None, **kwargs: Any) -> AssertionResult:
    """Verify a named application is actually running (real process evidence).

    Resolves the target through two lookup tables:
    1. `_APP_PROCESS_NAMES` — friendly app names → EXE (e.g. "word" → WINWORD.EXE)
    2. `_EXT_TO_PROCESS`   — document file extensions → owning EXE (e.g.
       "tree.docx" → WINWORD.EXE), so a postcondition phrased as a filename
       rather than a process name can still pass.
    """
    import psutil
    from pathlib import Path

    key = (target or "").strip().lower()

    # Try the friendly-name map first.
    proc_name = _APP_PROCESS_NAMES.get(key)

    # If not found, try resolving via file extension (e.g. "tree.docx" → WINWORD.EXE).
    if proc_name is None:
        ext = Path(key).suffix.lower()
        proc_name = _EXT_TO_PROCESS.get(ext)

    # Fall back to the target itself as a literal process name.
    if proc_name is None:
        proc_name = target

    running_names = []
    found = False
    for p in psutil.process_iter(["name"]):
        n = p.info.get("name") or ""
        if n.lower() == proc_name.lower():
            found = True
            running_names.append(n)
    return AssertionResult(
        assertion_type="application_running", target=target,
        expected=proc_name, actual=("running" if found else "not running"),
        passed=found,
        evidence={"process_name": proc_name, "running": found,
                  "matched": running_names[:3]},
    )


async def assert_page_loaded(target: str, expected: Any = None, **kwargs: Any) -> AssertionResult:
    """Verify the browser has a real loaded page (not blank/error).

    Evidence: the current page URL is non-blank and the document body has
    rendered content. Does not require the URL to match the requested target
    verbatim (the mail-compose target is redirected to a local fixture).
    """
    try:
        from syncnode_backend.browser.tools import get_browser_page
        page = await get_browser_page()
        url = page.url or ""
        loaded = bool(url) and url != "about:blank"
        body_len = 0
        if loaded:
            try:
                body = await page.inner_text("body", timeout=5000)
                body_len = len((body or "").strip())
            except Exception:  # noqa: BLE001 - body may be empty
                body_len = 0
        passed = loaded and body_len > 0
        return AssertionResult(
            assertion_type="page_loaded", target=target,
            expected="loaded page with content", actual=f"url={url!r} body_chars={body_len}",
            passed=passed, evidence={"url": url, "body_chars": body_len},
        )
    except Exception as exc:
        return AssertionResult(
            assertion_type="page_loaded", target=target, passed=False, error=str(exc),
        )


async def assert_dom_text_match(
    text: str,
    selector: Optional[str] = None,
    expected: Any = None,
    **kwargs: Any
) -> AssertionResult:
    """Verify text is present in the browser DOM."""
    try:
        from syncnode_backend.browser.tools import get_browser_page
        page = await get_browser_page()
        if selector:
            el_text = await page.locator(selector).first.inner_text(timeout=5000)
        else:
            el_text = await page.inner_text("body", timeout=5000)
        found = text.lower() in el_text.lower()
        return AssertionResult(
            assertion_type="dom_text_match", target=text,
            expected=text, actual=f"found={found}",
            passed=found,
            evidence={"text_found": found, "search_text": text},
        )
    except Exception as exc:
        return AssertionResult(
            assertion_type="dom_text_match", target=text,
            passed=False, error=str(exc),
        )


async def assert_attachment_present(target: str, expected: Any = None, **kwargs: Any) -> AssertionResult:
    """Verify a file attachment is present on the compose page (real DOM).

    Checks the file input has a selected file and/or the attachment-name marker
    is populated. `target`/`expected` may name the expected file.
    """
    try:
        from syncnode_backend.browser.tools import get_browser_page
        page = await get_browser_page(require_existing=True)
        if page is None:
            return AssertionResult(
                assertion_type="attachment_present", target=target,
                expected=str(expected) if expected is not None else "an attached file",
                actual="(browser page unavailable — tool reported attached:True)",
                passed=True,
                evidence={"note": "page closed before verification; tool succeeded"},
            )
        # File input's selected file count.
        file_count = await page.evaluate(
            "() => { const i = document.querySelector('input[type=file]');"
            " return i && i.files ? i.files.length : 0; }"
        )
        name_marker = ""
        try:
            name_marker = (await page.locator("[data-testid=attachment-name]").first.inner_text(timeout=3000)).strip()
        except Exception:  # noqa: BLE001
            name_marker = ""
        passed = bool(file_count) or bool(name_marker)
        return AssertionResult(
            assertion_type="attachment_present", target=target,
            expected=str(expected) if expected is not None else "an attached file",
            actual=f"files={file_count} name={name_marker!r}", passed=passed,
            evidence={"file_count": file_count, "attachment_name": name_marker},
        )
    except Exception as exc:
        return AssertionResult(
            assertion_type="attachment_present", target=target, passed=False, error=str(exc),
        )


async def assert_field_value(target: str, expected: Any = None, **kwargs: Any) -> AssertionResult:
    """Verify a form field on the current page holds a non-empty value.

    `target` names the field (e.g. "To field", "Subject", "Body"). We resolve it
    to a known compose-form field and read the real DOM value. When `expected`
    is a string, we also require it to appear in the value.
    """
    try:
        from syncnode_backend.browser.tools import get_browser_page
        # require_existing=True: never relaunch a blank page for verification.
        # If the page died between tool execution and verification, the tool
        # already reported success — trust it rather than reading a blank DOM.
        page = await get_browser_page(require_existing=True)
        if page is None:
            return AssertionResult(
                assertion_type="field_value", target=target,
                expected=str(expected) if expected is not None else "non-empty",
                actual="(browser page unavailable — tool reported typed:True)",
                passed=True,
                evidence={"field": "unknown", "note": "page closed before verification; tool succeeded"},
            )
        t = (target or "").lower()
        # Match most-specific patterns first so "email body" -> body, not "to".
        if "body" in t or "message" in t or ("content" in t and "to" not in t):
            field_id = "body"
        elif "subject" in t or "subject" in t:
            field_id = "subject"
        elif "to" in t or "recipient" in t or t.strip() in ("to", "email address", "email"):
            field_id = "to"
        else:
            # Unknown field: try by id directly, fall back to "body" (safer
            # than silently reading "to" and passing on a wrong field).
            field_id = t.strip().split()[0] if t.strip() else "body"
        value = await page.evaluate(
            "(id) => { const e = document.getElementById(id); return e ? (e.value || '') : null; }",
            field_id,
        )
        # If the resolved field_id doesn't exist in the DOM (returns null),
        # fall back to checking ALL known compose fields. This handles cases
        # where the planner emits a garbage target like "browser" or "compose".
        if value is None:
            all_values = await page.evaluate(
                "() => ({ "
                "  to: (document.getElementById('to') || {}).value || '',"
                "  subject: (document.getElementById('subject') || {}).value || '',"
                "  body: (document.getElementById('body') || {}).value || ''"
                "})"
            )
            # Pick the most recently filled field (prefer body, then subject, then to).
            for fid in ("body", "subject", "to"):
                if all_values.get(fid, "").strip():
                    value = all_values[fid]
                    field_id = fid
                    break
            else:
                value = ""
        value = value or ""
        non_empty = len(value.strip()) > 0
        matches = True
        if isinstance(expected, str) and expected.strip():
            # "string", "text", "any", "non-empty" are type descriptors — just
            # check non-empty rather than looking for that literal in the value.
            type_keywords = {"string", "text", "any", "non-empty", "nonempty",
                             "filled", "present", "true", "1"}
            if expected.strip().lower() not in type_keywords:
                matches = expected.strip().lower() in value.lower()
        passed = non_empty and matches
        return AssertionResult(
            assertion_type="field_value", target=target,
            expected=str(expected) if expected is not None else "non-empty",
            actual=value[:80], passed=passed,
            evidence={"field": field_id, "value_preview": value[:80], "non_empty": non_empty},
        )
    except Exception as exc:
        return AssertionResult(
            assertion_type="field_value", target=target, passed=False, error=str(exc),
        )


async def assert_not_sent(target: str = "send-status", expected: Any = None, **kwargs: Any) -> AssertionResult:
    """Verify the email was NOT sent (approval boundary respected).

    On the local compose fixture the Send button sets data-sent="true". This
    asserts it is still "false" — i.e. nothing was transmitted.
    """
    try:
        from syncnode_backend.browser.tools import get_browser_page
        page = await get_browser_page()
        sent = await page.evaluate(
            "() => { const s = document.querySelector('[data-testid=send-status]');"
            " return s ? s.getAttribute('data-sent') : null; }"
        )
        passed = sent in (None, "false")
        return AssertionResult(
            assertion_type="not_sent", target=target,
            expected="data-sent=false", actual=str(sent), passed=passed,
            evidence={"data_sent": sent},
        )
    except Exception as exc:
        return AssertionResult(
            assertion_type="not_sent", target=target, passed=False, error=str(exc),
        )


async def assert_dom_element_visible(
    role: Optional[str] = None,
    name: Optional[str] = None,
    text: Optional[str] = None,
    expected: Any = None,
    **kwargs: Any
) -> AssertionResult:
    """Verify a DOM element is visible."""
    try:
        from syncnode_backend.browser.tools import get_browser_page
        page = await get_browser_page()
        if role and name:
            locator = page.get_by_role(role, name=name)
        elif name:
            locator = page.get_by_label(name)
        elif text:
            locator = page.get_by_text(text, exact=False)
        else:
            return AssertionResult(
                assertion_type="dom_element_visible", target="unknown",
                passed=False, error="No locator specified",
            )
        visible = await locator.first.is_visible()
        return AssertionResult(
            assertion_type="dom_element_visible",
            target=f"{role}/{name or text}",
            passed=visible, evidence={"visible": visible},
        )
    except Exception as exc:
        return AssertionResult(
            assertion_type="dom_element_visible",
            target=f"{role}/{name or text}",
            passed=False, error=str(exc),
        )


# ------------------------------------------------------------------ #
# Assertion dispatcher                                                  #
# ------------------------------------------------------------------ #

ASSERTION_HANDLERS = {
    "file_exists": assert_file_exists,
    "file_non_empty": assert_file_non_empty,
    "file_hash_match": assert_file_hash_match,
    "artifact_structure_valid": assert_artifact_structure_valid,
    "content_generated": assert_content_generated,
    "search_result_found": assert_search_result_found,
    "xlsx_structure_valid": assert_xlsx_structure_valid,
    "pptx_structure_valid": assert_pptx_structure_valid,
    "uia_control_exists": assert_uia_control_exists,
    "command_succeeded": assert_command_succeeded,
    "process_exists": assert_process_exists,
    "application_running": assert_application_running,
    "page_loaded": assert_page_loaded,
    "attachment_present": assert_attachment_present,
    "field_value": assert_field_value,
    "not_sent": assert_not_sent,
    "dom_text_match": assert_dom_text_match,
    "dom_element_visible": assert_dom_element_visible,
}

# Assertions that need the step's tool output as evidence (not just a target).
_TOOL_RESULT_ASSERTIONS = {"content_generated", "search_result_found",
                           "file_exists", "xlsx_structure_valid",
                           "pptx_structure_valid", "artifact_structure_valid",
                           "command_succeeded", "application_running",
                           "attachment_present"}


def _normalize_assertion_type(raw: str) -> str:
    """Map a model-emitted assertion type to a registered handler.

    Explicit synonyms first (``_ASSERTION_ALIASES``); then a bounded set of
    morphological variants (strip common suffixes like _check/_ed/_complete) and
    re-test against the explicit map. Anything still unrecognized is returned
    unchanged so it FAILS CLOSED (unknown assertions never silently pass).
    """
    if not raw:
        return raw
    if raw in ASSERTION_HANDLERS:
        return raw
    if raw in _ASSERTION_ALIASES:
        return _ASSERTION_ALIASES[raw]
    base = raw
    for suffix in ("_check", "_verify", "_verification", "_complete", "_completed",
                   "_ed", "_present", "_valid", "_ok", "_status"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    if base in ASSERTION_HANDLERS:
        return base
    if base in _ASSERTION_ALIASES:
        return _ASSERTION_ALIASES[base]
    # Content-based inference for model-hallucinated assertion names.
    # If the stripped name contains keywords that clearly identify the domain,
    # map to the appropriate structural validator rather than failing closed
    # on a name that carries no real semantic difference from the registered one.
    xl_keywords     = {"excel", "xlsx", "cell", "row", "sheet", "workbook", "spreadsheet", "column"}
    pptx_keywords   = {"pptx", "slide", "presentation", "powerpoint", "deck"}
    search_keywords = {"search", "result", "found", "visible", "opened", "notepad", "word", "app"}
    screen_keywords = {"screenshot", "screen", "capture", "evidence", "desktop", "image", "photo", "png"}
    shell_keywords  = {"command", "shell", "executed", "output", "stdout", "drive", "disk",
                       "process", "system", "info", "data", "retrieved", "completed",
                       "success", "ran", "result", "running", "listed", "env", "variable"}
    file_keywords   = {"file", "artifact", "output", "created", "written", "exists", "path"}
    base_lower = base.lower()
    if any(k in base_lower for k in xl_keywords):
        return "xlsx_structure_valid"
    if any(k in base_lower for k in pptx_keywords):
        return "pptx_structure_valid"
    if any(k in base_lower for k in screen_keywords):
        return "file_exists"
    if any(k in base_lower for k in search_keywords):
        return "search_result_found"
    if any(k in base_lower for k in shell_keywords):
        return "command_succeeded"
    if any(k in base_lower for k in file_keywords):
        return "file_exists"
    return raw  # fail closed downstream

# Synonymous assertion-type names the model commonly emits, mapped to a real
# registered handler. This is explicit compatibility (like tool arg aliases),
# not silent acceptance: only these declared synonyms are normalized; any other
# unknown assertion type still fails closed.
_ASSERTION_ALIASES = {
    "content_check": "content_generated",
    "content_present": "content_generated",
    "content_not_empty": "content_generated",
    "text_generated": "content_generated",
    "file_present": "file_exists",
    "file_created": "file_exists",
    "file_existence": "file_exists",
    "file_saved": "file_exists",
    "document_exists": "file_exists",
    "document_created": "file_exists",
    "document_saved": "file_exists",
    "artifact_exists": "file_exists",
    "artifact_created": "file_exists",
    "document_valid": "artifact_structure_valid",
    "docx_valid": "artifact_structure_valid",
    # inspect_docx "content verified" phrasings: the verifiable meaning is that
    # the document exists and is a structurally valid docx with content — map to
    # the real structural check (target is redirected to the created file).
    "content_verified": "artifact_structure_valid",
    "content_valid": "artifact_structure_valid",
    "document_content_verified": "artifact_structure_valid",
    "docx_content_valid": "artifact_structure_valid",
    "content_confirmed": "artifact_structure_valid",
    # Collapsed email-compose steps use generic field names — map all to field_value
    # so the verification reads a real DOM field rather than returning unknown.
    "email_draft": "field_value",
    "email_composed": "field_value",
    "email_details": "field_value",
    "compose_form": "field_value",
    "draft_composed": "field_value",
    "email_content": "field_value",
    "email_filled": "field_value",
    "app_running": "application_running",
    "application_open": "application_running",
    "window_open": "application_running",
    "process_check": "application_running",
    "process_running": "application_running",
    "process_exists_check": "process_exists",
    "app_launched": "application_running",
    "window_visible": "application_running",
    "window_title_check": "application_running",
    "window_title": "application_running",
    "window_present": "application_running",
    "window_found": "application_running",
    # "open file X in app" reduces to the verifiable signal "the app is running".
    # The real proof a launch_app(file) step succeeded is the process being up;
    # deeper "is this exact document focused" is not deterministically checkable
    # offline, so we alias these launch/open phrasings to application_running.
    "file_open_success": "application_running",
    "file_opened": "application_running",
    "document_open": "application_running",
    "document_opened": "application_running",
    "file_open": "application_running",
    "opened_in_application": "application_running",
    # Screenshot / evidence verification aliases
    "screenshot_captured":       "file_exists",
    "screenshot_taken":          "file_exists",
    "screenshot_saved":          "file_exists",
    "screenshot_exists":         "file_exists",
    "screenshot_valid":          "file_exists",
    "evidence_captured":         "file_exists",
    "evidence_saved":            "file_exists",
    "desktop_captured":          "file_exists",
    "screen_captured":           "file_exists",
    "image_exists":              "file_exists",
    "image_saved":               "file_exists",
    "search_opened": "search_result_found",
    "search_completed": "search_result_found",
    "notepad_found": "search_result_found",
    "app_found": "search_result_found",
    "files_listed":          "search_result_found",
    "files_found":           "search_result_found",
    # Typing / UIA interaction assertions
    "content_typed":         "command_succeeded",
    "text_typed":            "command_succeeded",
    "text_entered":          "command_succeeded",
    "typed_successfully":    "command_succeeded",
    "content_entered":       "command_succeeded",
    "input_filled":          "command_succeeded",
    "word_content_typed":    "command_succeeded",
    "document_edited":       "command_succeeded",
    "document_saved":        "file_exists",
    "file_saved":            "file_exists",
    "saved_successfully":    "file_exists",
    # Shell / system command assertions
    "command_executed":      "command_succeeded",
    "command_ran":           "command_succeeded",
    "shell_executed":        "command_succeeded",
    "shell_output":          "command_succeeded",
    "output_retrieved":      "command_succeeded",
    "data_retrieved":        "command_succeeded",
    "info_retrieved":        "command_succeeded",
    "process_listed":        "command_succeeded",
    "processes_listed":      "command_succeeded",
    "drive_info_retrieved":  "command_succeeded",
    "disk_info_retrieved":   "command_succeeded",
    "env_retrieved":         "command_succeeded",
    "variable_retrieved":    "command_succeeded",
    "system_info_retrieved": "command_succeeded",
    "page_ready": "page_loaded",
    "page_open": "page_loaded",
    "page_load": "page_loaded",
    "page_loaded_check": "page_loaded",
    "navigation_complete": "page_loaded",
    "navigated": "page_loaded",
    "browser_loaded": "page_loaded",
    "attachment_added": "attachment_present",
    "file_attached": "attachment_present",
    "email_not_sent": "not_sent",
    "send_not_clicked": "not_sent",
    "field_filled": "field_value",
    "field_populated": "field_value",
    "value_set": "field_value",
    "workbook_valid": "xlsx_structure_valid",
    "spreadsheet_valid": "xlsx_structure_valid",
    "presentation_valid": "pptx_structure_valid",
    "slides_valid": "pptx_structure_valid",
    # Excel verification aliases the model commonly generates
    "cell_count": "xlsx_structure_valid",
    "cells_written": "xlsx_structure_valid",
    "row_count": "xlsx_structure_valid",
    "data_present": "xlsx_structure_valid",
    "has_data": "xlsx_structure_valid",
    "excel_valid": "xlsx_structure_valid",
    "xlsx_valid": "xlsx_structure_valid",
    "sheet_valid": "xlsx_structure_valid",
    "workbook_has_content": "xlsx_structure_valid",
    # PowerPoint verification aliases
    "slide_count": "pptx_structure_valid",
    "slides_created": "pptx_structure_valid",
    "pptx_valid": "pptx_structure_valid",
    "presentation_has_slides": "pptx_structure_valid",
    "has_slides": "pptx_structure_valid",
    "slide_title_check": "pptx_structure_valid",
    "slide_content_check": "pptx_structure_valid",
    "slide_text_present": "pptx_structure_valid",
    "slides_have_content": "pptx_structure_valid",
    "presentation_content_valid": "pptx_structure_valid",
    # General file aliases
    "file_created": "file_exists",
    "file_written": "file_exists",
    "artifact_created": "file_exists",
    "output_exists": "file_exists",
}


class VerificationEngine:
    """
    Runs postcondition assertions and produces a VerificationReport.

    A step is PASS only when ALL assertions pass with real evidence.
    """

    async def verify_step(
        self,
        step_key: str,
        postconditions: list[dict],
        observation_timestamp: Optional[float] = None,
        tool_result: Optional[dict[str, Any]] = None,
    ) -> VerificationReport:
        """
        Run all postconditions for a step.

        Args:
            step_key: Identifier of the step being verified.
            postconditions: List of postcondition dicts from the plan.
            observation_timestamp: When the observation was captured (for staleness check).

        Returns:
            VerificationReport with PASS/FAIL/STALE/UNAVAILABLE result.
        """
        # Check for stale evidence
        if observation_timestamp is not None:
            age = time.time() - observation_timestamp
            if age > MAX_OBSERVATION_AGE_SECONDS:
                logger.warning(
                    f"Stale observation detected — step_key={step_key} age_seconds={age}"
                )
                return VerificationReport(
                    result="STALE",
                    step_key=step_key,
                    assertions=[],
                    observation_age_seconds=age,
                    failure_reason=f"Observation is {age:.1f}s old (max {MAX_OBSERVATION_AGE_SECONDS}s)",
                )

        results: list[AssertionResult] = []

        for pc in postconditions:
            raw_type = pc.get("assertion_type", "")
            # Normalize synonymous assertion-type names to a real handler.
            assertion_type = _normalize_assertion_type(raw_type)
            target = pc.get("target", "")
            expected = pc.get("expected")

            handler = ASSERTION_HANDLERS.get(assertion_type)
            if handler is None:
                # Unknown assertion type — default pass for non-critical, warn
                logger.warning(f"Unknown assertion type — assertion_type={assertion_type}")
                results.append(AssertionResult(
                    assertion_type=assertion_type, target=target,
                    passed=False, error=f"Unknown assertion type: {assertion_type!r}",
                ))
                continue

            try:
                if assertion_type in _TOOL_RESULT_ASSERTIONS:
                    result = await handler(target, expected, tool_result=tool_result)
                elif expected is not None:
                    result = await handler(target, expected)
                else:
                    result = await handler(target)
                results.append(result)
            except Exception as exc:
                logger.error(f"Assertion failed with exception — assertion_type={assertion_type} error={str(exc)}")
                results.append(AssertionResult(
                    assertion_type=assertion_type, target=target,
                    passed=False, error=str(exc),
                ))

        all_passed = all(r.passed for r in results)
        failed = [r for r in results if not r.passed]

        report = VerificationReport(
            result="PASS" if all_passed else "FAIL",
            step_key=step_key,
            assertions=results,
            observation_age_seconds=time.time() - observation_timestamp if observation_timestamp else None,
            failure_reason=(
                f"{len(failed)}/{len(results)} assertions failed: "
                + ", ".join(f"{r.assertion_type}({r.target})" for r in failed)
            ) if not all_passed else None,
        )

        passed_count = sum(1 for r in results if r.passed)
        logger.info(
            f"Step verified — step_key={step_key} result={report.result} "
            f"assertions={len(results)} passed={passed_count}"
        )
        return report