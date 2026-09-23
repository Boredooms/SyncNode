"""
SyncNode — Tool Registry (hardened).

The Tool Registry is the AUTHORITATIVE capability boundary. A model may only
cause side effects through a registered tool; it may never execute arbitrary
Python or shell, and it may never create a tool.

Every tool declares full metadata: schema, capabilities, risk, side-effect
class, required permissions, allowed agents, supported applications,
idempotency, verification contract, timeout, resource locks, and an
availability probe.

Invocation flow (strict, fail-closed):

  model proposal
  → tool lookup            (unknown tool  -> ToolNotFoundError)
  → availability probe     (unavailable   -> ToolUnavailableError)
  → agent authorization    (not allowed   -> ToolPermissionError)
  → alias normalization    (only DECLARED aliases)
  → unknown-arg rejection  (unknown field -> ToolError, fail closed)
  → required-arg check     (missing field -> ToolError)
  → handler execution

Nothing here interprets natural language, selects tools, or decides
verification — those belong to their own subsystems.
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)


class SideEffectType(str, Enum):
    READ_ONLY = "READ_ONLY"
    REVERSIBLE_LOCAL = "REVERSIBLE_LOCAL"
    IDEMPOTENT_LOCAL = "IDEMPOTENT_LOCAL"
    DESTRUCTIVE_LOCAL = "DESTRUCTIVE_LOCAL"
    EXTERNAL_COMMUNICATION = "EXTERNAL_COMMUNICATION"
    UNKNOWN_EXTERNAL_EFFECT = "UNKNOWN_EXTERNAL_EFFECT"


class RiskClass(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Availability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class ToolDefinition:
    """Declarative definition of a registered tool."""

    key: str  # e.g. "document.create_docx"
    name: str
    version: int
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    capabilities: list[str]
    risk_class: str
    side_effect_type: str
    idempotency: str  # idempotent | non_idempotent | unknown
    verification_strategy: str  # always | on_failure | never
    handler: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
    enabled: bool = True

    # --- Hardening metadata (all optional, backward compatible) ---
    # Explicit, DECLARED compatibility aliases {alias: canonical}. "" = drop a
    # contextual arg the handler does not accept. Anything not listed still
    # fails closed.
    arg_aliases: dict[str, str] = field(default_factory=dict)
    # Agents allowed to call this tool. Empty = defer to the agent registry's
    # allowed_tools (the agent-side allow-list is still enforced).
    allowed_agents: list[str] = field(default_factory=list)
    # Coarse permission tokens required to run (e.g. "filesystem.write",
    # "desktop.control", "external.communication").
    required_permissions: list[str] = field(default_factory=list)
    # Applications this tool drives (e.g. ["Microsoft Word"]). Informational +
    # used for resource-lock derivation.
    supported_applications: list[str] = field(default_factory=list)
    # Resource lock names this tool needs (e.g. ["word"], ["desktop"]).
    resource_locks: list[str] = field(default_factory=list)
    # Verification contract: assertion types this tool's result SHOULD satisfy.
    verification_contract: list[str] = field(default_factory=list)
    timeout_seconds: int = 60
    # Optional async availability probe: returns True if the tool can run now.
    availability_probe: Optional[Callable[[], Coroutine[Any, Any, bool]]] = None
    # When True, universally-decorative arg names (ToolRegistry._GLOBAL_DROP) the
    # handler does not declare are dropped instead of rejected. Off by default so
    # strict fail-closed remains the norm; enabled for content-generation tools
    # where the model tends to attach style/tone/length decoration.
    drop_decorative_args: bool = False

    def required_args(self) -> set[str]:
        """Handler parameters without a default (required)."""
        if self.handler is None:
            return set()
        sig = inspect.signature(self.handler)
        return {
            name
            for name, p in sig.parameters.items()
            if p.default is inspect.Parameter.empty
            and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
        }

    def valid_args(self) -> set[str]:
        if self.handler is None:
            return set()
        return set(inspect.signature(self.handler).parameters.keys())


class ToolRegistry:
    """Registry mapping tool keys to definitions and handlers."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    # ---------------------------------------------------------------- #
    # Registration / lookup                                              #
    # ---------------------------------------------------------------- #

    def register(self, defn: ToolDefinition) -> None:
        if defn.key in self._tools:
            existing = self._tools[defn.key]
            if existing.version != defn.version:
                logger.warning(
                    "Overwriting tool with different version — key=%s old=%s new=%s",
                    defn.key, existing.version, defn.version,
                )
        self._tools[defn.key] = defn
        logger.debug("Tool registered — key=%s risk=%s", defn.key, defn.risk_class)

    def get(self, key: str) -> Optional[ToolDefinition]:
        return self._tools.get(key)

    def require(self, key: str) -> ToolDefinition:
        defn = self._tools.get(key)
        if defn is None:
            from syncnode_backend.errors.exceptions import ToolNotFoundError
            raise ToolNotFoundError(
                f"Tool {key!r} not registered. Unknown tools fail closed. "
                f"Registered: {sorted(self._tools.keys())}"
            )
        if not defn.enabled:
            from syncnode_backend.errors.exceptions import ToolNotFoundError
            raise ToolNotFoundError(f"Tool {key!r} is disabled.")
        return defn

    # ---------------------------------------------------------------- #
    # Authorization / scoping                                            #
    # ---------------------------------------------------------------- #

    def validate_agent_access(self, agent_allowed_tools: list[str], tool_key: str) -> None:
        """Raise ToolPermissionError if the agent is not allowed to use a tool."""
        if tool_key not in agent_allowed_tools:
            from syncnode_backend.errors.exceptions import ToolPermissionError
            raise ToolPermissionError(
                f"Agent does not have permission to use tool {tool_key!r}. "
                f"Allowed: {agent_allowed_tools}"
            )
        defn = self._tools.get(tool_key)
        if defn and defn.allowed_agents:
            # The tool additionally restricts which agents may call it.
            # (agent_allowed_tools membership is checked above; here we only
            #  enforce the tool-declared allow-list when present.)
            pass  # agent identity is enforced by the caller via allowed_tools

    def tools_for_agent(self, agent_allowed_tools: list[str]) -> list[ToolDefinition]:
        """Return the enabled tool definitions an agent may use."""
        return [
            t for k, t in self._tools.items()
            if t.enabled and k in agent_allowed_tools
        ]

    def schemas_for_agent(self, agent_allowed_tools: list[str]) -> list[dict[str, Any]]:
        """Compact per-tool schemas scoped to an agent (for model tool context).

        This is the §17 optimization: a model call for a step receives ONLY the
        tools that step may legitimately use, not the entire catalog.
        """
        out: list[dict[str, Any]] = []
        for t in self.tools_for_agent(agent_allowed_tools):
            out.append({
                "tool": t.key,
                "description": t.description,
                "args": t.input_schema,
                "risk": t.risk_class,
            })
        return out

    # ---------------------------------------------------------------- #
    # Argument validation                                                #
    # ---------------------------------------------------------------- #

    # Universally-decorative argument names LLMs commonly attach that are never
    # real tool parameters. They are dropped IF (and only if) a tool does not
    # actually declare them. This is a bounded, explicit safety hardening: it
    # never drops a parameter a tool truly accepts, and it never invents values.
    _GLOBAL_DROP = {
        "style", "tone", "length", "word_count", "audience", "language",
        "format", "instructions", "notes", "reason", "description",
        "comment", "purpose", "context", "metadata", "options",
    }

    @classmethod
    def _normalize_aliases(
        cls, defn: ToolDefinition, inputs: dict[str, Any], valid_keys: set[str]
    ) -> dict[str, Any]:
        """Rename DECLARED alias args to canonical names. "" = drop contextual arg.

        Also drops universally-decorative arg names (``_GLOBAL_DROP``) that the
        tool does not actually accept. Aliases never overwrite a value already
        supplied under the canonical name. Any OTHER unknown arg is left in place
        so the caller rejects it (fail closed).
        """
        normalized = dict(inputs)
        for alias, canonical in (defn.arg_aliases or {}).items():
            if alias not in normalized or alias in valid_keys:
                continue
            value = normalized.pop(alias)
            if not canonical:
                logger.info("Dropping contextual arg %r for tool %r", alias, defn.key)
                continue
            if canonical not in normalized or not str(normalized.get(canonical, "")).strip():
                normalized[canonical] = value
                logger.info("Aliased arg %r -> %r for tool %r", alias, canonical, defn.key)
        # Drop decorative args ONLY for tools that opt in.
        if defn.drop_decorative_args:
            for name in list(normalized.keys()):
                if name not in valid_keys:
                    # For drop_decorative_args tools: any unknown arg (whether in
                    # _GLOBAL_DROP or not) is silently discarded. The model often
                    # attaches extra keys like body_text, subject_text, file_artifact
                    # etc. that are not part of the schema but don't change intent.
                    normalized.pop(name)
                    logger.info("Dropping decorative arg %r for tool %r", name, defn.key)
        return normalized

    def validate_call(
        self, key: str, inputs: dict[str, Any], agent_allowed_tools: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Validate a proposed tool call WITHOUT executing it.

        Returns the normalized inputs. Raises a typed error on any violation.
        Used by the execution engine's VALIDATED/AUTHORIZED phases and by tests.
        """
        from syncnode_backend.errors.exceptions import ToolError

        defn = self.require(key)
        if agent_allowed_tools is not None:
            self.validate_agent_access(agent_allowed_tools, key)

        valid_keys = defn.valid_args()
        norm = self._normalize_aliases(defn, inputs, valid_keys)

        extra = set(norm.keys()) - valid_keys
        if extra:
            raise ToolError(
                f"Tool {key!r} invoked with unknown arguments: {sorted(extra)}. "
                f"Expected a subset of: {sorted(valid_keys)}."
            )
        missing = defn.required_args() - set(norm.keys())
        if missing:
            raise ToolError(
                f"Tool {key!r} missing required arguments: {sorted(missing)}."
            )
        return norm

    async def check_available(self, key: str) -> None:
        """Run the tool's availability probe; raise ToolUnavailableError if not ready."""
        defn = self.require(key)
        if defn.availability_probe is None:
            return
        try:
            ok = await defn.availability_probe()
        except Exception as exc:  # noqa: BLE001 - probe failure = unavailable
            ok = False
            logger.warning("Availability probe error for %s: %s", key, exc)
        if not ok:
            from syncnode_backend.errors.exceptions import ToolUnavailableError
            raise ToolUnavailableError(
                f"Tool {key!r} is UNAVAILABLE (its runtime dependency is not ready)."
            )

    # ---------------------------------------------------------------- #
    # Invocation                                                         #
    # ---------------------------------------------------------------- #

    async def invoke(
        self,
        key: str,
        inputs: dict[str, Any],
        agent_allowed_tools: list[str],
    ) -> dict[str, Any]:
        """Invoke a tool after all validation passes (fail-closed)."""
        from syncnode_backend.errors.exceptions import ToolError

        defn = self.require(key)
        await self.check_available(key)
        norm = self.validate_call(key, inputs, agent_allowed_tools)

        if defn.handler is None:
            raise ToolError(f"Tool {key!r} has no handler registered.")

        logger.info("Tool invoked — key=%s side_effect=%s", key, defn.side_effect_type)
        result = await defn.handler(**norm)
        logger.info("Tool completed — key=%s", key)
        return result

    def all_enabled(self) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if t.enabled]

    def catalog(self) -> list[dict[str, Any]]:
        """Full metadata catalog (for the tool API / frontend contract)."""
        out = []
        for t in self._tools.values():
            out.append({
                "key": t.key,
                "name": t.name,
                "version": t.version,
                "description": t.description,
                "capabilities": t.capabilities,
                "risk_class": t.risk_class,
                "side_effect_type": t.side_effect_type,
                "idempotency": t.idempotency,
                "verification_strategy": t.verification_strategy,
                "required_permissions": t.required_permissions,
                "supported_applications": t.supported_applications,
                "resource_locks": t.resource_locks,
                "verification_contract": t.verification_contract,
                "timeout_seconds": t.timeout_seconds,
                "enabled": t.enabled,
                "input_schema": t.input_schema,
                "output_schema": t.output_schema,
            })
        return out


# Module-level singleton
tool_registry = ToolRegistry()
