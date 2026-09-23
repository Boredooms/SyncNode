"""Process-wide knowledge service singleton."""

from __future__ import annotations

from functools import lru_cache

from syncnode_backend.config.settings import settings
from syncnode_backend.knowledge.service import KnowledgeService


@lru_cache(maxsize=1)
def get_knowledge_service() -> KnowledgeService:
    svc = KnowledgeService(settings.syncnode_knowledge_root)
    svc.load_all()
    return svc
