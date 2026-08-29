"""Minimal run metadata for future observable agent and pipeline execution."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from .vehicle_context import VehicleContext


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
NonNegativeInt = Annotated[int, Field(ge=0, strict=True)]
NonNegativeFloat = Annotated[float, Field(ge=0)]


class RunMode(StrEnum):
    FULL_WEB = "full_web"
    HYBRID = "hybrid"


class RunStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class AnalysisRunMetadata(BaseModel):
    """Serializable run metadata without execution or persistence behavior."""

    model_config = ConfigDict(extra="forbid")

    run_id: NonEmptyText
    mode: RunMode
    started_at: datetime
    completed_at: datetime | None = None
    status: RunStatus
    input_context: VehicleContext
    model_call_count: NonNegativeInt | None = None
    tool_call_count: NonNegativeInt | None = None
    web_search_count: NonNegativeInt | None = None
    latency_ms: NonNegativeInt | None = None
    estimated_cost_usd: NonNegativeFloat | None = None
    unknown_count: NonNegativeInt | None = None
    retry_count: NonNegativeInt | None = None
    failures: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
    event_references: tuple[NonEmptyText, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def completed_at_must_follow_started_at(self) -> "AnalysisRunMetadata":
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")
        return self
