"""Planner output schema for structured generation."""

from __future__ import annotations

from pydantic import BaseModel
from syncnode_ai.planner.schemas import PlanStep


class _PlannerOutput(BaseModel):
    steps: list[PlanStep]
