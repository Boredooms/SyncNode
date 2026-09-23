"""
SyncNode — resource-aware agent scheduler.

Separates LOGICAL parallelism (independent agents/branches may run concurrently)
from PHYSICAL model concurrency (a 4 GB GPU can only run one local generation at
a time). The scheduler bounds:

  - model inference concurrency (default 1 — one Gemma generation at a time),
  - tool concurrency (default 3 — deterministic file tools can overlap),

and defers desktop/application exclusivity to the ResourceLockManager.

Independent artifact work (e.g. Excel + PowerPoint deterministic file creation)
can overlap; two model-generation calls are serialized by the model semaphore.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    model_concurrency: int = 1     # local GPU: one generation at a time
    tool_concurrency: int = 3      # deterministic tools may overlap


class ResourceScheduler:
    def __init__(self, limits: ResourceLimits | None = None) -> None:
        self._limits = limits or ResourceLimits()
        self._model_sem = asyncio.Semaphore(self._limits.model_concurrency)
        self._tool_sem = asyncio.Semaphore(self._limits.tool_concurrency)
        self._model_inflight = 0
        self._model_peak = 0

    @property
    def limits(self) -> ResourceLimits:
        return self._limits

    @property
    def model_peak_concurrency(self) -> int:
        return self._model_peak

    @asynccontextmanager
    async def model_slot(self, agent_id: str = ""):
        """Acquire a bounded model-inference slot (physical GPU concurrency)."""
        await self._model_sem.acquire()
        self._model_inflight += 1
        self._model_peak = max(self._model_peak, self._model_inflight)
        try:
            yield
        finally:
            self._model_inflight -= 1
            self._model_sem.release()

    @asynccontextmanager
    async def tool_slot(self, agent_id: str = ""):
        await self._tool_sem.acquire()
        try:
            yield
        finally:
            self._tool_sem.release()


# Module-level singleton for the single-process backend.
scheduler = ResourceScheduler()
