"""Exact vehicle/configuration context for runtime analysis.

These models are independent from the frozen evaluation answer-key schema in
``evals/ground_truth``. Missing configuration data remains explicit; this
module does not infer or import nearby vehicle values.
"""

from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, StringConstraints


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class VehicleContext(BaseModel):
    """The best-known identity and configuration supplied to an analysis."""

    model_config = ConfigDict(extra="forbid")

    year: int = Field(ge=1886, le=2100, strict=True)
    make: NonEmptyText
    model: NonEmptyText
    trim: NonEmptyText | None = None
    body_style: NonEmptyText | None = None
    transmission: NonEmptyText | None = None
    drivetrain: NonEmptyText | None = None
    market: NonEmptyText | None = None
    vin: NonEmptyText | None = None
    listing_id: NonEmptyText | None = None
    listing_url: AnyHttpUrl | None = None
    packages: tuple[NonEmptyText, ...] = Field(default_factory=tuple)
    build_date_or_range: NonEmptyText | None = None
    hardware_generation: NonEmptyText | None = None
    notes: NonEmptyText | None = None
