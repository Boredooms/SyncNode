"""
Structured-output schema compaction.

``pydantic.model_json_schema()`` is verbose: ``title`` on every field, long
``description`` strings, ``$defs`` with ``$ref`` indirection. Embedding that
verbatim in the prompt inflates prompt tokens (~1.2-1.4k for intent/plan
schemas) with no benefit to validity.

``compact_schema`` produces a small, accurate description of the required shape:
inlines ``$ref``/``$defs`` (bounded depth), keeps field names, types,
``required``, ``enum``/``const`` (the real constraints), and drops title/long
description noise. Validation is still done against the FULL pydantic schema, so
correctness is unchanged — only the prompt is smaller.
"""

from __future__ import annotations

import json
from typing import Any

_MAX_DEPTH = 6
_MAX_DESC = 80


def _resolve_ref(ref: str, defs: dict[str, Any]) -> dict[str, Any]:
    name = ref.split("/")[-1]
    return defs.get(name, {})


def _compact_node(node: dict[str, Any], defs: dict[str, Any], depth: int) -> Any:
    if depth > _MAX_DEPTH or not isinstance(node, dict):
        return "..."

    if "$ref" in node:
        node = _resolve_ref(node["$ref"], defs)

    for key in ("anyOf", "oneOf"):
        if key in node:
            options = [_compact_node(o, defs, depth + 1) for o in node[key]]
            options = [o for o in options if o != "null"]
            return options[0] if len(options) == 1 else {"one_of": options}

    if "enum" in node:
        return {"enum": node["enum"]}
    if "const" in node:
        return {"const": node["const"]}

    t = node.get("type")

    if t == "object" or "properties" in node:
        props = node.get("properties", {})
        required = set(node.get("required", []))
        out: dict[str, Any] = {}
        for name, sub in props.items():
            compact = _compact_node(sub, defs, depth + 1)
            label = name if name in required else f"{name}?"
            out[label] = compact
        return out or "object"

    if t == "array":
        items = node.get("items", {})
        return [_compact_node(items, defs, depth + 1)]

    if isinstance(t, list):
        return "|".join(str(x) for x in t)

    return t or "any"


def compact_schema(full_schema: dict[str, Any]) -> dict[str, Any]:
    """Return a compact, inlined representation of a JSON schema."""
    defs = full_schema.get("$defs", {}) or full_schema.get("definitions", {})
    return _compact_node(full_schema, defs, 0)


def compact_schema_text(full_schema: dict[str, Any]) -> str:
    """Compact schema serialized as compact JSON for prompt embedding.

    A trailing legend explains the notation so the model reads it correctly:
      - ``name?`` means the field is optional.
      - ``{"enum": [...]}`` means the value must be one of the listed options.
    """
    compact = compact_schema(full_schema)
    body = json.dumps(compact, separators=(",", ":"), ensure_ascii=True)
    return (
        body
        + '\n(Notation: "field?" = optional; {"enum":[...]} = value must be one '
        'of the listed options; [x] = array of x.)'
    )
