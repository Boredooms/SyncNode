---
id: powerpoint
type: application
version: 1
trust: reference
status: active
tags:
  - microsoft
  - office
  - powerpoint
  - pptx
  - presentation
---

# Microsoft PowerPoint

Artifact creation uses the office tools (`powerpoint.create`,
`powerpoint.add_slide`, `powerpoint.inspect`) which write real `.pptx` files.

Required verification:
- presentation file exists
- `pptx_structure_valid` (openable, at least one slide with text)
- expected slide count and titles
