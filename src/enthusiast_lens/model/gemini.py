"""Official Gemini Generate Content adapter with sanitized trace extraction."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import (
    ModelEvent,
    ModelExecution,
    ModelProviderError,
    ModelUsage,
    ProviderDiagnostic,
    StructuredModelRequest,
    sanitize_for_trace,
    to_jsonable,
    utc_now,
)


GEMINI_PROVIDER = "gemini"
GEMINI_MODEL = "gemini-3.6-flash"
GeminiModel = Literal["gemini-3.7-flash", "gemini-3.6-flash"]
SUPPORTED_GEMINI_MODELS = frozenset({"gemini-3.7-flash", "gemini-3.6-flash"})
TERMINAL_INTERACTION_STATUSES = frozenset(
    {"completed", "failed", "cancelled", "incomplete", "budget_exceeded"}
)


class MissingGeminiApiKeyError(ModelProviderError):
    """Raised when the runtime environment does not provide a Gemini key."""


class GeminiSettings(BaseModel):
    """Non-secret Gemini runtime settings loaded from environment variables."""

    model_config = ConfigDict(extra="forbid")

    model: GeminiModel = GEMINI_MODEL
    thinking_level: Literal["medium"] = "medium"
    request_timeout_seconds: float = Field(default=15, gt=0, le=30)
    poll_interval_seconds: float = Field(default=2, gt=0, le=10)
    wall_clock_deadline_seconds: float = Field(default=90, gt=0, le=180)
    max_repair_attempts: Literal[0] = 0
    max_model_calls: Literal[2] = 2
    max_search_calls: int | None = Field(default=4, ge=0, le=20)

    @model_validator(mode="after")
    def validate_deadline(self) -> "GeminiSettings":
        if self.wall_clock_deadline_seconds <= self.request_timeout_seconds:
            raise ValueError("wall_clock_deadline_seconds must exceed request_timeout_seconds")
        return self

    @classmethod
    def from_environment(cls) -> "GeminiSettings":
        """Load only non-secret configuration from the process environment."""

        def optional_int(name: str, default: int | None) -> int | None:
            raw = os.getenv(name)
            return default if raw in (None, "") else int(raw)

        return cls(
            model=os.getenv("ENTHUSIAST_LENS_MODEL", GEMINI_MODEL),
            thinking_level=os.getenv("ENTHUSIAST_LENS_THINKING_LEVEL", "medium"),
            request_timeout_seconds=float(
                os.getenv("ENTHUSIAST_LENS_REQUEST_TIMEOUT_SECONDS", "15")
            ),
            poll_interval_seconds=float(os.getenv("ENTHUSIAST_LENS_POLL_INTERVAL_SECONDS", "2")),
            wall_clock_deadline_seconds=float(
                os.getenv("ENTHUSIAST_LENS_WALL_CLOCK_DEADLINE_SECONDS", "90")
            ),
            max_search_calls=optional_int("ENTHUSIAST_LENS_MAX_SEARCH_CALLS", 4),
        )

    @staticmethod
    def require_api_key() -> str:
        """Read the key only at the boundary and never serialize it."""

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise MissingGeminiApiKeyError("GEMINI_API_KEY is required for a live Gemini request")
        return api_key


class GeminiPricing(BaseModel):
    """Verified standard USD pricing shared by Gemini 3.6/3.7 Flash (August 2026)."""

    model_config = ConfigDict(extra="forbid")

    input_usd_per_million_tokens: float = 0.75
    output_usd_per_million_tokens: float = 3.75
    effective_through: str = "2026-12-31"

    def estimate(
        self,
        input_tokens: int | None,
        output_tokens: int | None,
        thinking_tokens: int | None = None,
    ) -> float | None:
        if input_tokens is None or output_tokens is None:
            return None
        billed_output_tokens = output_tokens + (thinking_tokens or 0)
        return round(
            (input_tokens / 1_000_000 * self.input_usd_per_million_tokens)
            + (billed_output_tokens / 1_000_000 * self.output_usd_per_million_tokens),
            8,
        )


def _as_mapping(value: Any) -> dict[str, Any]:
    converted = to_jsonable(value)
    return converted if isinstance(converted, dict) else {}


def _provider_diagnostic(
    error: Exception,
    *,
    stage: str,
    started: float,
    interaction_id: str | None = None,
) -> ProviderDiagnostic:
    """Extract useful SDK/HTTP diagnostics without credentials or headers."""

    response = getattr(error, "response", None)
    http_status = getattr(error, "status_code", None) or getattr(response, "status_code", None)
    body: Any = getattr(error, "body", None)
    if body is None and response is not None:
        try:
            body = response.json()
        except Exception:
            body = getattr(response, "text", None)
    provider_code = getattr(error, "code", None)
    provider_type = getattr(error, "type", None)
    provider_message = getattr(error, "message", None) or str(error) or None
    if isinstance(body, Mapping):
        error_body = body.get("error")
        if isinstance(error_body, Mapping):
            provider_code = provider_code or error_body.get("code") or error_body.get("status")
            provider_type = provider_type or error_body.get("type") or error_body.get("status")
            provider_message = provider_message or error_body.get("message")
    return ProviderDiagnostic(
        request_stage=stage,
        exception_class=type(error).__name__,
        http_status=int(http_status) if isinstance(http_status, int) else None,
        provider_code=str(provider_code) if provider_code is not None else None,
        provider_type=str(provider_type) if provider_type is not None else None,
        provider_message=sanitize_for_trace(provider_message) if provider_message else None,
        response_body=sanitize_for_trace(body) if body is not None else None,
        elapsed_ms=round((time.perf_counter() - started) * 1000),
        interaction_id_issued=interaction_id is not None,
    )


def _first_text_output(interaction: Mapping[str, Any]) -> str:
    output_text = interaction.get("output_text")
    if isinstance(output_text, str) and output_text:
        return output_text
    text_parts: list[str] = []
    for step in interaction.get("steps", []):
        step_data = _as_mapping(step)
        if step_data.get("type") != "model_output":
            continue
        for content in step_data.get("content", []):
            content_data = _as_mapping(content)
            if content_data.get("type") == "text" and isinstance(content_data.get("text"), str):
                text_parts.append(content_data["text"])
    return "".join(text_parts)


def _usage_from_interaction(interaction: Mapping[str, Any]) -> ModelUsage:
    usage_data = _as_mapping(interaction.get("usage"))

    def integer(*keys: str) -> int | None:
        for key in keys:
            value = usage_data.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
        return None

    input_tokens = integer("total_input_tokens", "prompt_tokens", "input_tokens")
    output_tokens = integer("total_output_tokens", "completion_tokens", "output_tokens")
    thinking_tokens = integer("total_thought_tokens", "thinking_tokens", "thought_tokens")
    total_tokens = integer("total_tokens", "total_token_count")
    estimated_cost = GeminiPricing().estimate(input_tokens, output_tokens, thinking_tokens)
    note = (
        "Estimated from measured input and output tokens using the August 2026 "
        "Gemini 3.6/3.7 Flash standard rates; thinking tokens are billed at the "
        "output-token rate."
        if estimated_cost is not None
        else "Provider did not expose both input and output token counts; cost is unknown."
    )
    return ModelUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        thinking_tokens=thinking_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost,
        pricing_note=note,
    )


def _usage_from_generate_response(response: Any) -> ModelUsage:
    data = _as_mapping(getattr(response, "usage_metadata", None))

    def integer(*keys: str) -> int | None:
        for key in keys:
            value = data.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
        return None

    input_tokens = integer("prompt_token_count", "input_token_count")
    output_tokens = integer("candidates_token_count", "output_token_count")
    thinking_tokens = integer("thoughts_token_count", "thinking_token_count")
    tool_use_tokens = integer("tool_use_prompt_token_count", "tool_tokens")
    total_tokens = integer("total_token_count", "total_tokens")
    estimated_cost = GeminiPricing().estimate(input_tokens, output_tokens, thinking_tokens)
    return ModelUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        thinking_tokens=thinking_tokens,
        tool_use_tokens=tool_use_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost,
        pricing_note=(
            "Estimated from Generate Content usage using August 2026 Gemini 3.6/3.7 Flash rates; "
            "thinking tokens are billed at the output-token rate."
            if estimated_cost is not None
            else "Provider did not expose both input and output token counts; cost is unknown."
        ),
    )


def _events_from_generate_response(response: Any) -> tuple[ModelEvent, ...]:
    """Capture only observable Generate Content text and grounding metadata."""

    response_data = _as_mapping(response)
    events: list[ModelEvent] = []

    def append(event_type: str, details: Any) -> None:
        events.append(
            ModelEvent(
                sequence=len(events) + 1,
                event_type=event_type,
                observed_at=utc_now(),
                details=sanitize_for_trace(details),
            )
        )

    text = getattr(response, "text", None)
    if isinstance(text, str) and text:
        append("model_output", {"text": text})
    candidates = getattr(response, "candidates", None) or []
    candidate_data = _as_mapping(candidates[0]) if candidates else {}
    grounding = _as_mapping(candidate_data.get("grounding_metadata"))
    queries = grounding.get("web_search_queries") or grounding.get("web_search_queries", [])
    if isinstance(queries, list):
        for query in queries:
            append("google_search_query", {"query": query})
    chunks = grounding.get("grounding_chunks", [])
    if isinstance(chunks, list):
        for index, chunk in enumerate(chunks):
            chunk_data = _as_mapping(chunk)
            web = _as_mapping(chunk_data.get("web"))
            if web.get("uri"):
                append("grounding_source", {"index": index, "url": web.get("uri"), "title": web.get("title")})
    supports = grounding.get("grounding_supports", [])
    if isinstance(supports, list):
        for support in supports:
            support_data = _as_mapping(support)
            append("grounding_support", support_data)
            append("citation", support_data)
    if not grounding:
        # Preserve provider response metadata that is observable without inventing steps.
        response_id = response_data.get("response_id")
        if response_id:
            append("provider_response", {"response_id": response_id})
    return tuple(events)


def _events_from_interaction(interaction: Mapping[str, Any]) -> tuple[ModelEvent, ...]:
    """Retain inspectable steps/citations, excluding thought and signature payloads."""

    events: list[ModelEvent] = []

    def append(event_type: str, details: Any) -> None:
        events.append(
            ModelEvent(
                sequence=len(events) + 1,
                event_type=event_type,
                observed_at=utc_now(),
                details=sanitize_for_trace(details),
            )
        )

    if interaction.get("id"):
        append("provider_interaction", {"interaction_id": interaction["id"]})
    for step in interaction.get("steps", []):
        step_data = _as_mapping(step)
        step_type = str(step_data.get("type", "provider_step"))
        if "thought" in step_type.casefold() or "reasoning" in step_type.casefold():
            continue
        append(step_type, step_data)
        if step_type == "model_output":
            for content in step_data.get("content", []):
                content_data = _as_mapping(content)
                if content_data.get("thought"):
                    continue
                annotations = content_data.get("annotations", [])
                for annotation in annotations if isinstance(annotations, list) else []:
                    annotation_data = _as_mapping(annotation)
                    if "citation" in str(annotation_data.get("type", "")).casefold():
                        append("citation", annotation_data)
    return tuple(events)


class GeminiModelClient:
    """Synchronous ``google-genai`` Generate Content adapter for V1 research."""

    def __init__(self, settings: GeminiSettings, client: Any | None = None) -> None:
        self._settings = settings
        self._client = client

    def _client_or_create(self) -> Any:
        if self._client is not None:
            return self._client
        from google import genai

        self._client = genai.Client(api_key=self._settings.require_api_key())
        return self._client

    def _validate_request(self, request: StructuredModelRequest) -> None:
        if request.model != self._settings.model or (
            request.thinking_level is not None and request.thinking_level != self._settings.thinking_level
        ):
            raise ModelProviderError("request model configuration does not match configured Gemini settings")

    @staticmethod
    def _interaction_body(request: StructuredModelRequest, *, background: bool) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": request.model,
            "input": request.prompt,
        }
        if request.thinking_level is not None:
            body["generation_config"] = {"thinking_level": request.thinking_level}
        if background:
            body["background"] = True
        if request.system_instruction is not None:
            body["system_instruction"] = request.system_instruction
        if request.response_schema is not None:
            body["response_format"] = {
                "type": "text",
                "mime_type": "application/json",
                "schema": request.response_schema,
            }
        if request.enable_google_search:
            body["tools"] = [{"type": "google_search"}]
        return body

    @staticmethod
    def _execution_from_interaction(interaction: Any, latency_ms: int) -> ModelExecution:
        interaction_data = _as_mapping(interaction)
        return ModelExecution(
            provider=GEMINI_PROVIDER,
            model=str(interaction_data.get("model", GEMINI_MODEL)),
            request_id=str(interaction_data["id"]) if interaction_data.get("id") else None,
            output_text=_first_text_output(interaction_data),
            status=str(interaction_data["status"]) if interaction_data.get("status") else None,
            events=_events_from_interaction(interaction_data),
            usage=_usage_from_interaction(interaction_data),
            latency_ms=latency_ms,
        )

    def execute(self, request: StructuredModelRequest) -> ModelExecution:
        """Perform one Generate Content request; outer-process control owns the deadline."""

        self._validate_request(request)
        from google.genai import types

        config: dict[str, Any] = {}
        if request.system_instruction is not None:
            config["system_instruction"] = request.system_instruction
        if request.enable_google_search:
            config["tools"] = [types.Tool(google_search=types.GoogleSearch())]
        if request.thinking_level is not None:
            config["thinking_config"] = types.ThinkingConfig(thinking_level=request.thinking_level)
        if request.response_schema is not None:
            config["response_mime_type"] = "application/json"
            # Keep the Pydantic JSON Schema as raw JSON.  The legacy
            # ``response_schema`` path converts dictionaries through the SDK's
            # typed Schema model and can rewrite ``additionalProperties`` to
            # the unsupported protobuf-style ``additional_properties`` key.
            # ``response_json_schema`` preserves the documented JSON Schema
            # keywords while leaving canonical validation local to us.
            config["response_json_schema"] = request.response_schema
        started = time.perf_counter()
        try:
            response = self._client_or_create().models.generate_content(
                model=request.model,
                contents=request.prompt,
                config=types.GenerateContentConfig(**config) if config else None,
            )
        except MissingGeminiApiKeyError:
            raise
        except Exception as error:
            diagnostic = _provider_diagnostic(error, stage="generate_content", started=started)
            raise ModelProviderError(
                f"Gemini Generate Content request failed: {diagnostic.exception_class}", diagnostic
            ) from error
        latency_ms = round((time.perf_counter() - started) * 1000)
        output_text = getattr(response, "text", None) or ""
        return ModelExecution(
            provider=GEMINI_PROVIDER,
            model=request.model,
            request_id=str(getattr(response, "response_id", None)) if getattr(response, "response_id", None) else None,
            output_text=output_text,
            status="completed",
            events=_events_from_generate_response(response),
            usage=_usage_from_generate_response(response),
            latency_ms=latency_ms,
        )

    def start_background(self, request: StructuredModelRequest) -> ModelExecution:
        """Create a server-side background interaction and capture its ID immediately."""

        self._validate_request(request)
        started = time.perf_counter()
        try:
            interaction = self._client_or_create().interactions.create(
                timeout=request.timeout_seconds, **self._interaction_body(request, background=True)
            )
        except MissingGeminiApiKeyError:
            raise
        except Exception as error:
            diagnostic = _provider_diagnostic(error, stage="create", started=started)
            raise ModelProviderError(
                f"Gemini background creation failed: {diagnostic.exception_class}", diagnostic
            ) from error
        return self._execution_from_interaction(interaction, round((time.perf_counter() - started) * 1000))

    def get_interaction(self, interaction_id: str, timeout_seconds: float) -> ModelExecution:
        """Retrieve one interaction snapshot with a bounded HTTP call."""

        started = time.perf_counter()
        try:
            interaction = self._client_or_create().interactions.get(
                id=interaction_id, timeout=timeout_seconds
            )
        except Exception as error:
            diagnostic = _provider_diagnostic(
                error, stage="poll", started=started, interaction_id=interaction_id
            )
            raise ModelProviderError(
                f"Gemini interaction retrieval failed: {diagnostic.exception_class}", diagnostic
            ) from error
        return self._execution_from_interaction(interaction, round((time.perf_counter() - started) * 1000))

    def cancel_interaction(self, interaction_id: str, timeout_seconds: float) -> ModelExecution:
        """Attempt official cancellation after the application wall-clock deadline."""

        started = time.perf_counter()
        try:
            interaction = self._client_or_create().interactions.cancel(
                id=interaction_id, timeout=timeout_seconds
            )
        except Exception as error:
            diagnostic = _provider_diagnostic(
                error, stage="cancel", started=started, interaction_id=interaction_id
            )
            raise ModelProviderError(
                f"Gemini interaction cancellation failed: {diagnostic.exception_class}", diagnostic
            ) from error
        return self._execution_from_interaction(interaction, round((time.perf_counter() - started) * 1000))
