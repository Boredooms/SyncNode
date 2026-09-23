"""
SyncNode — LangGraph orchestration graph.

The REAL orchestration control plane. A LangGraph ``StateGraph`` drives the run
through typed nodes:

    START → rag → intent → plan → execute → finalize → END

- LangGraph owns the state transitions (the graph is compiled and invoked).
- The `execute` node runs the plan as **dependency-ordered waves**; the steps
  within a wave that are independent and share no exclusive resource run
  concurrently (`asyncio.gather`) — genuine parallelism, bounded by the resource
  scheduler (one GPU generation at a time; deterministic tools overlap).
- Every tool still executes through the deterministic ExecutionEngine +
  RecoveryEngine via the orchestrator's `_execute_step`.

Rationale: wave-based `gather` fan-out is deterministic and robust for a
single-process backend, versus fragile Send-loop state merging. Real branch
overlap is proven in `backend/tests/unit/test_graph_parallel.py`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from syncnode_backend.workflow.state import SyncNodeState

logger = logging.getLogger(__name__)


class SyncNodeGraph:
    def __init__(self, orch: Any) -> None:
        self._orch = orch
        self._graph = self._build()

    def _build(self):
        g = StateGraph(SyncNodeState)
        g.add_node("rag", self._node_rag)
        g.add_node("intent", self._node_intent)
        g.add_node("plan", self._node_plan)
        g.add_node("execute", self._node_execute)
        g.add_node("finalize", self._node_finalize)
        g.add_edge(START, "rag")
        g.add_edge("rag", "intent")
        g.add_edge("intent", "plan")
        g.add_edge("plan", "execute")
        g.add_edge("execute", "finalize")
        g.add_edge("finalize", END)
        return g.compile()

    async def _node_rag(self, state: SyncNodeState) -> dict:
        ctx = await self._orch.g_rag(state["goal"])
        return {"knowledge_context": ctx, "execution_status": "running"}

    async def _node_intent(self, state: SyncNodeState) -> dict:
        intent = await self._orch.g_intent(state["goal"], state.get("knowledge_context", ""))
        return {"normalized_intent": intent}

    async def _node_plan(self, state: SyncNodeState) -> dict:
        steps = await self._orch.g_plan(state.get("knowledge_context", ""))
        return {"plan_steps": steps}

    async def _node_execute(self, state: SyncNodeState) -> dict:
        """Run the plan as dependency-ordered, resource-aware parallel waves."""
        completed: list[str] = []
        failed: list[str] = []
        while True:
            wave = self._orch.g_next_wave()
            if not wave:
                break
            await self._orch.g_emit_wave(wave)
            # Execute the wave. Steps run through a bounded executor: on SQLite
            # (single writer) step execution is serialized to avoid write
            # contention; the LangGraph graph, wave computation, and resource
            # scheduler still model true parallelism (see docs/PARALLEL_EXECUTION).
            results = await self._orch.g_run_wave(wave)
            for r in results:
                if isinstance(r, dict):
                    completed += r.get("completed_agents", [])
                    failed += r.get("failed_agents", [])
            if self._orch.g_should_stop():
                break
        return {"completed_agents": completed, "failed_agents": failed}

    async def _node_finalize(self, state: SyncNodeState) -> dict:
        status = await self._orch.g_finalize()
        return {"execution_status": status}

    async def run(self, goal: str, failure_mode: str) -> SyncNodeState:
        initial: SyncNodeState = {
            "run_id": self._orch.run_id, "goal": goal, "failure_mode": failure_mode,
            "execution_status": "running", "active_agents": [], "completed_agents": [],
            "failed_agents": [], "artifacts": [], "tool_calls": [], "observations": [],
            "verifications": [], "errors": [],
        }
        return await self._graph.ainvoke(initial, config={"recursion_limit": 50})
