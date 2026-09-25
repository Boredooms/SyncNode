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


async def _resolve_xlsx_path(path: str) -> Path:
    """Resolve an xlsx path — if it's a bare filename, search the workspace."""
    from syncnode_backend.documents.tools import _safe_path
    from syncnode_backend.config.settings import settings
    p = Path(path)
    # Already absolute and exists — use it directly
    if p.is_absolute() and p.exists():
        return _safe_path(path)
    # Bare filename (e.g. "Battery_Data.xlsx") — scan workspace for it
    if not p.is_absolute():
        import glob as _glob
        workspace = str(settings.syncnode_workspace_root)
        pattern = f"{workspace}/**/{p.name}"
        matches = sorted(_glob.glob(pattern, recursive=True),
                         key=lambda x: Path(x).stat().st_mtime, reverse=True)
        if matches:
            logger.info("[EXCEL] resolved bare filename '%s' -> '%s'", path, matches[0])
            return Path(matches[0])
    return _safe_path(path)


def _close_excel_if_open(xlsx_path: Path) -> bool:
    """Try to close any Excel process that has this file open.
    Uses PowerShell to gracefully save+close. Returns True if Excel was closed."""
    try:
        import subprocess
        name = xlsx_path.name
        # Ask Excel COM to save and close this workbook via PowerShell
        ps = (
            f'$xl = [Runtime.InteropServices.Marshal]::GetActiveObject("Excel.Application") 2>$null; '
            f'if ($xl) {{ foreach ($wb in $xl.Workbooks) {{ if ($wb.Name -like "*{name}*") '
            f'{{ $wb.Save(); $wb.Close($false) }} }} }}'
        )
        subprocess.run(["powershell", "-NonInteractive", "-Command", ps],
                       timeout=5, capture_output=True)
        import time; time.sleep(0.5)
        return True
    except Exception:
        return False


async def _write_xlsx_safe(p: Path, mutate_fn, max_retries: int = 3) -> dict:
    """Call mutate_fn(wb, ws) on an openpyxl workbook, retrying on file-locked errors.
    On first PermissionError tries to close Excel, then retries.
    Returns {"ok": True, "sha256": ...} or {"ok": False, "error": ..., "hint": ...}
    """
    from openpyxl import load_workbook
    import asyncio as _aio

    last_err = None
    for attempt in range(max_retries):
        try:
            wb = load_workbook(str(p))
            mutate_fn(wb)
            wb.save(str(p))
            return {"ok": True, "sha256": _sha256(p)}
        except PermissionError as exc:
            last_err = exc
            logger.warning("[EXCEL] file locked (attempt %d/%d): %s", attempt + 1, max_retries, p.name)
            if attempt == 0:
                # First failure: try to close Excel gracefully
                _close_excel_if_open(p)
            await _aio.sleep(1.0 * (attempt + 1))
        except Exception as exc:
            return {"ok": False, "error": str(exc), "hint": ""}

    return {
        "ok": False,
        "error": f"File is locked by Excel after {max_retries} attempts: {p.name}",
        "hint": (
            f"The file '{p.name}' is currently open in Microsoft Excel. "
            "Please close the file in Excel (Ctrl+W or File > Close), "
            "then try again. Alternatively, use computer.key_press with "
            "keys='{Ctrl}w' to close it."
        ),
    }


async def tool_excel_write_cell(path: str, cell: str, value: Any,
                                sheet_name: Optional[str] = None) -> dict[str, Any]:
    """Write a single cell (e.g. cell="B2") in an existing workbook.
    Accepts a bare filename. If file is locked by Excel, tries to close it automatically.
    """
    p = await _resolve_xlsx_path(path)
    if not p.exists():
        return {"written": False, "error": f"Workbook not found: {p}"}

    def _mutate(wb):
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.worksheets[0]
        ws[cell] = value

    result = await _write_xlsx_safe(p, _mutate)
    if result["ok"]:
        return {"written": True, "path": str(p), "cell": cell, "sha256": result["sha256"]}
    return {"written": False, "path": str(p), **{k: v for k, v in result.items() if k != "ok"}}


