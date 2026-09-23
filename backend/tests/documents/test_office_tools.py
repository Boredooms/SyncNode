"""
Office tool tests (Phase D): real Excel + PowerPoint artifact creation.

Offline, deterministic (openpyxl / python-pptx). Writes into a temp workspace.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


@pytest.fixture()
def workspace(tmp_path, monkeypatch):
    # Point the workspace sandbox at a temp dir.
    from syncnode_backend.config.settings import settings
    monkeypatch.setattr(type(settings), "syncnode_workspace_root",
                        property(lambda self: tmp_path), raising=False)
    # documents.tools._get_workspace_root reads settings.syncnode_workspace_root
    import syncnode_backend.documents.tools as doc_tools
    monkeypatch.setattr(doc_tools, "_get_workspace_root", lambda: tmp_path)
    return tmp_path


@pytest.mark.asyncio
async def test_excel_create_read_inspect(workspace):
    from syncnode_backend.office.tools import (
        tool_excel_create, tool_excel_read_range, tool_excel_inspect,
        tool_excel_write_cell, tool_excel_read_cell,
    )
    rows = [["Name", "Q1", "Q2"], ["Widgets", 100, 150], ["Gadgets", 80, 120]]
    res = await tool_excel_create("report.xlsx", rows=rows, sheet_name="Sales")
    assert res["created"] and res["cells_written"] == 9
    assert (workspace / "report.xlsx").exists()

    read = await tool_excel_read_range("report.xlsx", "A1:C3", sheet_name="Sales")
    assert read["values"][0] == ["Name", "Q1", "Q2"]
    assert read["values"][1][1] == 100

    await tool_excel_write_cell("report.xlsx", "D1", "Total", sheet_name="Sales")
    cell = await tool_excel_read_cell("report.xlsx", "D1", sheet_name="Sales")
    assert cell["value"] == "Total"

    ins = await tool_excel_inspect("report.xlsx")
    assert ins["exists"] and ins["has_content"]
    assert ins["sheets"][0]["name"] == "Sales"


@pytest.mark.asyncio
async def test_powerpoint_create_add_inspect(workspace):
    from syncnode_backend.office.tools import (
        tool_powerpoint_create, tool_powerpoint_add_slide, tool_powerpoint_inspect,
    )
    res = await tool_powerpoint_create("deck.pptx", title="SyncNode Demo", subtitle="Q1 Results")
    assert res["created"] and res["slide_count"] == 1

    add = await tool_powerpoint_add_slide("deck.pptx", title="Summary", body="Revenue up 20%")
    assert add["added"] and add["slide_count"] == 2

    ins = await tool_powerpoint_inspect("deck.pptx")
    assert ins["exists"] and ins["has_content"]
    all_text = " ".join(t for s in ins["slides"] for t in s["texts"])
    assert "SyncNode Demo" in all_text and "Summary" in all_text


@pytest.mark.asyncio
async def test_excel_read_missing_file(workspace):
    from syncnode_backend.office.tools import tool_excel_read_cell
    res = await tool_excel_read_cell("nope.xlsx", "A1")
    assert res["exists"] is False
