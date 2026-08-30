"""Provider-neutral grounded evidence and synthesis-output contracts."""

from __future__ import annotations

from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, JsonValue, StringConstraints

from enthusiast_lens.model import ModelUsage
from enthusiast_lens.models import Confidence, FactState, VehicleContext


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
SourceId = Annotated[str, StringConstraints(pattern=r"^S[1-9][0-9]*$")]


class GroundedSource(BaseModel):
    """One source admitted only from provider grounding metadata."""

    model_config = ConfigDict(extra="forbid")

    source_id: SourceId
    title: NonEmptyText | None = None
    url: AnyHttpUrl
    grounded_text: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
    support_details: tuple[dict[str, JsonValue], ...] = Field(default_factory=tuple)


class EvidenceBundle(BaseModel):
    """Evidence acquired from actual provider Search grounding."""

    model_config = ConfigDict(extra="forbid")

    vehicle: VehicleContext
    requested_field_ids: tuple[NonEmptyText, ...]
    research_summary: NonEmptyText
    sources: tuple[GroundedSource, ...]
    search_queries: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
    usage: ModelUsage = Field(default_factory=ModelUsage)
    latency_ms: int | None = Field(default=None, ge=0)


class ProviderFactResult(BaseModel):
    """Gemini-facing fact shape; provenance is represented only by source IDs."""

    model_config = ConfigDict(extra="forbid")

    field_id: NonEmptyText
    value: JsonValue | None = None
    unit: NonEmptyText | None = None
    state: FactState
    confidence: Confidence | None = None
    source_ids: tuple[SourceId, ...] = Field(default_factory=tuple)
    conflict_source_ids: tuple[SourceId, ...] = Field(default_factory=tuple)
    configuration_dependency_notes: NonEmptyText | None = None
    conflict_information: NonEmptyText | None = None


class ProviderResearchOutput(BaseModel):
    """Provider schema for evidence-constrained synthesis."""

    model_config = ConfigDict(extra="forbid")

    facts: tuple[ProviderFactResult, ...]
    warnings: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
    configuration_notes: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
