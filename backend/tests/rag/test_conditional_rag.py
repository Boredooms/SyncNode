"""Conditional RAG tests (Phase F): requirement detection + retrieval + provenance."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "ai_ml" / "src"))

from syncnode_ai.rag.conditional import ConditionalRAG, detect_knowledge_requirement  # noqa: E402


def test_trivial_task_skips_rag():
    required, reason, tags = detect_knowledge_requirement("Say hello in one sentence.")
    assert required is False


def test_office_task_requires_rag():
    required, reason, tags = detect_knowledge_requirement(
        "Create an Excel workbook, then a Word report, and email a draft with it attached."
    )
    assert required is True
    assert "excel" in tags or "spreadsheet" in tags
    assert "email" in tags or "approval" in tags


def test_email_task_requires_approval_knowledge():
    required, reason, tags = detect_knowledge_requirement(
        "Draft an email to the client and attach the report. Do not send."
    )
    assert required is True
    assert "approval" in tags


def test_retrieval_returns_provenance():
    def _retriever(query, tags, limit):
        return [
            {"doc_id": "approval_rules", "title": "Approval", "trust": "authoritative_policy",
             "path": "policies/approval_rules.md", "content_hash": "a" * 64,
             "score": 9.0, "text": "Sending requires approval."},
        ]

    rag = ConditionalRAG(_retriever)
    result = rag.retrieve_for_goal("Draft and send an email with attachment.")
    assert result.required is True
    prov = result.provenance()
    assert prov and prov[0]["doc_id"] == "approval_rules"
    assert prov[0]["content_hash"] == "a" * 64
    assert "approval" in result.context_text().lower()


def test_context_is_labeled_reference_only():
    def _retriever(query, tags, limit):
        return [{"doc_id": "word", "title": "Word", "trust": "reference",
                 "path": "applications/word.md", "content_hash": "b" * 64,
                 "score": 3.0, "text": "Use the launch tool."}]

    rag = ConditionalRAG(_retriever)
    result = rag.retrieve_for_goal("Create a Word document report.")
    assert "reference only" in result.context_text().lower()
