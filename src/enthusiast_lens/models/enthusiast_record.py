"""Canonical product-facing fact and record contracts.

The fact collection is a runtime result, not the frozen benchmark answer-key
format. Unknown is represented as a state with no fabricated value.
"""

from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    model_validator,
)

from .provenance import Confidence, OriginType, Provenance
from .trajectory import AnalysisRunMetadata
from .vehicle_context import VehicleContext


CanonicalFieldId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$",
    ),
]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class FactState(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    CONFLICTED = "conflicted"
    NOT_AVAILABLE = "not_available"
    NOT_APPLICABLE = "not_applicable"


class FactResult(BaseModel):
    """One normalized enthusiast fact and its evidence/state."""

    model_config = ConfigDict(extra="forbid")

    field_id: CanonicalFieldId
    value: JsonValue | None = None
    unit: NonEmptyText | None = None
    state: FactState
    confidence: Confidence | None = None
    provenance: tuple[Provenance, ...] = Field(default_factory=tuple)
    configuration_dependency_notes: NonEmptyText | None = None
    conflict_information: NonEmptyText | None = None
    origin: OriginType | None = None

    @model_validator(mode="after")
    def enforce_state_semantics(self) -> "FactResult":
        if self.state is FactState.KNOWN and self.value is None:
            raise ValueError("known facts require a value")
        if self.state in {
            FactState.UNKNOWN,
            FactState.NOT_AVAILABLE,
            FactState.NOT_APPLICABLE,
        } and self.value is not None:
            raise ValueError(f"{self.state.value} facts must not contain a value")
        if self.state is FactState.CONFLICTED and self.conflict_information is None:
            raise ValueError("conflicted facts require conflict_information")
        return self


class EnthusiastRecord(BaseModel):
    """Canonical JSON-serializable result shared by all future surfaces."""

    model_config = ConfigDict(extra="forbid")

    vehicle: VehicleContext
    facts: tuple[FactResult, ...]
    analysis: AnalysisRunMetadata
    warnings: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
    configuration_notes: tuple[NonEmptyText, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def enforce_record_invariants(self) -> "EnthusiastRecord":
        field_ids = [fact.field_id for fact in self.facts]
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("duplicate canonical field_id values are not allowed")
        if self.vehicle != self.analysis.input_context:
            raise ValueError("record vehicle must match analysis input_context")
        return self
