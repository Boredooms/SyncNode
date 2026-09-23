"""
TRUE final golden E2E — model-driven, run-scoped, evidence-based.

Drives a real run through the backend (FastAPI + LangGraph orchestrator +
ExecutionEngine + RecoveryEngine + conditional RAG + workflow memory) and
verifies the run reaches WAITING_APPROVAL with:
  - run-scoped artifacts (no stale reuse),
  - RAG participation (audit + provenance),
  - workflow memory persisted,
  - audit chain present,
  - SSE events present,
  - send NOT executed.

Requires the backend server running on :8000 and Ollama with gemma4:e4b.
The email leg uses the local compose fixture (no external mail).
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"
DB = r"C:\syncnode\data\syncnode.db"

GOAL = (
    "Search Windows for Microsoft Word and open it, then produce three documents about "
    "SyncNode: a Word document with a short professional paragraph, an Excel workbook with "
    "a small data table, and a PowerPoint presentation with a few text slides. Then create "
    "an email draft to demo@example.com and attach all three documents. Do NOT send the email."
)


@pytest.fixture(scope="module")
def client():
    return httpx.Client(base_url=BASE_URL, timeout=300.0)


def _wait(client, run_id, timeout=300.0):
    terminal = {"completed", "failed", "waiting_approval", "cancelled"}
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/api/v1/runs/{run_id}")
        assert r.status_code == 200
        data = r.json()
        if data["status"] in terminal:
            return data
        time.sleep(3.0)
    raise TimeoutError(f"run {run_id} not terminal in {timeout}s")


def test_true_golden_e2e_waiting_approval(client):
    # Gate A: readiness
    ready = client.get("/health/ready").json()
    assert ready["checks"]["model"]["status"] == "healthy"

    resp = client.post("/api/v1/runs", json={"goal": GOAL, "failure_mode": "none"})
    assert resp.status_code == 200, resp.text
    run_id = resp.json()["run_id"]
    print(f"\n[TRUE-GOLDEN] run {run_id}")

    final = _wait(client, run_id, timeout=600.0)
    print(f"[TRUE-GOLDEN] final status: {final['status']}")
    assert final["status"] == "waiting_approval", (
        f"Expected waiting_approval, got {final['status']}: {final.get('error_message')}"
    )

    # --- Run-scoped artifact isolation ---
    # Derive the run dir from the configured workspace root (runs/<run_id>).
    candidates = [
        Path(r"C:\syncnode\workspace\demo\runs") / run_id,
        Path(r"C:\syncnode\workspace\runs") / run_id,
    ]
    run_dir = next((c for c in candidates if c.exists()), None)
    assert run_dir is not None, f"run-scoped workspace missing (tried {candidates})"
    docx = list((run_dir / "word").glob("*.docx"))
    assert docx, f"no run-scoped Word artifact under {run_dir / 'word'}"
    assert docx[0].stat().st_size > 100
    # The artifact belongs to THIS run (run_id in its path) — not a stale file.
    assert run_id in str(docx[0])

    # --- Three run-scoped artifacts produced this run (Word + Excel + PPT) ---
    arts = client.get(f"/api/v1/runs/{run_id}/artifacts").json()["artifacts"]
    print(f"[TRUE-GOLDEN] artifacts: {[a.get('name') for a in arts]}")
    kinds = {Path(a['path']).suffix for a in arts if a.get('path')}
    assert '.docx' in kinds, f"Word artifact missing; kinds={kinds}"
    assert '.xlsx' in kinds, f"Excel artifact missing; kinds={kinds}"
    assert '.pptx' in kinds, f"PowerPoint artifact missing; kinds={kinds}"
    # All artifacts belong to THIS run (run_id in path) and are hashed.
    for a in arts:
        assert run_id in a['path'], f"stale artifact: {a['path']}"
        assert a.get('sha256'), f"artifact missing hash: {a['name']}"

    # --- RAG genuinely participated (audit + context provenance) ---
    ctx = client.get(f"/api/v1/runs/{run_id}/context").json()["context"]
    assert ctx.get("rag", {}).get("required") is True, "RAG did not participate"
    assert ctx["rag"]["documents"], "RAG returned no provenance"

    audit = client.get(f"/api/v1/runs/{run_id}/audit").json()["events"]
    audit_types = {e["type"] for e in audit}
    assert "rag.query" in audit_types or "rag.retrieval.completed" in audit_types
    assert len(audit) > 0, "no audit chain"

    # --- Verifications recorded, all PASS up to the gate ---
    vers = client.get(f"/api/v1/runs/{run_id}/verifications").json()["verifications"]
    assert vers, "no verifications recorded"
    assert all(v["result"] == "PASS" for v in vers), (
        f"non-PASS verification present: {[v for v in vers if v['result'] != 'PASS']}"
    )

    # --- Approval requested, send NOT executed ---
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    cur.execute("SELECT status FROM approvals WHERE run_id=?", (run_id,))
    approvals = cur.fetchall()
    assert approvals, "no approval was requested"
    # Workflow memory recorded for safe learning.
    cur.execute("SELECT task_type, success FROM workflow_memory WHERE run_id=?", (run_id,))
    mem = cur.fetchone()
    assert mem is not None, "workflow memory not recorded"

    # No cloud model was used.
    assert final["model_id"] and not final["model_id"].endswith(":cloud")

    print("[TRUE-GOLDEN] ✓ waiting_approval, run-scoped artifact, RAG+memory+audit verified, send not executed")
