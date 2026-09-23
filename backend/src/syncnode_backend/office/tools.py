"""
SyncNode — Office document tools (Excel, PowerPoint).

These use deterministic, offline document libraries (openpyxl, python-pptx)
rather than COM automation. That makes artifact creation reliable, verifiable by
hash/structure, and runnable without a live Office UI. Launching/observing the
running Office application (UIA) remains the job of the computer runtime; these
tools create and inspect the artifacts on disk.

All paths are workspace-sandboxed via documents.tools._safe_path.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _safe(path: str) -> Path:
    from syncnode_backend.documents.tools import _safe_path
    return _safe_path(path)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ #
# Excel (openpyxl)                                                      #
# ------------------------------------------------------------------ #

async def tool_excel_create(
    path: str,
    rows: Optional[list] = None,
    sheet_name: str = "Sheet1",
    headers: Optional[list] = None,
) -> dict[str, Any]:
    """Create an XLSX workbook, optionally writing a 2D `rows` table.

    `headers` is an optional flat list of column names. If provided and the
    first row of `rows` doesn't already match it, it is prepended as row 1.
    This lets the model pass headers separately from data rows.
    """
    from openpyxl import Workbook

    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Merge headers + rows: prepend headers if they're not already row 0
    all_rows: list = list(rows or [])
    if headers and isinstance(headers, (list, tuple)):
        if not all_rows or list(all_rows[0]) != list(headers):
            all_rows = [list(headers)] + all_rows

    written = 0
    for r_idx, row in enumerate(all_rows, start=1):
        if not isinstance(row, (list, tuple)):
            row = [row]
        for c_idx, value in enumerate(row, start=1):
            ws.cell(row=r_idx, column=c_idx, value=value)
            written += 1
    wb.save(str(p))
    digest = _sha256(p)
    logger.info("XLSX created — path=%s cells=%d sha=%s", p, written, digest[:8])
    return {
        "path": str(p), "sha256": digest, "size_bytes": p.stat().st_size,
        "sheet": sheet_name, "cells_written": written, "created": True,
    }


async def tool_excel_write_cell(path: str, cell: str, value: Any,
                                sheet_name: Optional[str] = None) -> dict[str, Any]:
    """Write a single cell (e.g. cell="B2") in an existing workbook."""
    from openpyxl import load_workbook

    p = _safe(path)
    if not p.exists():
        return {"written": False, "error": f"Workbook not found: {p}"}
    wb = load_workbook(str(p))
    ws = wb[sheet_name] if sheet_name else wb.active
    ws[cell] = value
    wb.save(str(p))
    return {"written": True, "path": str(p), "cell": cell, "sha256": _sha256(p)}


async def tool_excel_read_cell(path: str, cell: str,
                               sheet_name: Optional[str] = None) -> dict[str, Any]:
    """Read a single cell value."""
    from openpyxl import load_workbook

    p = _safe(path)
    if not p.exists():
        return {"exists": False, "value": None}
    wb = load_workbook(str(p), data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.active
    return {"exists": True, "path": str(p), "cell": cell, "value": ws[cell].value}


async def tool_excel_read_range(path: str, cell_range: str,
                                sheet_name: Optional[str] = None) -> dict[str, Any]:
    """Read a rectangular range (e.g. "A1:C3") as a list of rows."""
    from openpyxl import load_workbook

    p = _safe(path)
    if not p.exists():
        return {"exists": False, "values": []}
    wb = load_workbook(str(p), data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.active
    values = [[c.value for c in row] for row in ws[cell_range]]
    return {"exists": True, "path": str(p), "range": cell_range, "values": values}


async def tool_excel_inspect(path: str) -> dict[str, Any]:
    """Inspect workbook structure: sheets, dimensions, non-empty cell count."""
    from openpyxl import load_workbook

    p = _safe(path)
    if not p.exists():
        return {"exists": False, "path": str(p)}
    wb = load_workbook(str(p), data_only=True)
    sheets = []
    for ws in wb.worksheets:
        non_empty = sum(1 for row in ws.iter_rows() for c in row if c.value is not None)
        sheets.append({
            "name": ws.title, "max_row": ws.max_row, "max_col": ws.max_column,
            "non_empty_cells": non_empty,
        })
    return {
        "exists": True, "path": str(p), "sha256": _sha256(p),
        "size_bytes": p.stat().st_size, "sheet_count": len(sheets), "sheets": sheets,
        "has_content": any(s["non_empty_cells"] > 0 for s in sheets),
    }


# ------------------------------------------------------------------ #
# PowerPoint (python-pptx)                                              #
# ------------------------------------------------------------------ #

async def tool_powerpoint_create(path: str, title: Optional[str] = None,
                                 subtitle: Optional[str] = None,
                                 slides: Optional[list] = None) -> dict[str, Any]:
    """Create a PPTX with an optional title slide, then append any additional slides.

    `slides` is an optional list of dicts, each with optional keys:
      - title / heading / type  → slide title text
      - body / content / text   → slide body text
    This lets the model create a multi-slide deck in a single tool call.
    """
    from pptx import Presentation

    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    prs = Presentation()

    # Title slide
    if title is not None:
        layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(layout)
        slide.shapes.title.text = title
        if subtitle is not None and len(slide.placeholders) > 1:
            slide.placeholders[1].text = subtitle

    # Additional slides from the `slides` list
    for slide_def in (slides or []):
        if not isinstance(slide_def, dict):
            continue
        stitle = (
            slide_def.get("title") or slide_def.get("heading") or
            slide_def.get("type") or slide_def.get("name") or ""
        )
        sbody = (
            slide_def.get("body") or slide_def.get("content") or
            slide_def.get("text") or slide_def.get("description") or ""
        )
        layout = prs.slide_layouts[1]  # Title and Content
        sl = prs.slides.add_slide(layout)
        if sl.shapes.title is not None:
            sl.shapes.title.text = str(stitle)
        if sbody and len(sl.placeholders) > 1:
            sl.placeholders[1].text = str(sbody)

    prs.save(str(p))
    digest = _sha256(p)
    slide_count = len(prs.slides._sldIdLst)
    logger.info("PPTX created — path=%s slides=%d sha=%s", p, slide_count, digest[:8])
    return {
        "path": str(p), "sha256": digest, "size_bytes": p.stat().st_size,
        "slide_count": slide_count, "created": True,
    }


async def tool_powerpoint_add_slide(path: str, title: str = "",
                                    body: str = "") -> dict[str, Any]:
    """Append a title+content slide to an existing presentation."""
    from pptx import Presentation

    p = _safe(path)
    if not p.exists():
        return {"added": False, "error": f"Presentation not found: {p}"}
    prs = Presentation(str(p))
    layout = prs.slide_layouts[1]  # Title and Content
    slide = prs.slides.add_slide(layout)
    if slide.shapes.title is not None:
        slide.shapes.title.text = title
    if body and len(slide.placeholders) > 1:
        slide.placeholders[1].text = body
    prs.save(str(p))
    return {"added": True, "path": str(p), "slide_count": len(prs.slides._sldIdLst),
            "sha256": _sha256(p)}


async def tool_powerpoint_inspect(path: str) -> dict[str, Any]:
    """Inspect a presentation: slide count and per-slide text."""
    from pptx import Presentation

    p = _safe(path)
    if not p.exists():
        return {"exists": False, "path": str(p)}
    prs = Presentation(str(p))
    slides = []
    for i, slide in enumerate(prs.slides):
        texts = [sh.text for sh in slide.shapes if sh.has_text_frame and sh.text.strip()]
        slides.append({"index": i, "texts": texts})
    return {
        "exists": True, "path": str(p), "sha256": _sha256(p),
        "size_bytes": p.stat().st_size, "slide_count": len(slides), "slides": slides,
        "has_content": any(s["texts"] for s in slides),
    }


# ------------------------------------------------------------------ #
# Registration                                                          #
# ------------------------------------------------------------------ #

def register_office_tools(registry) -> None:
    from syncnode_backend.tools.registry import ToolDefinition

    common_xlsx_alias = {"filename": "path", "file_name": "path", "file": "path",
                         "workbook": "path", "workspace": "", "directory": ""}
    common_pptx_alias = {"filename": "path", "file_name": "path", "file": "path",
                         "presentation": "path", "workspace": "", "directory": ""}

    tools = [
        ToolDefinition(
            key="excel.create", name="Create XLSX", version=2,
            description=(
                "Create an Excel workbook with a data table. Pass `rows` as a 2D list "
                "(each inner list is one row). Pass `headers` as a flat list of column "
                "names — they will be written as the first row automatically."
            ),
            input_schema={"path": "str", "rows": "list?", "sheet_name": "str?", "headers": "list?"},
            output_schema={"path": "str", "sha256": "str", "cells_written": "int"},
            capabilities=["spreadsheet_creation"], risk_class="medium",
            side_effect_type="IDEMPOTENT_LOCAL", idempotency="idempotent",
            verification_strategy="always", handler=tool_excel_create,
            supported_applications=["Microsoft Excel"], resource_locks=["excel"],
            verification_contract=["file_exists", "artifact_structure_valid"],
            drop_decorative_args=True,
            arg_aliases={
                **common_xlsx_alias,
                "data": "rows",
                "table": "rows",
                "sheet": "sheet_name",
                "columns": "headers",
                "column_headers": "headers",
                "header_row": "headers",
                "data_rows": "rows",
                "row_data": "rows",
                "values": "rows",
                "records": "rows",
            },
        ),
        ToolDefinition(
            key="excel.write_cell", name="Write Cell", version=1,
            description="Write a value to a single cell (e.g. B2)",
            input_schema={"path": "str", "cell": "str", "value": "any", "sheet_name": "str?"},
            output_schema={"written": "bool"},
            capabilities=["spreadsheet_modification"], risk_class="medium",
            side_effect_type="IDEMPOTENT_LOCAL", idempotency="idempotent",
            verification_strategy="always", handler=tool_excel_write_cell,
            supported_applications=["Microsoft Excel"], resource_locks=["excel"],
            drop_decorative_args=True,
            arg_aliases={**common_xlsx_alias, "sheet": "sheet_name"},
        ),
        ToolDefinition(
            key="excel.read_cell", name="Read Cell", version=1,
            description="Read a single cell value",
            input_schema={"path": "str", "cell": "str", "sheet_name": "str?"},
            output_schema={"value": "any"},
            capabilities=["spreadsheet_inspection"], risk_class="low",
            side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_excel_read_cell,
            supported_applications=["Microsoft Excel"],
            drop_decorative_args=True,
            arg_aliases={**common_xlsx_alias, "sheet": "sheet_name"},
        ),
        ToolDefinition(
            key="excel.read_range", name="Read Range", version=1,
            description="Read a rectangular range (e.g. A1:C3)",
            input_schema={"path": "str", "cell_range": "str", "sheet_name": "str?"},
            output_schema={"values": "list"},
            capabilities=["spreadsheet_inspection"], risk_class="low",
            side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_excel_read_range,
            supported_applications=["Microsoft Excel"],
            drop_decorative_args=True,
            arg_aliases={**common_xlsx_alias, "range": "cell_range", "sheet": "sheet_name"},
        ),
        ToolDefinition(
            key="excel.inspect", name="Inspect XLSX", version=1,
            description="Inspect workbook structure and content",
            input_schema={"path": "str"},
            output_schema={"exists": "bool", "sheets": "list"},
            capabilities=["spreadsheet_inspection"], risk_class="low",
            side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_excel_inspect,
            supported_applications=["Microsoft Excel"],
            drop_decorative_args=True,
            arg_aliases=common_xlsx_alias,
        ),
        ToolDefinition(
            key="powerpoint.create", name="Create PPTX", version=2,
            description=(
                "Create a PowerPoint presentation. Pass `title` and `subtitle` for the title slide. "
                "Pass a `slides` list to create additional content slides in one call — each item "
                "is a dict with 'title' (slide heading) and 'body' (slide content text)."
            ),
            input_schema={
                "path": "str",
                "title": "str?",
                "subtitle": "str?",
                "slides": "list? — [{title: str, body: str}, ...]",
            },
            output_schema={"path": "str", "slide_count": "int"},
            capabilities=["presentation_creation"], risk_class="medium",
            side_effect_type="IDEMPOTENT_LOCAL", idempotency="idempotent",
            verification_strategy="always", handler=tool_powerpoint_create,
            supported_applications=["Microsoft PowerPoint"], resource_locks=["powerpoint"],
            verification_contract=["file_exists", "artifact_structure_valid"],
            drop_decorative_args=True,
            arg_aliases={
                **common_pptx_alias,
                "heading": "title",
                "name": "title",
                "deck_title": "title",
                "slide_list": "slides",
                "slide_data": "slides",
                "contents": "slides",
                "data": "slides",
            },
        ),
        ToolDefinition(
            key="powerpoint.add_slide", name="Add Slide", version=1,
            description="Append a title+content slide",
            input_schema={"path": "str", "title": "str?", "body": "str?"},
            output_schema={"added": "bool", "slide_count": "int"},
            capabilities=["presentation_modification"], risk_class="medium",
            side_effect_type="IDEMPOTENT_LOCAL", idempotency="non_idempotent",
            verification_strategy="always", handler=tool_powerpoint_add_slide,
            supported_applications=["Microsoft PowerPoint"], resource_locks=["powerpoint"],
            drop_decorative_args=True,
            arg_aliases={**common_pptx_alias, "text": "body", "content": "body", "heading": "title", "type": "title", "slide_title": "title", "slide_index": "", "index": "", "position": ""},
        ),
        ToolDefinition(
            key="powerpoint.inspect", name="Inspect PPTX", version=1,
            description="Inspect a presentation's slides and text",
            input_schema={"path": "str"},
            output_schema={"exists": "bool", "slides": "list"},
            capabilities=["presentation_inspection"], risk_class="low",
            side_effect_type="READ_ONLY", idempotency="idempotent",
            verification_strategy="never", handler=tool_powerpoint_inspect,
            supported_applications=["Microsoft PowerPoint"],
            drop_decorative_args=True,
            arg_aliases=common_pptx_alias,
        ),
    ]
    for t in tools:
        registry.register(t)
    logger.info("Office tools registered — count=%d", len(tools))
