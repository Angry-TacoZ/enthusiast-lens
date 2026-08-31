"""Provider-neutral structured seed contracts for the future Hybrid pipeline."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    model_validator,
)

from .enthusiast_record import CanonicalFieldId
from .provenance import Provenance


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class StructuredFactState(StrEnum):
    """Interpretation of a structured provider value without overclaiming it."""

    REPORTED = "reported"
    STANDARD = "standard"
    OPTIONAL = "optional"
    NOT_AVAILABLE = "not_available"
    UNKNOWN = "unknown"


class StructuredVehicleIdentity(BaseModel):
    """Identity fields decoded by a structured provider; all but VIN may be absent."""

    model_config = ConfigDict(extra="forbid")

    vin: NonEmptyText
    model_year: int | None = Field(default=None, ge=1886, le=2100, strict=True)
    make: NonEmptyText | None = None
    model: NonEmptyText | None = None
    trim: NonEmptyText | None = None
    series: NonEmptyText | None = None
    body_class: NonEmptyText | None = None


class StructuredSeedFact(BaseModel):
    """One provider field mapped to a canonical runtime field."""

    model_config = ConfigDict(extra="forbid")

    field_id: CanonicalFieldId
    provider_field: NonEmptyText
    provider_value: str | None = None
    normalized_value: JsonValue | None = None
    unit: NonEmptyText | None = None
    state: StructuredFactState
    provenance: Provenance

    @model_validator(mode="after")
    def enforce_interpretation(self) -> "StructuredSeedFact":
        if self.state in {StructuredFactState.REPORTED, StructuredFactState.STANDARD}:
            if self.normalized_value is None:
                raise ValueError("reported and standard facts require a normalized value")
        elif self.normalized_value is not None:
            raise ValueError("unknown, optional, and not-available facts cannot assert a value")
        return self


class StructuredContextFact(BaseModel):
    """Exact-VIN provider context that constrains research without being a final fact."""

    model_config = ConfigDict(extra="forbid")

    provider_field: NonEmptyText
    provider_value: str | None = None
    normalized_value: JsonValue | None = None
    unit: NonEmptyText | None = None
    state: StructuredFactState
    provenance: Provenance

    @model_validator(mode="after")
    def enforce_interpretation(self) -> "StructuredContextFact":
        if self.state in {StructuredFactState.REPORTED, StructuredFactState.STANDARD}:
            if self.normalized_value is None:
                raise ValueError("reported and standard context requires a normalized value")
        elif self.normalized_value is not None:
            raise ValueError("unknown, optional, and not-available context cannot assert a value")
        return self


class StructuredVehicleSeed(BaseModel):
    """Non-final structured input for future Hybrid gap analysis and research."""

    model_config = ConfigDict(extra="forbid")

    provider: Literal["nhtsa_vpic"] = "nhtsa_vpic"
    requested_vin: NonEmptyText
    requested_model_year: int | None = Field(default=None, ge=1886, le=2100, strict=True)
    source_url: AnyHttpUrl
    retrieved_at: datetime
    identity: StructuredVehicleIdentity
    facts: tuple[StructuredSeedFact, ...]
    context_facts: tuple[StructuredContextFact, ...] = Field(default_factory=tuple)
    provider_warnings: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
    raw_provider_payload: dict[str, JsonValue]
