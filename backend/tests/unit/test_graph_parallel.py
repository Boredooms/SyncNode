"""
LangGraph orchestration + real parallel fan-out/fan-in tests (Phase B/F/G).

Proves the graph actually overlaps independent branches (not a sequential loop)
using an async barrier, and that the resource scheduler bounds model concurrency.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from langgraph.graph import END, START, StateGraph  # noqa: E402
from langgraph.types import Send  # noqa: E402
from typing_extensions import TypedDict  # noqa: E402
import operator  # noqa: E402
from typing import Annotated  # noqa: E402

from syncnode_backend.runtime.scheduler import ResourceLimits, ResourceScheduler  # noqa: E402


class _S(TypedDict, total=False):
    order: Annotated[list, operator.add]


@pytest.mark.asyncio
async def test_langgraph_branches_overlap():
    """Three branches with a barrier must all be in-flight simultaneously."""
    barrier = asyncio.Barrier(3)
    overlap = {"max_inflight": 0, "inflight": 0}
    lock = asyncio.Lock()

    async def branch(state):
        async with lock:
            overlap["inflight"] += 1
            overlap["max_inflight"] = max(overlap["max_inflight"], overlap["inflight"])
        # If branches truly overlap, all 3 reach the barrier; else this deadlocks.
        await asyncio.wait_for(barrier.wait(), timeout=5.0)
        async with lock:
            overlap["inflight"] -= 1
        return {"order": [1]}

    def fan(state):
        return [Send("branch", state) for _ in range(3)]

    def join(state):
        return {}

    g = StateGraph(_S)
    g.add_node("dispatch", lambda s: {})
    g.add_node("branch", branch)
    g.add_node("join", join)
    g.add_edge(START, "dispatch")
    g.add_conditional_edges("dispatch", fan, ["branch"])
    g.add_edge("branch", "join")
    g.add_edge("join", END)
    graph = g.compile()

    result = await graph.ainvoke({"order": []})
    assert overlap["max_inflight"] == 3, "branches did not overlap (not real parallelism)"
    assert len(result["order"]) == 3


@pytest.mark.asyncio
async def test_scheduler_bounds_model_concurrency():
    """The model semaphore must serialize inference to the configured limit."""
    sched = ResourceScheduler(ResourceLimits(model_concurrency=1))
    inflight = {"cur": 0, "peak": 0}

    async def gen():
        async with sched.model_slot("agent"):
            inflight["cur"] += 1
            inflight["peak"] = max(inflight["peak"], inflight["cur"])
            await asyncio.sleep(0.05)
            inflight["cur"] -= 1

    await asyncio.gather(*[gen() for _ in range(4)])
    assert inflight["peak"] == 1, "model concurrency exceeded the GPU limit of 1"
    assert sched.model_peak_concurrency == 1


@pytest.mark.asyncio
async def test_tool_concurrency_allows_overlap():
    sched = ResourceScheduler(ResourceLimits(tool_concurrency=3))
    inflight = {"cur": 0, "peak": 0}

    async def tool():
        async with sched.tool_slot("agent"):
            inflight["cur"] += 1
            inflight["peak"] = max(inflight["peak"], inflight["cur"])
            await asyncio.sleep(0.05)
            inflight["cur"] -= 1

    await asyncio.gather(*[tool() for _ in range(3)])
    assert inflight["peak"] >= 2, "independent tools did not overlap"
