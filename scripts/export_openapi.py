"""Export the FastAPI OpenAPI schema to shared/openapi/openapi.json.

This is the machine-readable REST contract the future Electron client consumes.
Run whenever the API surface changes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "backend" / "src"))
sys.path.insert(0, str(_ROOT / "ai_ml" / "src"))

from syncnode_backend.main import create_app  # noqa: E402


def main() -> int:
    app = create_app()
    schema = app.openapi()
    out_dir = _ROOT / "shared" / "openapi"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "openapi.json"
    out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    paths = sorted(schema.get("paths", {}).keys())
    print(f"Wrote {out}")
    print(f"Paths ({len(paths)}):")
    for p in paths:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
