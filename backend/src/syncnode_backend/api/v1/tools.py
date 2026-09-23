"""
SyncNode — Tools & Agents catalog API (frontend contract).

GET /api/v1/tools          — full tool catalog (metadata)
GET /api/v1/tools/{key}    — one tool's metadata
GET /api/v1/agents         — agent definitions + their scoped tools
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from syncnode_backend.tools.registry import tool_registry

router = APIRouter()


def _ensure_tools_registered() -> None:
    # Tools are registered on app startup; ensure idempotently for direct calls.
    if tool_registry.all_enabled():
        return
    from syncnode_backend.documents.tools import register_document_tools
    from syncnode_backend.computer.tools import register_computer_tools
    from syncnode_backend.browser.tools import register_browser_tools
    from syncnode_backend.office.tools import register_office_tools
    for r in (register_document_tools, register_computer_tools,
              register_browser_tools, register_office_tools):
        r(tool_registry)


@router.get("/tools")
async def list_tools():
    _ensure_tools_registered()
    return {"tools": tool_registry.catalog()}


@router.get("/tools/{key}")
async def get_tool(key: str):
    _ensure_tools_registered()
    defn = tool_registry.get(key)
    if not defn:
        raise HTTPException(status_code=404, detail="Tool not found")
    for entry in tool_registry.catalog():
        if entry["key"] == key:
            return entry
    raise HTTPException(status_code=404, detail="Tool not found")


@router.get("/agents")
async def list_agents():
    _ensure_tools_registered()
    from syncnode_ai.agents.registry import agent_registry
    out = []
    for agent in agent_registry.all_enabled():
        out.append({
            "agent_id": agent.agent_id,
            "name": agent.name,
            "description": agent.description,
            "capabilities": agent.capabilities,
            "risk_class": agent.risk_class,
            "allowed_tools": agent.allowed_tools,
            "scoped_tools": tool_registry.schemas_for_agent(agent.allowed_tools),
        })
    return {"agents": out}
