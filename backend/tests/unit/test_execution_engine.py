"""
Execution Engine + Resource Lock tests (Phase C).

Pure-unit: no model, no Ollama, no network.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from syncnode_backend.errors.exceptions import LockTimeoutError  # noqa: E402
from syncnode_backend.runtime.execution_engine import (  # noqa: E402
    ExecState, ExecutionEngine, ToolProposal,
)
from syncnode_backend.runtime.locks import ResourceLockManager, lease_group  # noqa: E402
from syncnode_backend.tools.registry import ToolDefinition, ToolRegistry  # noqa: E402


class _Report:
    def __init__(self, result: str, reason: str = "") -> None:
        self.result = result
        self.failure_reason = reason


def _registry(handler) -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(ToolDefinition(
        key="word.save",
        name="Save",
        version=1,
        description="save",
        input_schema={"path": "str"},
        output_schema={"saved": "bool"},
        capabilities=["document_modification"],
        risk_class="medium",
        side_effect_type="IDEMPOTENT_LOCAL",
        idempotency="idempotent",
        verification_strategy="always",
        handler=handler,
        supported_applications=["Microsoft Word"],
        resource_locks=["word"],
    ))
    return reg


def _proposal(**kw) -> ToolProposal:
    base = dict(
        tool_key="word.save", inputs={"path": "a.docx"}, agent_key="document",
        agent_allowed_tools=["word.save"], step_key="save_step",
        postconditions=[{"assertion_type": "file_exists", "target": "a.docx"}],
    )
    base.update(kw)
    return ToolProposal(**base)


# ------------------------------------------------------------------ #
# Locks                                                                 #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_lock_exclusive_then_reusable():
    m = ResourceLockManager()
    lease = await m.acquire("word", "agentA")
    assert m.status()["word"]["owner"] == "agentA"
    m.release(lease)
    lease2 = await m.acquire("word", "agentB")
    assert m.status()["word"]["owner"] == "agentB"
    m.release(lease2)


@pytest.mark.asyncio
async def test_lock_conflict_times_out():
    m = ResourceLockManager()
    lease = await m.acquire("desktop", "agentA")
    with pytest.raises(LockTimeoutError):
        await m.acquire("desktop", "agentB", wait_timeout=0.3)
    m.release(lease)


@pytest.mark.asyncio
async def test_expired_lease_reclaimed():
    m = ResourceLockManager()
    await m.acquire("word", "agentA", ttl_seconds=0.1)
    await asyncio.sleep(0.2)
    lease2 = await m.acquire("word", "agentB", wait_timeout=1.0)
    assert lease2.owner == "agentB"
    m.release(lease2)


@pytest.mark.asyncio
async def test_lease_group_atomic():
    m = ResourceLockManager()
    async with lease_group(m, ["word", "desktop"], "agentA") as leases:
        assert len(leases) == 2
    assert m.status()["word"] is None
    assert m.status()["desktop"] is None


# ------------------------------------------------------------------ #
# Execution Engine                                                      #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_happy_path_reaches_passed():
    async def handler(path):
        return {"saved": True, "path": path}

    async def verify(proposal, output, ts):
        return _Report("PASS")

    eng = ExecutionEngine(_registry(handler), ResourceLockManager(), verify=verify)
    res = await eng.run(_proposal())
    assert res.state == ExecState.PASSED
    assert res.transitions[:5] == ["PROPOSED", "VALIDATED", "AUTHORIZED", "LOCKED", "PRECONDITION_CHECK"]
    assert "EXECUTING" in res.transitions and "VERIFYING" in res.transitions
    assert res.tool_output["saved"] is True


@pytest.mark.asyncio
async def test_verification_failure_marks_failed():
    async def handler(path):
        return {"saved": True}

    async def verify(proposal, output, ts):
        return _Report("FAIL", "file missing")

    eng = ExecutionEngine(_registry(handler), ResourceLockManager(), verify=verify)
    res = await eng.run(_proposal())
    assert res.state == ExecState.FAILED
    assert res.error_class == "VERIFICATION_FAILED"


@pytest.mark.asyncio
async def test_stale_observation_marks_ambiguous():
    async def handler(path):
        return {"saved": True}

    async def verify(proposal, output, ts):
        return _Report("STALE", "too old")

    eng = ExecutionEngine(_registry(handler), ResourceLockManager(), verify=verify)
    res = await eng.run(_proposal())
    assert res.state == ExecState.AMBIGUOUS
    assert res.error_class == "STALE"


@pytest.mark.asyncio
async def test_precondition_failure():
    async def handler(path):
        return {"saved": True}

    async def precondition(defn, proposal):
        return "app not running"

    eng = ExecutionEngine(_registry(handler), ResourceLockManager(), precondition=precondition)
    res = await eng.run(_proposal())
    assert res.state == ExecState.FAILED
    assert res.error_class == "PRECONDITION_FAILED"


@pytest.mark.asyncio
async def test_tool_execution_error_classified():
    async def handler(path):
        raise RuntimeError("boom")

    eng = ExecutionEngine(_registry(handler), ResourceLockManager())
    res = await eng.run(_proposal(postconditions=[]))
    assert res.state == ExecState.FAILED
    assert res.error_class == "TOOL_EXECUTION_ERROR"


@pytest.mark.asyncio
async def test_invalid_args_rejected_before_execution():
    executed = {"v": False}

    async def handler(path):
        executed["v"] = True
        return {"saved": True}

    eng = ExecutionEngine(_registry(handler), ResourceLockManager())
    res = await eng.run(_proposal(inputs={"path": "a.docx", "bogus": 1}))
    assert res.state == ExecState.FAILED
    assert res.error_class == "INVALID_TOOL_ARGUMENTS"
    assert executed["v"] is False  # never ran the handler


@pytest.mark.asyncio
async def test_unknown_tool_rejected():
    async def handler(path):
        return {}

    eng = ExecutionEngine(_registry(handler), ResourceLockManager())
    res = await eng.run(_proposal(tool_key="word.explode", agent_allowed_tools=["word.explode"]))
    assert res.state == ExecState.FAILED
    assert res.error_class == "TOOL_NOT_FOUND"
