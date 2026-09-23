"""Measure prompt-token reduction from compact structured-output schemas."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "ai_ml" / "src"))
sys.path.insert(0, str(_ROOT / "backend" / "src"))

from syncnode_ai.gateway._schema import compact_schema_text  # noqa: E402
from syncnode_ai.intent.schemas import StructuredIntent  # noqa: E402
from syncnode_ai.planner._output import _PlannerOutput  # noqa: E402


def approx_tokens(s: str) -> int:
    # rough heuristic: ~4 chars/token
    return len(s) // 4


for name, cls in (("StructuredIntent", StructuredIntent), ("PlannerOutput(plan)", _PlannerOutput)):
    full = json.dumps(cls.model_json_schema(), indent=2)
    compact = compact_schema_text(cls.model_json_schema())
    print(f"\n=== {name} ===")
    print(f"  full   : {len(full):>6} chars  (~{approx_tokens(full):>4} tok)")
    print(f"  compact: {len(compact):>6} chars  (~{approx_tokens(compact):>4} tok)")
    reduction = 100 * (1 - len(compact) / len(full)) if full else 0
    print(f"  reduction: {reduction:.0f}%")
    print(f"  --- compact preview ---\n{compact[:600]}")