async def tool_excel_write_range(path: str, start_cell: str, rows: list,
                                 sheet_name: Optional[str] = None) -> dict[str, Any]:
    """Write multiple rows starting at start_cell. Accepts bare filename.
    If file is locked by Excel, tries to close it automatically and retries.
    """
    from openpyxl.utils.cell import coordinate_from_string, column_index_from_string

    p = await _resolve_xlsx_path(path)
    if not p.exists():
        return {"written": False, "error": f"Workbook not found: {p}"}

    col_letter, start_row = coordinate_from_string(start_cell)
    start_col = column_index_from_string(col_letter)

    def _mutate(wb):
        # Use provided sheet_name if it exists, else fall back to first sheet
        # (handles "Sheet1" vs "Specifications" mismatch from model hallucination)
        if sheet_name and sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
        else:
            ws = wb.worksheets[0]  # always use first sheet, not just 'active'
            if sheet_name:
                logger.info("[EXCEL] sheet '%s' not found, using first sheet '%s'", sheet_name, ws.title)
        for r_offset, row in enumerate(rows or []):
            if not isinstance(row, (list, tuple)):
                row = [row]
            for c_offset, value in enumerate(row):
                ws.cell(row=start_row + r_offset, column=start_col + c_offset, value=value)

    result = await _write_xlsx_safe(p, _mutate)
    if result["ok"]:
        logger.info("[EXCEL] write_range path=%s start=%s rows=%d", p, start_cell, len(rows or []))
        return {
            "written": True, "path": str(p), "start_cell": start_cell,
            "rows_written": len(rows or []),
            "cells_written": sum(len(r) if isinstance(r, (list, tuple)) else 1 for r in (rows or [])),
            "sha256": result["sha256"],
        }
    return {"written": False, "path": str(p), **{k: v for k, v in result.items() if k != "ok"}}


async def tool_excel_read_cell(path: str, cell: str,
                               sheet_name: Optional[str] = None) -> dict[str, Any]:
    """Read a single cell value. Accepts bare filename."""
    from openpyxl import load_workbook
    p = await _resolve_xlsx_path(path)
    if not p.exists():
        return {"exists": False, "value": None}
    wb = load_workbook(str(p), data_only=True)
    ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
    return {"exists": True, "path": str(p), "cell": cell, "value": ws[cell].value}


async def tool_excel_read_range(path: str, cell_range: str,
                                sheet_name: Optional[str] = None) -> dict[str, Any]:
    """Read a rectangular range (e.g. "A1:C3") as a list of rows. Accepts bare filename."""
    from openpyxl import load_workbook
    p = await _resolve_xlsx_path(path)
    if not p.exists():
        return {"exists": False, "values": []}
    wb = load_workbook(str(p), data_only=True)
    ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
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
            key="excel.write_cell", name="Write Cell", version=2,
            description="Write a value to a single cell (e.g. B2). Accepts bare filename — auto-resolves path in workspace.",
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
            key="excel.write_range", name="Write Range", version=1,
            description=(
                "Write multiple rows of data into an existing workbook starting at a cell address. "
                "Use start_cell='A10' to append after existing data. "
                "rows is a 2D list — each inner list is one row. "
                "Accepts bare filename — auto-resolves path in workspace. "
                "Perfect for adding new rows to an existing spreadsheet."
            ),
            input_schema={"path": "str", "start_cell": "str", "rows": "list", "sheet_name": "str?"},
            output_schema={"written": "bool", "rows_written": "int", "cells_written": "int"},
            capabilities=["spreadsheet_modification"], risk_class="medium",
            side_effect_type="IDEMPOTENT_LOCAL", idempotency="non_idempotent",
            verification_strategy="always", handler=tool_excel_write_range,
            supported_applications=["Microsoft Excel"], resource_locks=["excel"],
            drop_decorative_args=True,
            arg_aliases={
                **common_xlsx_alias,
                "sheet": "sheet_name",
                "start": "start_cell",
                "cell": "start_cell",
                "from_cell": "start_cell",
                "starting_cell": "start_cell",
                "data": "rows",
                "table": "rows",
                "values": "rows",
                "records": "rows",
                "row_data": "rows",
                "new_rows": "rows",
            },
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
