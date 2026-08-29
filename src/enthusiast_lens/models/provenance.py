"""Structured provenance retained with every externally supported fact."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, StringConstraints


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class SourceType(StrEnum):
    MANUFACTURER = "manufacturer"
    MANUFACTURER_SERVICE_OR_PARTS = "manufacturer_service_or_parts"
    GOVERNMENT_OR_REGULATORY = "government_or_regulatory"
    INSTRUMENTED_TEST = "instrumented_test"
    REPUTABLE_AUTOMOTIVE_PUBLICATION = "reputable_automotive_publication"
    TECHNICAL_DATABASE = "technical_database"
    DEALER_OR_WINDOW_STICKER = "dealer_or_window_sticker"
    MARKETPLACE = "marketplace"
    SECONDARY_SOURCE = "secondary_source"


class ConfigurationMatch(StrEnum):
    EXACT = "exact"
    SAME_TRIM = "same_trim"
    SAME_POWERTRAIN = "same_powertrain"
    SAME_MODEL_YEAR = "same_model_year"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class OriginType(StrEnum):
    STRUCTURED = "structured"
    RESEARCHED = "researched"
    DERIVED = "derived"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceRelationship(StrEnum):
    SUPPORTS = "supports"
    CONFLICTS = "conflicts"
    CONTEXT = "context"


class Provenance(BaseModel):
    """One evidence relationship, with optional fields for incomplete sources."""

    model_config = ConfigDict(extra="forbid")

    source_url: AnyHttpUrl | None = None
    publisher: NonEmptyText | None = None
    source_type: SourceType
    configuration_match: ConfigurationMatch | None = None
    origin: OriginType
    confidence: Confidence | None = None
    retrieved_at: datetime | None = None
    notes: NonEmptyText | None = None
    relationship: EvidenceRelationship
