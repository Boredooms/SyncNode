"""
SyncNode — Agent Registry and Spawner.

Agents are declared, not hard-coded to prompts.
Spawning uses capability matching, never:

    if "Word" in prompt: spawn_word_agent()

The registry stores AgentDefinition objects.
The spawner selects an agent by matching required capabilities.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentDefinition:
    """Declarative agent definition — what an agent IS, not what it does on a specific run."""

    agent_id: str
    version: int
    name: str
    description: str
    capabilities: list[str]
    allowed_tools: list[str]
    risk_class: str  # normal | sensitive | external | destructive
    system_prompt: str
    model_requirements: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 120
    max_concurrent: int = 1
    enabled: bool = True


# ------------------------------------------------------------------ #
# Built-in agent definitions                                            #
# ------------------------------------------------------------------ #

BUILT_IN_AGENTS: list[AgentDefinition] = [
    AgentDefinition(
        agent_id="supervisor",
        version=1,
        name="Supervisor Agent",
        description="Orchestrates the overall workflow, handles approval gates and recovery escalation.",
        capabilities=["orchestration", "approval_management", "replan", "human_escalation"],
        allowed_tools=["workflow.approve", "workflow.reject", "workflow.replan", "workflow.pause"],
        risk_class="normal",
        system_prompt=(
            "You are the SyncNode Supervisor Agent. Your role is to oversee the execution of "
            "multi-step workflows. You manage approval gates, detect oscillation, escalate failures, "
            "and ensure the workflow completes safely. You never execute tools directly."
        ),
    ),
    AgentDefinition(
        agent_id="writer",
        version=1,
        name="Writer Agent",
        description="Generates original text content for documents. No file writes — hands off to document agent.",
        capabilities=["text_generation", "content_creation", "paragraph_writing"],
        allowed_tools=["writer.generate_paragraph"],  # Writer only generates text, no file access
        risk_class="normal",
        system_prompt=(
            "You are the SyncNode Writer Agent. Your role is to generate high-quality original text content. "
            "You produce clean, professional prose based on the task requirements. "
            "Do not include confidential information. Do not claim to be an AI in the output content. "
            "Return the generated text as a JSON object with a 'content' field."
        ),
        model_requirements={"completion": True},
    ),
    AgentDefinition(
        agent_id="document",
        version=1,
        name="Document Agent",
        description="Creates and manipulates local documents (DOCX, XLSX, PPTX, PDF).",
        capabilities=["document_creation", "document_modification", "document_inspection", "artifact_hashing"],
        allowed_tools=[
            "document.create_docx",
            "document.inspect_docx",
            "document.read_docx",
            "filesystem.write",
            "filesystem.find",
            "filesystem.hash",
        ],
        risk_class="normal",
        system_prompt=(
            "You are the SyncNode Document Agent. You create, modify, and inspect local documents. "
            "You work only within the approved workspace directory. "
            "Every file write must be followed by a structural verification."
        ),
        model_requirements={"completion": True, "tools": True},
    ),
    AgentDefinition(
        agent_id="office",
        version=1,
        name="Office Agent",
        description="Creates and inspects Excel workbooks and PowerPoint presentations.",
        capabilities=[
            "spreadsheet_creation", "spreadsheet_modification", "spreadsheet_inspection",
            "presentation_creation", "presentation_modification", "presentation_inspection",
        ],
        allowed_tools=[
            "excel.create", "excel.write_cell", "excel.write_range", "excel.read_cell",
            "excel.read_range", "excel.inspect",
            "powerpoint.create", "powerpoint.add_slide", "powerpoint.inspect",
        ],
        risk_class="normal",
        system_prompt=(
            "You are the SyncNode Office Agent. You create and inspect Excel workbooks "
            "and PowerPoint presentations within the approved workspace. Every artifact "
            "you create must be followed by a structural verification."
        ),
        model_requirements={"completion": True, "tools": True},
    ),
    AgentDefinition(
        agent_id="computer",
        version=1,
        name="Computer Agent",
        description="Controls Windows applications via UI Automation. Opens, interacts, and observes apps.",
        capabilities=["uia_control", "window_management", "screenshot_capture", "process_launch"],
        allowed_tools=[
            "computer.windows_search",
            "computer.launch_app",
            "computer.find_window",
            "computer.uia_find",
            "computer.uia_click",
            "computer.uia_type",
            "computer.key_press",
            "computer.screenshot",
            "computer.get_active_window",
        ],
        risk_class="sensitive",
        system_prompt=(
            "You are the SyncNode Computer Agent. You control Windows applications using UI Automation. "
            "Always use semantic identifiers (AutomationId, Name, ControlType) before falling back to coordinates. "
            "Never interact with UAC prompts, credential dialogs, or secure desktop surfaces. "
            "After every action, observe the result before proceeding."
        ),
        model_requirements={"completion": True, "vision": True},
    ),
    AgentDefinition(
        agent_id="browser",
        version=1,
        name="Browser Agent",
        description="Controls a Playwright browser session for web automation tasks.",
        capabilities=["browser_navigation", "dom_interaction", "file_attachment", "email_draft"],
        allowed_tools=[
            "browser.navigate",
            "browser.find_element",
            "browser.click",
            "browser.type",
            "browser.attach_file",
            "browser.screenshot",
            "browser.get_url",
            "browser.get_dom_text",
        ],
        risk_class="external",
        system_prompt=(
            "You are the SyncNode Browser Agent. You control a Chromium browser using Playwright. "
            "Use semantic locators (role, label, text) — not CSS selectors or XPath — when possible. "
            "You are NOT allowed to submit forms, click Send buttons, or trigger external communications "
            "without explicit approval. Stop at the approval boundary."
        ),
        model_requirements={"completion": True, "vision": True},
    ),
    AgentDefinition(
        agent_id="verifier",
        version=1,
        name="Verifier Agent",
        description="Observes real-world state and runs deterministic postcondition assertions.",
        capabilities=["file_verification", "uia_verification", "dom_verification", "screenshot_analysis", "artifact_validation"],
        allowed_tools=[
            "verify.file_exists",
            "verify.file_hash",
            "verify.uia_control_exists",
            "verify.uia_property",
            "verify.dom_text",
            "verify.dom_visible",
            "verify.screenshot_hash",
            "computer.screenshot",
            "filesystem.hash",
            "document.inspect_docx",
        ],
        risk_class="normal",
        system_prompt=(
            "You are the SyncNode Verifier Agent. Your role is to verify that actions actually succeeded "
            "by observing real-world state — NOT by trusting what other agents reported. "
            "A model claim is never proof. You must check files, UI state, DOM, and application state directly. "
            "Return a structured verification result: PASS or FAIL with evidence."
        ),
        model_requirements={"completion": True, "vision": True},
    ),
    AgentDefinition(
        agent_id="system",
        version=1,
        name="System Agent",
        description="Full local PC access — read/write files anywhere, run shell commands, search the filesystem, manage processes, read clipboard and environment.",
        capabilities=[
            "filesystem", "system_access", "shell",
            "system_info", "system_control", "clipboard", "registry",
        ],
        allowed_tools=[
            "system.fs_read", "system.fs_list", "system.fs_search",
            "system.fs_write", "system.fs_delete",
            "system.shell",
            "system.process_list", "system.process_kill",
            "system.clipboard_get", "system.clipboard_set",
            "system.env_get", "system.registry_get",
        ],
        risk_class="sensitive",
        system_prompt=(
            "You are the SyncNode System Agent. You have full access to the local Windows PC. "
            "You can read/write files anywhere, execute shell commands, search the filesystem, "
            "manage processes, and access the clipboard and environment. "
            "SAFETY RULES you must follow: "
            "1. For fs_delete: always call with confirm=false FIRST (dry run), show the result, then call again with confirm=true only if needed. "
            "2. For process_kill: always dry-run first (confirm=false), then confirm=true only if the user explicitly confirmed. "
            "3. For shell: never use commands matching blocked patterns (format, mass-delete, shutdown, bootloader). "
            "4. Never attempt to write to C:\\Windows, C:\\Program Files, or system32. "
            "5. When in doubt about a destructive operation, report what you would do and ask. "
            "Otherwise: be powerful and helpful — you have access to everything on this machine."
        ),
        model_requirements={"completion": True, "tools": True},
        timeout_seconds=120,
    ),
    AgentDefinition(
        agent_id="recovery",
        version=1,
        name="Recovery Agent",
        description="Handles bounded failure recovery: observe → retry → fallback → replan → escalate.",
        capabilities=["failure_analysis", "retry_management", "tool_fallback", "replan_proposal"],
        allowed_tools=[
            "computer.screenshot",
            "filesystem.find",
            "workflow.replan",
            "workflow.pause",
        ],
        risk_class="normal",
        system_prompt=(
            "You are the SyncNode Recovery Agent. When a step fails, you: "
            "1. Observe the real environment to understand what actually happened. "
            "2. Classify the failure and choose a recovery tier (retry/fallback/replan/escalate). "
            "3. Never exceed the configured recovery budget. "
            "4. Never claim a step succeeded without evidence. "
            "Return a structured recovery proposal."
        ),
    ),
]


class AgentRegistry:
    """Registry of all known agent definitions."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentDefinition] = {}
        for defn in BUILT_IN_AGENTS:
            self._agents[defn.agent_id] = defn

    def register(self, defn: AgentDefinition) -> None:
        """Register a custom agent definition."""
        self._agents[defn.agent_id] = defn
        logger.info(f"Agent registered — agent_id={defn.agent_id}")

    def get(self, agent_id: str) -> Optional[AgentDefinition]:
        """Return agent definition by ID, or None."""
        return self._agents.get(agent_id)

    def find_by_capability(self, capability: str) -> list[AgentDefinition]:
        """Return all enabled agents that have the requested capability."""
        return [
            a for a in self._agents.values()
            if a.enabled and capability in a.capabilities
        ]

    def all_enabled(self) -> list[AgentDefinition]:
        return [a for a in self._agents.values() if a.enabled]

    def spawn(self, agent_id: str) -> AgentDefinition:
        """
        Spawn (resolve) an agent by ID.

        Raises AgentNotFoundError if not registered.
        """
        defn = self._agents.get(agent_id)
        if defn is None or not defn.enabled:
            from syncnode_ai.errors import AgentNotFoundError
            raise AgentNotFoundError(
                f"Agent {agent_id!r} not found in registry. "
                f"Available: {list(self._agents.keys())}"
            )
        logger.info(f"Agent spawned — agent_id={agent_id} version={defn.version}")
        return defn

    def spawn_for_capability(self, required_capability: str) -> AgentDefinition:
        """
        Spawn the first enabled agent that satisfies the required capability.

        This is the capability-based dispatch — never use string-matching on the prompt.
        """
        candidates = self.find_by_capability(required_capability)
        if not candidates:
            from syncnode_ai.errors import AgentNotFoundError
            raise AgentNotFoundError(
                f"No agent satisfies capability {required_capability!r}. "
                f"Registered agents: {list(self._agents.keys())}"
            )
        chosen = candidates[0]
        logger.info(f"Agent spawned by capability — capability={required_capability} agent_id={chosen.agent_id}")
        return chosen


# Module-level singleton
agent_registry = AgentRegistry()
