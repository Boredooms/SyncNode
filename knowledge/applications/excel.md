---
id: excel
type: application
version: 1
trust: reference
status: active
tags:
  - microsoft
  - office
  - excel
  - xlsx
  - spreadsheet
---

# Microsoft Excel

Artifact creation uses the office tools (`excel.create`, `excel.write_cell`,
`excel.read_range`, `excel.inspect`) which write real `.xlsx` files
deterministically. Launching/observing the running Excel UI is the computer
runtime's job.

Required verification:
- workbook file exists
- `xlsx_structure_valid` (openable, non-empty cells)
- expected cell/range values match

Cells use A1 notation (e.g. `B2`); ranges use `A1:C3`.
