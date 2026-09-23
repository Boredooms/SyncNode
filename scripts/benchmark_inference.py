"""
SyncNode — local inference benchmark.

Measures the ACTUAL configured local model through the SyncNode ModelGateway /
OllamaAdapter path (i.e. with the inference profiles and GPU-offload options this
project sends in production), not just raw Ollama.

Workloads:
  A. Tiny response
  B. Normal short reasoning (SyncNode-style planning ask)
  C. Small structured JSON (intent-like)
  D. Large structured plan (ExecutionPlan via the real Planner schema)
  E. Vision (small local image fixture)
  F. Multi-turn accumulated context

For each it records Ollama's own timing counters plus GPU/VRAM/RAM samples from
nvidia-smi and the OS, and writes:
  - data/benchmarks/inference_<timestamp>.json
  - a human-readable summary to stdout

Usage:
    python scripts/benchmark_inference.py
    python scripts/benchmark_inference.py --profile-compare   # A/B auto vs num_gpu=99

Fails loudly if Ollama or the model is unavailable (no fabrication).
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import struct
import subprocess
import sys
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Wire up source paths (mirrors the test harness).
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "ai_ml" / "src"))
sys.path.insert(0, str(_ROOT / "backend" / "src"))

from pydantic import BaseModel  # noqa: E402

from syncnode_ai.gateway.gateway import ModelGateway  # noqa: E402
from syncnode_ai.gateway.ollama_adapter import OllamaAdapter  # noqa: E402
from syncnode_ai.gateway.schemas import ImageInput, Message, ModelRequest  # noqa: E402
from syncnode_ai.routing import TaskClass, profile_registry  # noqa: E402
from syncnode_ai.planner._output import _PlannerOutput  # noqa: E402
from syncnode_ai.intent.schemas import StructuredIntent  # noqa: E402

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_ID = "gemma4:e4b"


# ------------------------------------------------------------------ #
# Hardware sampling                                                     #
# ------------------------------------------------------------------ #

def gpu_sample() -> dict[str, Any]:
    """Sample GPU state via nvidia-smi. Returns {} if unavailable."""
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode != 0:
            return {"error": out.stderr.strip()}
        name, total, used, free, util, mem_util, temp = [
            x.strip() for x in out.stdout.strip().split(",")
        ]
        return {
            "name": name,
            "vram_total_mib": float(total),
            "vram_used_mib": float(used),
            "vram_free_mib": float(free),
            "gpu_util_pct": float(util),
            "mem_util_pct": float(mem_util),
            "temp_c": float(temp),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostic only
        return {"error": str(exc)}


def ram_sample() -> dict[str, Any]:
    try:
        import psutil
        vm = psutil.virtual_memory()
        return {
            "ram_total_mib": round(vm.total / 1024 / 1024),
            "ram_available_mib": round(vm.available / 1024 / 1024),
            "ram_used_pct": vm.percent,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def ollama_ps() -> dict[str, Any]:
    """Read /api/ps to learn resident size / VRAM split / processor."""
    import urllib.request
    try:
        with urllib.request.urlopen(OLLAMA_URL + "/api/ps", timeout=15) as r:
            data = json.loads(r.read().decode())
        for m in data.get("models", []):
            size = m.get("size", 0)
            vram = m.get("size_vram", 0)
            return {
                "resident_size_gb": round(size / 1e9, 2),
                "vram_gb": round(vram / 1e9, 2),
                "gpu_pct": round(100 * vram / size) if size else 0,
                "context": m.get("context_length"),
            }
        return {"resident": False}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


# ------------------------------------------------------------------ #
# Fixtures                                                              #
# ------------------------------------------------------------------ #

def make_png(w: int = 96, h: int = 96) -> bytes:
    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    row = b"\x00" + (b"\x22\x55\xbb" * w)  # steady blue-ish
    idat = chunk(b"IDAT", zlib.compress(row * h))
    iend = chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend


GOLDEN_PLANNING_ASK = (
    "Plan the steps to write a short paragraph about a tree beside a quiet "
    "industrial road, save it as a Word document, open it, verify it, then "
    "create a browser email draft with the document attached. Do not send."
)


# ------------------------------------------------------------------ #
# Measurement primitives                                                #
# ------------------------------------------------------------------ #

async def _timed_generate(
    gateway: ModelGateway, request: ModelRequest
) -> tuple[Any, float]:
    t0 = time.monotonic()
    resp = await gateway.generate(request)
    wall = time.monotonic() - t0
    return resp, wall


def _profile_request(task: TaskClass, messages: list[Message], **overrides) -> ModelRequest:
    profile = profile_registry.get(task)
    req = ModelRequest(model_id=MODEL_ID, messages=messages, caller="benchmark")
    upd = profile.request_overrides()
    upd.update(overrides)
    return req.model_copy(update=upd)


async def run_workload(
    gateway: ModelGateway, name: str, task: TaskClass, request: ModelRequest,
    structured_schema: Optional[type[BaseModel]] = None,
) -> dict[str, Any]:
    before_gpu = gpu_sample()
    before_ram = ram_sample()
    valid = None
    err = None
    t0 = time.monotonic()
    try:
        if structured_schema is not None:
            _, resp = await gateway.generate_structured(request, structured_schema)
            valid = True
        else:
            resp = await gateway.generate(request)
    except Exception as exc:  # noqa: BLE001
        err = f"{type(exc).__name__}: {exc}"
        valid = False if structured_schema is not None else None
        wall = time.monotonic() - t0
        return {
            "workload": name, "task_class": task.value, "error": err,
            "wall_seconds": round(wall, 2), "gpu_before": before_gpu,
        }
    wall = time.monotonic() - t0
    during_ps = ollama_ps()
    after_gpu = gpu_sample()
    after_ram = ram_sample()
    gen_tokps = (
        resp.output_tokens / (resp.latency_ms / 1000)
        if resp.latency_ms else 0
    )
    return {
        "workload": name,
        "task_class": task.value,
        "prompt_tokens": resp.input_tokens,
        "completion_tokens": resp.output_tokens,
        "total_tokens": resp.input_tokens + resp.output_tokens,
        "latency_ms": round(resp.latency_ms, 1),
        "wall_seconds": round(wall, 2),
        "approx_tokps_over_latency": round(gen_tokps, 2),
        "structured_valid": valid,
        "ollama_ps": during_ps,
        "gpu_before": before_gpu,
        "gpu_after": after_gpu,
        "ram_before": before_ram,
        "ram_after": after_ram,
        "reply_preview": (resp.content or "")[:120],
    }


# ------------------------------------------------------------------ #
# Main                                                                  #
# ------------------------------------------------------------------ #

async def main(profile_compare: bool) -> int:
    adapter = OllamaAdapter(base_url=OLLAMA_URL, timeout=600.0)
    gateway = ModelGateway(adapter=adapter, model_id=MODEL_ID, max_repair=2)

    # Fail loudly if unavailable — never fabricate results.
    health = await gateway.health()
    if health.status.value != "healthy":
        print(f"FATAL: model {MODEL_ID} not healthy: {health.error}", file=sys.stderr)
        await gateway.close()
        return 2

    results: list[dict[str, Any]] = []

    # A. Tiny
    results.append(await run_workload(
        gateway, "A_tiny", TaskClass.FAST_SIMPLE,
        _profile_request(TaskClass.FAST_SIMPLE, [
            Message(role="user", content="Say hello in one short sentence."),
        ]),
    ))

    # B. Normal reasoning (short)
    results.append(await run_workload(
        gateway, "B_normal_reasoning", TaskClass.NORMAL_REASONING,
        _profile_request(TaskClass.NORMAL_REASONING, [
            Message(role="user", content=GOLDEN_PLANNING_ASK),
        ]),
    ))

    # C. Small structured JSON (intent-like)
    results.append(await run_workload(
        gateway, "C_structured_intent", TaskClass.FAST_STRUCTURED,
        _profile_request(TaskClass.FAST_STRUCTURED, [
            Message(role="system", content="Extract a structured intent as JSON."),
            Message(role="user", content=GOLDEN_PLANNING_ASK),
        ]),
        structured_schema=StructuredIntent,
    ))

    # D. Large structured plan (real planner schema)
    results.append(await run_workload(
        gateway, "D_structured_plan", TaskClass.PLANNER,
        _profile_request(TaskClass.PLANNER, [
            Message(role="system", content=(
                "Return a JSON object {\"steps\": [...]} for an execution plan. "
                "Each step needs step_key, agent_key, action, description, "
                "dependencies, inputs, allowed_tools, risk, and postconditions "
                "(a non-empty list of {assertion_type, target, expected, description})."
            )),
            Message(role="user", content=GOLDEN_PLANNING_ASK),
        ]),
        structured_schema=_PlannerOutput,
    ))

    # E. Vision
    img_b64 = base64.b64encode(make_png()).decode()
    results.append(await run_workload(
        gateway, "E_vision", TaskClass.VISION,
        _profile_request(TaskClass.VISION, [
            Message(
                role="user",
                content="What color dominates this image? Answer in one word.",
                images=[ImageInput(source="base64", value=img_b64, mime_type="image/png")],
            ),
        ]),
    ))

    # F. Multi-turn accumulated context
    results.append(await run_workload(
        gateway, "F_multiturn", TaskClass.NORMAL_REASONING,
        _profile_request(TaskClass.NORMAL_REASONING, [
            Message(role="user", content="I'm building a document automation demo."),
            Message(role="assistant", content="Understood. What's the document about?"),
            Message(role="user", content="A tree beside a quiet industrial road."),
            Message(role="assistant", content="Got it. Anything else?"),
            Message(role="user", content="Summarize what I've asked for so far in two sentences."),
        ]),
    ))

    optional_compare: dict[str, Any] = {}
    if profile_compare:
        # A/B: auto offload (num_gpu=None) vs full offload (num_gpu=99), same ask.
        base_msgs = [Message(role="user", content="Write ~120 words of plain prose about rain.")]
        auto_req = _profile_request(TaskClass.FAST_SIMPLE, list(base_msgs), num_gpu=None, num_ctx=4096)
        full_req = _profile_request(TaskClass.FAST_SIMPLE, list(base_msgs), num_gpu=99, num_ctx=4096)
        # unload between for fair cold comparison
        optional_compare["auto_offload"] = await run_workload(
            gateway, "cmp_auto_offload", TaskClass.FAST_SIMPLE, auto_req)
        optional_compare["full_offload"] = await run_workload(
            gateway, "cmp_full_offload", TaskClass.FAST_SIMPLE, full_req)

    await gateway.close()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_id": MODEL_ID,
        "endpoint": OLLAMA_URL,
        "profiles": {k.value: v.model_dump() for k, v in profile_registry.all().items()},
        "workloads": results,
        "profile_compare": optional_compare,
    }

    out_dir = _ROOT / "data" / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"inference_{stamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Human summary
    print("\n=== SYNCNODE LOCAL INFERENCE BENCHMARK ===\n")
    g = results[0].get("gpu_after") or {}
    print(f"GPU:   {g.get('name', 'n/a')}  VRAM {g.get('vram_total_mib', '?')} MiB")
    print(f"Model: {MODEL_ID}   Endpoint: {OLLAMA_URL}\n")
    print(f"{'WORKLOAD':<22}{'PROFILE':<18}{'PROMPT':>7}{'OUT':>6}{'TOK/S':>8}{'TOTAL(s)':>10}{'VALID':>7}")
    print("-" * 78)
    for r in results:
        if "error" in r:
            print(f"{r['workload']:<22}{r['task_class']:<18}{'ERROR: ' + r['error'][:40]}")
            continue
        print(
            f"{r['workload']:<22}{r['task_class']:<18}"
            f"{r['prompt_tokens']:>7}{r['completion_tokens']:>6}"
            f"{r['approx_tokps_over_latency']:>8.1f}{r['wall_seconds']:>10.2f}"
            f"{str(r['structured_valid']):>7}"
        )
    if optional_compare:
        print("\n--- profile compare (same 120-word ask) ---")
        for k, r in optional_compare.items():
            if "error" in r:
                print(f"  {k}: ERROR {r['error']}")
            else:
                print(f"  {k:<14} tok/s={r['approx_tokps_over_latency']:>6.1f} "
                      f"total={r['wall_seconds']:.2f}s ps={r['ollama_ps']}")
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile-compare", action="store_true",
                    help="Also run an auto-offload vs full-GPU-offload A/B.")
    args = ap.parse_args()
    raise SystemExit(asyncio.run(main(args.profile_compare)))
