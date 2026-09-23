"""Verification assertion-alias tests (Phase J hardening)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from syncnode_backend.verification.engine import (  # noqa: E402
    VerificationEngine, _ASSERTION_ALIASES,
)


@pytest.mark.asyncio
async def test_content_check_alias_routes_to_content_generated(tmp_path, monkeypatch):
    import syncnode_backend.documents.tools as doc_tools
    monkeypatch.setattr(doc_tools, "_get_workspace_root", lambda: tmp_path)
    (tmp_path / "generated_paragraph.txt").write_text("A real paragraph.", encoding="utf-8")

    eng = VerificationEngine()
    report = await eng.verify_step(
        step_key="gen",
        postconditions=[{"assertion_type": "content_check", "target": "writer_output"}],
        tool_result={"path": "generated_paragraph.txt", "content": "A real paragraph."},
    )
    assert report.result == "PASS"


@pytest.mark.asyncio
async def test_unknown_assertion_still_fails_closed(tmp_path):
    eng = VerificationEngine()
    report = await eng.verify_step(
        step_key="x",
        postconditions=[{"assertion_type": "totally_made_up_check", "target": "y"}],
    )
    assert report.result == "FAIL"


def test_aliases_map_to_real_handlers():
    from syncnode_backend.verification.engine import ASSERTION_HANDLERS
    for alias, real in _ASSERTION_ALIASES.items():
        assert real in ASSERTION_HANDLERS, f"{alias} -> {real} not a real handler"


@pytest.mark.parametrize(
    "alias",
    [
        "file_open_success",
        "file_opened",
        "document_open",
        "document_opened",
        "file_open",
        "opened_in_application",
    ],
)
def test_file_open_family_aliases_to_application_running(alias):
    """"Open file X in app" phrasings reduce to the verifiable "app is running"
    signal so a launch_app(file) step is not failed over model-phrasing variance."""
    assert _ASSERTION_ALIASES[alias] == "application_running"


def test_retry_policy_coerces_scalar_backoff_ms():
    """The planner often emits backoff_ms as a single int; it must be coerced
    into a schedule list instead of triggering an expensive full-plan repair."""
    from syncnode_ai.planner.schemas import RetryPolicy

    assert RetryPolicy(backoff_ms=1000).backoff_ms == [1000, 2000, 4000]
    assert RetryPolicy(backoff_ms=None).backoff_ms == [250, 1000, 4000]
    assert RetryPolicy(backoff_ms="500").backoff_ms == [500, 1000, 2000]
    assert RetryPolicy(backoff_ms=[100, 200]).backoff_ms == [100, 200]
    # Non-numeric junk falls back to the safe default schedule.
    assert RetryPolicy(backoff_ms="oops").backoff_ms == [250, 1000, 4000]


@pytest.mark.parametrize(
    "goal,ext,expected",
    [
        ("write a paragraph of a tree in a word document and save it as tree.docx", ".docx", "tree.docx"),
        ("create the Q3 report and call it q3_report.xlsx", ".xlsx", "q3_report.xlsx"),
        ("make a deck named summary.pptx for the team", ".pptx", "summary.pptx"),
        ("just write a short note", ".docx", ""),            # no filename in goal
        ("save it as tree.docx", ".xlsx", ""),               # ext mismatch -> no match
    ],
)
def test_filename_extracted_from_goal(goal, ext, expected):
    """The user's requested filename (e.g. 'tree.docx') is honored, capturing
    only the final token before the extension — not the whole sentence."""
    from syncnode_backend.workflow.orchestrator import SyncNodeOrchestrator

    orch = SyncNodeOrchestrator.__new__(SyncNodeOrchestrator)
    orch._goal = goal
    orch._artifacts = {}   # enricher cache empty — fall back to regex
    assert orch._filename_from_goal(ext) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("paragraph_content", True),
        ("generated_content", True),
        ("tree_content", True),
        ("content", True),
        ("writer_output", True),
        ("step1_output", True),
        ("A real paragraph about trees, with punctuation.", False),  # real prose
        ("The tree stood tall.", False),
        ("", False),
        ("update.docx", False),   # a filename, not a content ref
    ],
)
def test_looks_like_field_ref(value, expected):
    """Bare symbolic content tokens (e.g. 'paragraph_content') must be detected
    so they are replaced by the writer's real output instead of written verbatim."""
    from syncnode_backend.workflow.orchestrator import SyncNodeOrchestrator
    assert SyncNodeOrchestrator._looks_like_field_ref(value) is expected
