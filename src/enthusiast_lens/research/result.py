"""Pydantic contracts and development-trace persistence for research runs."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from enthusiast_lens.model import ModelEvent, ModelUsage, sanitize_for_trace
from enthusiast_lens.models import AnalysisRunMetadata, FactResult, StructuredContextFact, VehicleContext

from .evidence import EvidenceBundle


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ResearchModelOutput(BaseModel):
    """The strict JSON payload the provider is asked to return."""

    model_config = ConfigDict(extra="forbid")

    facts: tuple[FactResult, ...]
    warnings: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
    configuration_notes: tuple[NonEmptyText, ...] = Field(default_factory=tuple)


class ResearchTrajectory(BaseModel):
    """A sanitized record of all externally observable research effects."""

    model_config = ConfigDict(extra="forbid")

    trajectory_id: NonEmptyText
    started_at: datetime
    completed_at: datetime | None = None
    status: NonEmptyText
    provider: NonEmptyText
    model: NonEmptyText
    thinking_level: NonEmptyText
    instruction_version: NonEmptyText
    instruction_sha256: NonEmptyText
    vehicle: VehicleContext
    requested_field_ids: tuple[NonEmptyText, ...]
    structured_context: tuple[StructuredContextFact, ...] = Field(default_factory=tuple)
    interaction_id: NonEmptyText | None = None
    last_provider_status: NonEmptyText | None = None
    elapsed_ms: int | None = Field(default=None, ge=0)
    phase_a_latency_ms: int | None = Field(default=None, ge=0)
    phase_b_latency_ms: int | None = Field(default=None, ge=0)
    phase_a_usage: ModelUsage = Field(default_factory=ModelUsage)
    phase_b_usage: ModelUsage = Field(default_factory=ModelUsage)
    search_query_count: int = Field(default=0, ge=0)
    grounded_source_count: int = Field(default=0, ge=0)
    evidence_bundle: EvidenceBundle | None = None
    events: tuple[ModelEvent, ...] = Field(default_factory=tuple)
    usage: ModelUsage = Field(default_factory=ModelUsage)
    model_call_count: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    failures: tuple[NonEmptyText, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def completion_follows_start(self) -> "ResearchTrajectory":
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")
        return self


class ResearchRunResult(BaseModel):
    """Agent output that remains distinct from the product EnthusiastRecord."""

    model_config = ConfigDict(extra="forbid")

    facts: tuple[FactResult, ...] = Field(default_factory=tuple)
    warnings: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
    configuration_notes: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
    trajectory: ResearchTrajectory
    analysis: AnalysisRunMetadata


def write_development_trace(
    trajectory: ResearchTrajectory,
    root: Path = Path("artifacts/trajectories/dev"),
) -> Path:
    """Persist a sanitized development trace outside evaluation artifacts."""

    destination = root / f"{trajectory.trajectory_id}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(sanitize_for_trace(trajectory.model_dump(mode="json")), indent=2),
        encoding="utf-8",
    )
    return destination
