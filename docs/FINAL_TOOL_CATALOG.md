# Final Tool Catalog

29 registered tools. Every tool declares schema, capabilities, risk, side-effect
class, aliases, resource locks, and (for artifact tools) a verification
contract. The registry is authoritative: unknown tools/args fail closed; only
declared aliases are normalized; decorative-arg dropping is opt-in per tool.
Live JSON: `GET /api/v1/tools` and `shared/openapi/openapi.json`.

| Tool | Risk | Side effect | Supported app |
|------|------|-------------|---------------|
| browser.attach_file | medium | REVERSIBLE_LOCAL | - |
| browser.click | medium | REVERSIBLE_LOCAL | - |
| browser.find_element | low | READ_ONLY | - |
| browser.get_dom_text | low | READ_ONLY | - |
| browser.get_url | low | READ_ONLY | - |
| browser.navigate | medium | REVERSIBLE_LOCAL | - |
| browser.screenshot | low | READ_ONLY | - |
| browser.type | medium | REVERSIBLE_LOCAL | - |
| computer.find_window | low | READ_ONLY | - |
| computer.get_active_window | low | READ_ONLY | - |
| computer.launch_app | medium | REVERSIBLE_LOCAL | - |
| computer.screenshot | low | READ_ONLY | - |
| computer.uia_find | low | READ_ONLY | - |
| computer.windows_search | medium | REVERSIBLE_LOCAL | - |
| document.create_docx | medium | IDEMPOTENT_LOCAL | - |
| document.inspect_docx | low | READ_ONLY | - |
| document.read_docx | low | READ_ONLY | - |
| excel.create | medium | IDEMPOTENT_LOCAL | Microsoft Excel |
| excel.inspect | low | READ_ONLY | Microsoft Excel |
| excel.read_cell | low | READ_ONLY | Microsoft Excel |
| excel.read_range | low | READ_ONLY | Microsoft Excel |
| excel.write_cell | medium | IDEMPOTENT_LOCAL | Microsoft Excel |
| filesystem.find | low | READ_ONLY | - |
| filesystem.hash | low | READ_ONLY | - |
| filesystem.write | medium | IDEMPOTENT_LOCAL | - |
| powerpoint.add_slide | medium | IDEMPOTENT_LOCAL | Microsoft PowerPoint |
| powerpoint.create | medium | IDEMPOTENT_LOCAL | Microsoft PowerPoint |
| powerpoint.inspect | low | READ_ONLY | Microsoft PowerPoint |
| writer.generate_paragraph | low | READ_ONLY | - |

## Agents (8) and their scoped tools

- **supervisor** — workflow control (workflow.pause/approve/reject/replan)
- **writer** — writer.generate_paragraph
- **document** — document.create_docx/inspect_docx/read_docx, filesystem.*
- **office** — excel.*, powerpoint.*
- **computer** — computer.windows_search/launch_app/find_window/uia_find/screenshot/get_active_window
- **browser** — browser.navigate/find_element/click/type/attach_file/screenshot/get_url/get_dom_text
- **verifier** — verify.* + document.inspect_docx + computer.screenshot
- **recovery** — computer.screenshot, filesystem.find, workflow.replan/pause

A model call for a step receives ONLY that agent's scoped tool schemas
(`tool_registry.schemas_for_agent`).
