"""
SyncNode — Knowledge API (backend-only; later powers the Electron editor).

GET    /api/v1/knowledge                 — list documents (summaries)
GET    /api/v1/knowledge/{id}            — full document
POST   /api/v1/knowledge                 — create a document
PUT    /api/v1/knowledge/{id}            — update a document
DELETE /api/v1/knowledge/{id}            — delete a document
GET    /api/v1/knowledge/{id}/history    — version/hash history (from DB)
POST   /api/v1/knowledge/{id}/reindex    — refresh + persist metadata row
POST   /api/v1/knowledge/search          — lexical retrieval (provenance)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from syncnode_backend.knowledge.registry import get_knowledge_service
from syncnode_backend.persistence.database import get_session
from syncnode_backend.persistence.models import KnowledgeDocument

router = APIRouter()


class KnowledgeWriteRequest(BaseModel):
    path: str  # relative to knowledge root, must end .md
    content: str  # full markdown incl. front matter


class KnowledgeSearchRequest(BaseModel):
    query: str
    tags: Optional[list[str]] = None
    limit: int = 5


async def _persist_metadata(doc) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.doc_id == doc.id)
            .order_by(KnowledgeDocument.version.desc()).limit(1)
        )
        last = result.scalar_one_or_none()
        if last and last.content_hash == doc.content_hash:
            return  # unchanged
        version = (last.version + 1) if last else doc.version
        session.add(KnowledgeDocument(
            doc_id=doc.id, path=doc.path, doc_type=doc.type, title=doc.title,
            trust=doc.trust.value, version=version, status=doc.status,
            tags=doc.tags, content_hash=doc.content_hash, indexed=True,
        ))


@router.get("/knowledge")
async def list_knowledge():
    svc = get_knowledge_service()
    return {"documents": [d.to_summary() for d in svc.all()]}


@router.get("/knowledge/{doc_id}")
async def get_knowledge(doc_id: str):
    svc = get_knowledge_service()
    doc = svc.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return {**doc.to_summary(), "body": doc.body}


@router.post("/knowledge")
async def create_knowledge(req: KnowledgeWriteRequest):
    svc = get_knowledge_service()
    from syncnode_backend.errors.exceptions import KnowledgeError
    try:
        doc = svc.write(req.path, req.content)
    except KnowledgeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await _persist_metadata(doc)
    return doc.to_summary()


@router.put("/knowledge/{doc_id}")
async def update_knowledge(doc_id: str, req: KnowledgeWriteRequest):
    svc = get_knowledge_service()
    existing = svc.get(doc_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    from syncnode_backend.errors.exceptions import KnowledgeError
    try:
        doc = svc.write(req.path or existing.path, req.content)
    except KnowledgeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await _persist_metadata(doc)
    return doc.to_summary()


@router.delete("/knowledge/{doc_id}")
async def delete_knowledge(doc_id: str):
    svc = get_knowledge_service()
    if not svc.delete(doc_id):
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return {"deleted": doc_id}


@router.get("/knowledge/{doc_id}/history")
async def knowledge_history(doc_id: str):
    async with get_session() as session:
        result = await session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.doc_id == doc_id)
            .order_by(KnowledgeDocument.version)
        )
        rows = result.scalars().all()
        return {"doc_id": doc_id, "history": [
            {"version": r.version, "content_hash": r.content_hash,
             "trust": r.trust, "updated_at": str(r.updated_at)}
            for r in rows
        ]}


@router.post("/knowledge/{doc_id}/reindex")
async def reindex_knowledge(doc_id: str):
    svc = get_knowledge_service()
    svc.load_all()
    doc = svc.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    await _persist_metadata(doc)
    return {"reindexed": doc_id, "content_hash": doc.content_hash}


@router.post("/knowledge/search")
async def search_knowledge(req: KnowledgeSearchRequest):
    svc = get_knowledge_service()
    hits = svc.search(req.query, tags=req.tags, limit=req.limit)
    return {"query": req.query, "results": [
        {**d.to_summary(), "score": round(score, 2)} for d, score in hits
    ]}
