"""
Workflow memory + safe learning tests (Phase G).

Uses an isolated SQLite DB via monkeypatched settings.database_url so it never
touches the real backend.db.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from syncnode_backend.learning.reward import step_reward, trajectory_reward  # noqa: E402


# ---- Reward (pure, deterministic) ----

def test_reward_verified_success_no_retry():
    r = step_reward(verification="PASS", retries=0, recovered=False)
    assert r == 1.2  # success + no-retry bonus


def test_reward_verification_failure():
    r = step_reward(verification="FAIL")
    assert r == -1.0


def test_reward_policy_violation_dominates():
    r = step_reward(verification="PASS", policy_violation=True)
    assert r == -2.0


def test_reward_unsafe_side_effect_worst():
    r = step_reward(verification="PASS", unsafe_side_effect=True)
    assert r == -3.0


def test_reward_retry_and_recovery_penalized():
    r = step_reward(verification="PASS", retries=2, recovered=True)
    # 1.0 + (no bonus, retries>0) + 2*-0.2 + -0.5
    assert r == round(1.0 - 0.4 - 0.5, 3)


def test_trajectory_sum():
    assert trajectory_reward([1.2, -1.0, 0.2]) == 0.4


# ---- Memory + candidate lifecycle (DB-backed, isolated) ----

@pytest.fixture()
async def isolated_db(tmp_path, monkeypatch):
    import syncnode_backend.persistence.database as db
    from syncnode_backend.config.settings import settings

    url = f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}"
    monkeypatch.setattr(settings, "database_url", url, raising=False)
    # reset cached engine/session factory
    db._engine = None
    db._session_factory = None
    await db.init_database()
    yield
    await db.close_database()
    db._engine = None
    db._session_factory = None


@pytest.mark.asyncio
async def test_record_run_and_best_strategies(isolated_db):
    from syncnode_backend.learning.memory import TrajectoryStep, workflow_memory

    steps = [
        TrajectoryStep(step_key="s1", action="excel.create", verification="PASS"),
        TrajectoryStep(step_key="s2", action="excel.inspect", verification="PASS"),
    ]
    res = await workflow_memory.record_run(
        run_id="r1", task_type="spreadsheet_workflow", goal_summary="make a sheet",
        steps=steps, success=True,
    )
    assert res["total_reward"] > 0
    best = await workflow_memory.best_strategies("spreadsheet_workflow")
    assert best and best[0]["tool_sequence"] == ["excel.create", "excel.inspect"]


@pytest.mark.asyncio
async def test_failure_creates_candidate_not_auto_promoted(isolated_db):
    from syncnode_backend.learning.memory import TrajectoryStep, workflow_memory

    steps = [TrajectoryStep(step_key="s1", action="computer.launch_app", verification="FAIL")]
    await workflow_memory.record_run(
        run_id="r2", task_type="document_workflow", goal_summary="open word",
        steps=steps, success=False, failure_class="APP_NOT_RUNNING",
    )
    candidates = await workflow_memory.list_candidates()
    assert candidates and candidates[0]["lifecycle"] == "CANDIDATE"
    # It must NOT be ACTIVE without human review.
    assert all(c["lifecycle"] != "ACTIVE" for c in candidates)


@pytest.mark.asyncio
async def test_promotion_requires_explicit_human_steps(isolated_db):
    from syncnode_backend.errors.exceptions import SyncNodeError
    from syncnode_backend.learning.memory import TrajectoryStep, workflow_memory

    await workflow_memory.record_run(
        run_id="r3", task_type="document_workflow", goal_summary="x",
        steps=[TrajectoryStep(step_key="s1", action="a", verification="FAIL")],
        success=False, failure_class="TOOL_NOT_FOUND",
    )
    cand = (await workflow_memory.list_candidates())[0]
    cid = cand["id"]

    # Cannot activate directly from CANDIDATE.
    with pytest.raises(SyncNodeError):
        await workflow_memory.review_candidate(cid, decision="activate", reviewer="human")

    approved = await workflow_memory.review_candidate(cid, decision="approve", reviewer="human")
    assert approved["lifecycle"] == "APPROVED"
    active = await workflow_memory.review_candidate(cid, decision="activate", reviewer="human")
    assert active["lifecycle"] == "ACTIVE"
