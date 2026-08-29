"""Frozen benchmark inputs that are safe to expose to evaluated systems.

These contracts contain vehicle identity and source metadata only. Expected
enthusiast facts, scoring tolerances, and answer-key provenance belong only in
``evals/ground_truth`` and are intentionally not representable here.
"""

from datetime import datetime
import re
from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, StringConstraints, model_validator

from .vehicle_context import VehicleContext


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class BenchmarkInputSource(BaseModel):
    """A public source snapshot used only to establish runtime input identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_url: AnyHttpUrl
    publisher: NonEmptyText
    source_type: NonEmptyText
    captured_at: datetime
    evidence_path: NonEmptyText
    evidence_record_id: NonEmptyText

    @model_validator(mode="after")
    def require_timezone(self) -> "BenchmarkInputSource":
        if self.captured_at.tzinfo is None:
            raise ValueError("captured_at must include a timezone")
        return self


class BenchmarkInput(BaseModel):
    """One reproducible, answer-key-free input mapped to one frozen fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_id: NonEmptyText
    vehicle_family_id: NonEmptyText
    vehicle: VehicleContext
    source_evidence: tuple[BenchmarkInputSource, ...] = Field(default_factory=tuple)
    vpic_decode_verified: bool
    configuration_identity_sufficient: bool
    runtime_ready: bool
    blocker: NonEmptyText | None = None

    @model_validator(mode="after")
    def enforce_readiness(self) -> "BenchmarkInput":
        for field_name in ("trim", "body_style", "transmission", "drivetrain", "market"):
            if getattr(self.vehicle, field_name) is None:
                raise ValueError(f"vehicle {field_name} is required for benchmark input")
        has_vin = self.vehicle.vin is not None
        if has_vin and re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", self.vehicle.vin or "") is None:
            raise ValueError("VIN must be 17 valid VIN characters")
        if has_vin != self.vpic_decode_verified:
            raise ValueError("VIN presence and vPIC verification must agree")
        if self.runtime_ready:
            if not self.configuration_identity_sufficient:
                raise ValueError("runtime-ready input requires sufficient configuration identity")
            if not self.source_evidence:
                raise ValueError("runtime-ready input requires public source evidence")
            if self.blocker is not None:
                raise ValueError("runtime-ready input cannot have a blocker")
        elif self.blocker is None:
            raise ValueError("non-ready input requires a blocker")
        return self


class BenchmarkInputCorpus(BaseModel):
    """Versioned collection of benchmark runtime inputs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: NonEmptyText
    frozen_at: datetime
    inputs: tuple[BenchmarkInput, ...]

    @model_validator(mode="after")
    def enforce_corpus_invariants(self) -> "BenchmarkInputCorpus":
        if self.frozen_at.tzinfo is None:
            raise ValueError("frozen_at must include a timezone")
        fixture_ids = [item.fixture_id for item in self.inputs]
        if len(fixture_ids) != len(set(fixture_ids)):
            raise ValueError("fixture IDs must be unique")

        vins = [item.vehicle.vin for item in self.inputs if item.vehicle.vin is not None]
        if len(vins) != len(set(vins)):
            raise ValueError("VINs must be unique across benchmark inputs")
        return self
