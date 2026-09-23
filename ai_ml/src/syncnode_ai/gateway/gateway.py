"""
SyncNode — Model Gateway.

The single boundary between all SyncNode cognition code and
concrete local model providers.

Enforces:
 - Local-only inference (MG-01)
 - Structured output validation + repair
 - Schema-repair retry loop
 - Telemetry
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncIterator, Optional, Type

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

from syncnode_ai.gateway.ollama_adapter import OllamaAdapter
from syncnode_ai.gateway.schemas import (
    ModelCapabilities,
    ModelProfile,
    ModelRequest,
    ModelResponse,
    ModelStreamEvent,
    ProviderHealth,
    ProviderScope,
    ProviderStatus,
)


class ModelGateway:
    """
    Upstream-facing model gateway.

    All Brain / Agent / Intent / Planner code calls this interface.
    Only this class and OllamaAdapter may interact with the model runtime.
    """

    def __init__(
        self,
        adapter: OllamaAdapter,
        model_id: str,
        max_repair: int = 2,
        *,
        compact_schema: bool = True,
    ) -> None:
        self._adapter = adapter
        self._model_id = model_id
        self._max_repair = max_repair
        # When True, embed a compact schema hint in the prompt instead of the
        # full pydantic JSON schema. Validation is always against the full
        # schema, so this only reduces prompt tokens.
        self._compact_schema = compact_schema

    @property
    def model_id(self) -> str:
        """The configured default model id for this gateway."""
        return self._model_id

    # ---------------------------------------------------------------- #
    # Core generate                                                      #
    # ---------------------------------------------------------------- #

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Execute a non-streaming inference request."""
        self._enforce_local_model(request)
        return await self._adapter.generate(request)

    async def stream(self, request: ModelRequest) -> AsyncIterator[ModelStreamEvent]:
        """Execute a streaming inference request."""
        self._enforce_local_model(request)
        async for event in self._adapter.stream(request):
            yield event

    # ---------------------------------------------------------------- #
    # Structured output                                                  #
    # ---------------------------------------------------------------- #

    async def generate_structured(
        self,
        request: ModelRequest,
        schema_class: Type[BaseModel],
    ) -> tuple[BaseModel, ModelResponse]:
        """
        Generate structured output and validate against a Pydantic schema.

        Attempts up to max_repair times with corrective prompting.

        Returns:
            (validated_instance, last_raw_response)

        Raises:
            StructuredOutputError: if all repair attempts fail.
        """
        from syncnode_ai.errors import StructuredOutputError

        last_response: Optional[ModelResponse] = None
        last_error: Optional[str] = None

        # Full schema is always used for validation and as the provider format.
        schema_dict = schema_class.model_json_schema()

        # Prompt hint: compact by default (fewer tokens), full on request.
        if self._compact_schema:
            from syncnode_ai.gateway._schema import compact_schema_text
            schema_hint = compact_schema_text(schema_dict)
        else:
            schema_hint = json.dumps(schema_dict, indent=2)

        new_messages = list(request.messages)
        if new_messages:
            last_msg = new_messages[-1]
            new_content = (
                last_msg.content
                + "\n\nReturn ONLY a valid JSON object matching this schema:\n"
                + schema_hint
            )
            new_messages[-1] = last_msg.model_copy(update={"content": new_content})

        req = request.model_copy(
            update={"output_schema": schema_dict, "temperature": 0.0, "messages": new_messages}
        )

        from syncnode_ai.gateway.schemas import Message

        # Invariant MG-03: one initial generation plus at most `_max_repair`
        # bounded repairs.
        total_attempts = self._max_repair + 1
        for attempt in range(1, total_attempts + 1):
            if attempt > 1 and last_error:
                logger.info(
                    "Structured-output repair attempt %d/%d — last_error=%s",
                    attempt - 1,
                    self._max_repair,
                    last_error,
                )
                repair_msg = Message(
                    role="user",
                    content=(
                        "Your previous response could not be parsed as valid JSON "
                        f"matching the required schema. Error: {last_error}\n\n"
                        f"Schema: {schema_hint}\n\n"
                        "Return ONLY valid JSON, no markdown, no explanation."
                    ),
                )
                req = req.model_copy(update={"messages": list(req.messages) + [repair_msg]})

            response = await self.generate(req)
            last_response = response

            try:
                data = self._extract_json(response)
                instance = schema_class.model_validate(data)
                return instance, response
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = str(exc)
                logger.debug(
                    "Structured-output parse failed (attempt %d/%d): %s",
                    attempt,
                    total_attempts,
                    last_error,
                )

        raise StructuredOutputError(
            f"Failed to produce valid structured output after {total_attempts} attempts "
            f"(1 initial + {self._max_repair} repairs). Last error: {last_error}"
        )

    @staticmethod
    def _extract_json(response: ModelResponse) -> Any:
        """Extract the JSON object/array from a model response."""
        if response.parsed_output is not None:
            return response.parsed_output
        raw = response.content.strip()
        match = re.search(r"(\{.*\}|\[.*\])", raw, re.DOTALL)
        if match:
            raw = match.group(1)
        return json.loads(raw)

    # ---------------------------------------------------------------- #
    # Model discovery                                                    #
    # ---------------------------------------------------------------- #

    async def discover_models(self) -> list[ModelProfile]:
        """Return profiles for all locally available models."""
        profiles = await self._adapter.list_models()
        # Filter to LOCAL scope only
        return [p for p in profiles if not p.model_id.endswith(":cloud")]

    async def get_default_profile(self) -> Optional[ModelProfile]:
        """Return the profile for the configured default model."""
        return await self._adapter.get_model_profile(self._model_id)

    # ---------------------------------------------------------------- #
    # Health                                                             #
    # ---------------------------------------------------------------- #

    async def health(self) -> ProviderHealth:
        """Return health status for the configured model."""
        return await self._adapter.health(self._model_id)

    # ---------------------------------------------------------------- #
    # Enforcement                                                        #
    # ---------------------------------------------------------------- #

    def _enforce_local_model(self, request: ModelRequest) -> None:
        """Reject any request targeting a cloud model (invariant MG-01)."""
        if request.model_id.endswith(":cloud"):
            from syncnode_ai.errors import CloudInferenceAttemptError
            raise CloudInferenceAttemptError(
                f"Attempted to use cloud model {request.model_id!r}. "
                "SyncNode enforces local-only inference."
            )

    async def close(self) -> None:
        await self._adapter.close()

