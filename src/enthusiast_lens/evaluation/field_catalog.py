"""Load the frozen, answer-key-independent V1 objective field catalog."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from enthusiast_lens.deterministic.validation import validate_field_id


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
DEFAULT_FIELD_CATALOG_PATH = (
    Path(__file__).resolve().parents[3] / "evals" / "task_definition" / "v1_objective_field_catalog.json"
)


class FieldCatalogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field_id: NonEmptyText
    category: NonEmptyText
    description: NonEmptyText

    @model_validator(mode="after")
    def validate_id(self) -> "FieldCatalogEntry":
        validate_field_id(self.field_id)
        return self


class FieldCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    catalog_version: NonEmptyText
    provenance: NonEmptyText
    fields: tuple[FieldCatalogEntry, ...]

    @model_validator(mode="after")
    def validate_fields(self) -> "FieldCatalog":
        ids = [field.field_id for field in self.fields]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("field catalog must contain unique non-empty fields")
        if any(term in field_id.casefold() for field_id in ids for term in ("feel", "fun", "sound_quality", "ride_quality", "reliability", "tuning_potential")):
            raise ValueError("subjective field is not allowed in objective catalog")
        return self

    @property
    def field_ids(self) -> tuple[str, ...]:
        return tuple(field.field_id for field in self.fields)


def load_field_catalog(path: Path = DEFAULT_FIELD_CATALOG_PATH) -> FieldCatalog:
    """Load and validate the fixed catalog without consulting evaluation answers."""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"field catalog could not be loaded: {error}") from error
    return FieldCatalog.model_validate(raw)


def field_catalog_hash(path: Path = DEFAULT_FIELD_CATALOG_PATH) -> str:
    """Return the SHA-256 of the catalog bytes exactly as stored."""

    return hashlib.sha256(path.read_bytes()).hexdigest()
