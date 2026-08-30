"""Provider-neutral request, result, and trace contracts.

The contracts intentionally contain only externally observable execution data.
They must not retain API keys, authorization headers, or model reasoning.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import os
import re
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, JsonValue


SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "password",
        "secret",
        "access_token",
        "refresh_token",
        "x_goog_api_key",
    }
)
NON_TRACEABLE_KEY_PARTS = ("thought", "reasoning", "chain_of_thought")


def utc_now() -> datetime:
    """Return a timezone-aware timestamp for a trace event."""

    return datetime.now(UTC)


def to_jsonable(value: Any) -> JsonValue:
    """Convert SDK/Pydantic objects into a JSON-compatible value."""

    if isinstance(value, BaseModel):
        return to_jsonable(value.model_dump(mode="json", exclude_none=True))
    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump(mode="json", exclude_none=True))
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def sanitize_for_trace(value: Any) -> JsonValue:
    """Redact secrets and omit hidden reasoning before serializing a trace."""

    converted = to_jsonable(value)
    if isinstance(converted, dict):
        sanitized: dict[str, JsonValue] = {}
        for key, item in converted.items():
            normalized = key.casefold().replace("-", "_")
            if normalized in SENSITIVE_KEYS or normalized.endswith("_api_key"):
                sanitized[key] = "[redacted]"
            elif any(part in normalized for part in NON_TRACEABLE_KEY_PARTS):
                continue
            else:
                sanitized[key] = sanitize_for_trace(item)
        return sanitized
    if isinstance(converted, list):
        return [sanitize_for_trace(item) for item in converted]
    if isinstance(converted, str):
        sanitized_text = converted
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            sanitized_text = sanitized_text.replace(api_key, "[redacted]")
        sanitized_text = re.sub(
            r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+",
            r"\1[redacted]",
            sanitized_text,
        )
        sanitized_text = re.sub(
            r"(?i)([?&](?:key|api_key)=)[^&\s]+",
            r"\1[redacted]",
            sanitized_text,
        )
        return sanitized_text
    return converted


class ProviderDiagnostic(BaseModel):
    """Sanitized provider failure details safe for development trajectories."""

    model_config = ConfigDict(extra="forbid")

    request_stage: str
    exception_class: str
    http_status: int | None = None
    provider_code: str | None = None
    provider_type: str | None = None
    provider_message: str | None = None
    response_body: JsonValue | None = None
    elapsed_ms: int = Field(ge=0)
    interaction_id_issued: bool


class ModelUsage(BaseModel):
    """Measured provider usage, retaining unavailable components as ``None``."""

    model_config = ConfigDict(extra="forbid")

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    thinking_tokens: int | None = Field(default=None, ge=0)
    tool_use_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    pricing_note: str | None = None


class ModelEvent(BaseModel):
    """A sanitized, externally observable provider event."""

    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(ge=1)
    event_type: str
    observed_at: datetime
    details: dict[str, JsonValue] = Field(default_factory=dict)


class StructuredModelRequest(BaseModel):
    """A structured-output request sent through a provider adapter."""

    model_config = ConfigDict(extra="forbid")

    model: str
    prompt: str
    timeout_seconds: float = Field(gt=0, le=120)
    thinking_level: str | None = None
    system_instruction: str | None = None
    response_schema: dict[str, JsonValue] | None = None
    enable_google_search: bool = True


class ModelExecution(BaseModel):
    """Sanitized outcome returned by a provider adapter."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    request_id: str | None = None
    output_text: str = ""
    status: str | None = None
    events: tuple[ModelEvent, ...] = Field(default_factory=tuple)
    usage: ModelUsage = Field(default_factory=ModelUsage)
    latency_ms: int | None = Field(default=None, ge=0)
    provider_latency_ms: int | None = Field(default=None, ge=0)


class ModelProviderError(RuntimeError):
    """An expected failure at the provider boundary without secret payloads."""

    def __init__(self, message: str, diagnostic: ProviderDiagnostic | None = None) -> None:
        super().__init__(message)
        self.diagnostic = diagnostic


class ModelProvider(Protocol):
    """Protocol implemented by a concrete model provider adapter."""

    def execute(self, request: StructuredModelRequest) -> ModelExecution:
        """Perform one structured model request."""


class BackgroundModelProvider(Protocol):
    """Provider contract for a background interaction lifecycle."""

    def start_background(self, request: StructuredModelRequest) -> ModelExecution:
        """Create a background interaction and return its ID/status immediately."""

    def get_interaction(self, interaction_id: str, timeout_seconds: float) -> ModelExecution:
        """Retrieve one current interaction snapshot."""

    def cancel_interaction(self, interaction_id: str, timeout_seconds: float) -> ModelExecution:
        """Attempt to cancel a still-running background interaction."""
