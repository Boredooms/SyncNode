"""
SyncNode — Workflow Memory & Learning API.

GET  /api/v1/learning/memory/{task_type}        — best past strategies (hints)
GET  /api/v1/learning/candidates                — candidate strategies (review queue)
POST /api/v1/learning/candidates/{id}/review    — human decision (approve/reject/activate/deprecate)

Candidate strategies are NEVER auto-promoted; promotion is an explicit human
decision here. Nothing in this API mutates policy, tool permissions, or prompts.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from syncnode_backend.learning.memory import workflow_memory

router = APIRouter()


class ReviewRequest(BaseModel):
    decision: str  # approve | reject | activate | deprecate
    reviewer: str = "human"
    reason: str = ""


@router.get("/learning/memory/{task_type}")
async def get_best_strategies(task_type: str, limit: int = 3):
    return {"task_type": task_type, "strategies": await workflow_memory.best_strategies(task_type, limit)}


@router.get("/learning/candidates")
async def list_candidates(lifecycle: Optional[str] = None):
    return {"candidates": await workflow_memory.list_candidates(lifecycle)}


@router.post("/learning/candidates/{candidate_id}/review")
async def review_candidate(candidate_id: str, req: ReviewRequest):
    from syncnode_backend.errors.exceptions import SyncNodeError
    try:
        return await workflow_memory.review_candidate(
            candidate_id, decision=req.decision, reviewer=req.reviewer, reason=req.reason,
        )
    except SyncNodeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
