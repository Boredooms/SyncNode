"""
Golden office-artifact workflow (Phase J, deterministic).

Exercises the real cross-application artifact path end-to-end without the model:
Excel workbook -> verify -> data flows to a Word report -> verify -> PowerPoint
summary -> verify. This proves the tool + verification + data-flow layers work
across applications; the model-driven planning path is covered by the golden
demo E2E (tests/e2e/test_golden_demo.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "src"))


@pytest.fixture()
def ws(tmp_path, monkeypatch):
    import syncnode_backend.documents.tools as doc_tools
    monkeypatch.setattr(doc_tools, "_get_workspace_root", lambda: tmp_path)
    return tmp_path


@pytest.mark.asyncio
async def test_excel_to_word_to_pptx_with_verification(ws):
    from syncnode_backend.office.tools import (
        tool_excel_create, tool_excel_read_range,
        tool_powerpoint_create, tool_powerpoint_add_slide,
    )
    from syncnode_backend.documents.tools import tool_document_create_docx
    from syncnode_backend.verification.engine import VerificationEngine

    engine = VerificationEngine()

    # 1. Excel artifact
    rows = [["Product", "Revenue"], ["Widgets", 1200], ["Gadgets", 900]]
    xlsx = await tool_excel_create("q1.xlsx", rows=rows, sheet_name="Q1")
    assert xlsx["created"]
    rep = await engine.verify_step("make_xlsx", [
        {"assertion_type": "file_exists", "target": xlsx["path"]},
        {"assertion_type": "xlsx_structure_valid", "target": xlsx["path"]},
    ])
    assert rep.result == "PASS"

    # 2. Data flows from Excel into a Word report
    read = await tool_excel_read_range("q1.xlsx", "A1:B3", sheet_name="Q1")
    total = sum(r[1] for r in read["values"][1:])
    report_text = f"Q1 revenue totaled {total}. Widgets led at {read['values'][1][1]}."
    docx = await tool_document_create_docx("q1_report.docx", content=report_text, title="Q1 Report")
    rep = await engine.verify_step("make_docx", [
        {"assertion_type": "file_exists", "target": docx["path"]},
        {"assertion_type": "artifact_structure_valid", "target": docx["path"]},
    ])
    assert rep.result == "PASS"
    assert total == 2100

    # 3. PowerPoint summary
    await tool_powerpoint_create("q1_deck.pptx", title="Q1 Summary")
    pptx = await tool_powerpoint_add_slide("q1_deck.pptx", title="Revenue", body=report_text)
    rep = await engine.verify_step("make_pptx", [
        {"assertion_type": "file_exists", "target": pptx["path"]},
        {"assertion_type": "pptx_structure_valid", "target": pptx["path"]},
    ])
    assert rep.result == "PASS"


@pytest.mark.asyncio
async def test_assertion_alias_synonyms_pass(ws):
    """Model-style synonym assertion names still verify real artifacts."""
    from syncnode_backend.office.tools import tool_excel_create
    from syncnode_backend.verification.engine import VerificationEngine

    engine = VerificationEngine()
    xlsx = await tool_excel_create("data.xlsx", rows=[["a", 1]])
    rep = await engine.verify_step("x", [
        {"assertion_type": "file_existence", "target": xlsx["path"]},       # -> file_exists
        {"assertion_type": "spreadsheet_valid", "target": xlsx["path"]},    # -> xlsx_structure_valid
    ])
    assert rep.result == "PASS"
