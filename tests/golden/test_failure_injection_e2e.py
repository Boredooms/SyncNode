"""
Failure-injection E2E (Phase N/§27): the verifier must catch false success and
the run must fail — proving verification is real, not traversal-based.

Requires the backend server on :8000.
"""

from __future__ import annotations

import time

import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture(scope="module")
def client():
    return httpx.Client(base_url=BASE_URL, timeout=200.0)


def _wait(client, run_id, timeout=180.0):
    terminal = {"completed", "failed", "waiting_approval", "cancelled"}
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = client.get(f"/api/v1/runs/{run_id}").json()
        if data["status"] in terminal:
            return data
        time.sleep(3.0)
    raise TimeoutError("run not terminal")


def test_false_model_success_claim_is_caught(client):
    """A tool that claims success without executing must be marked failed."""
    resp = client.post("/api/v1/runs", json={
        "goal": "Write a short note and save it as a document.",
        "failure_mode": "false_model_success_claim",
    })
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    final = _wait(client, run_id)
    assert final["status"] == "failed", (
        f"Injected false success must fail; got {final['status']}"
    )
    print(f"\n[FAILURE-INJECT] false success correctly caught -> failed ({run_id})")
