"""
SyncNode — missing exceptions referenced by tool and workflow code.
"""

from __future__ import annotations


class SyncNodeError(Exception):
    """Base for all SyncNode errors."""


class ModelError(SyncNodeError):
    pass


class ModelUnavailableError(ModelError):
    pass


class ModelNotFoundError(ModelError):
    pass


class CloudInferenceAttemptError(ModelError):
    """Rejected: cloud inference attempted."""


class StructuredOutputError(ModelError):
    pass


class ModelTimeoutError(ModelError):
    pass


class PolicyError(SyncNodeError):
    pass


class ApprovalRequiredError(PolicyError):
    pass


class SecurityBoundaryError(PolicyError):
    pass


class WorkspacePathError(SyncNodeError):
    """Path traversal / sandbox violation."""


class ToolNotFoundError(SyncNodeError):
    """Attempted to invoke an unregistered tool. Fail closed."""


class ToolPermissionError(SyncNodeError):
    """Agent does not have permission to invoke this tool."""


class ToolError(SyncNodeError):
    pass


class ToolUnavailableError(ToolError):
    """Tool's runtime dependency (app, browser, device) is not available."""


class LockTimeoutError(SyncNodeError):
    """Could not acquire a resource lock within the lease window."""


class RecoveryExhaustedError(SyncNodeError):
    """Bounded recovery attempts were exhausted."""


class KnowledgeError(SyncNodeError):
    pass


class AgentError(SyncNodeError):
    pass


class AgentNotFoundError(AgentError):
    pass


class PlannerError(SyncNodeError):
    pass


class IntentError(SyncNodeError):
    pass


class VerificationError(SyncNodeError):
    pass


class RAGError(SyncNodeError):
    pass


class RAGUnavailableError(RAGError):
    pass


class AuditError(SyncNodeError):
    pass


class RunNotFoundError(SyncNodeError):
    pass


class StepNotFoundError(SyncNodeError):
    pass
