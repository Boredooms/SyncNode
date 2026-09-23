"""
SyncNode AI errors — mirror of the backend error hierarchy for the ai_ml package.
"""

from __future__ import annotations


class SyncNodeAIError(Exception):
    """Base for all ai_ml errors."""


class ModelError(SyncNodeAIError):
    pass


class ModelUnavailableError(ModelError):
    pass


class ModelNotFoundError(ModelError):
    pass


class CloudInferenceAttemptError(ModelError):
    """Rejected: attempt to use a cloud inference endpoint."""


class StructuredOutputError(ModelError):
    """Model failed to produce schema-valid JSON output."""


class ModelTimeoutError(ModelError):
    pass


class RAGError(SyncNodeAIError):
    pass


class RAGUnavailableError(RAGError):
    pass


class PromptInjectionError(RAGError):
    pass


class IntentError(SyncNodeAIError):
    pass


class PlannerError(SyncNodeAIError):
    pass


class AgentError(SyncNodeAIError):
    pass


class AgentNotFoundError(AgentError):
    pass
