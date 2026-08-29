from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from enthusiast_lens.models import Provenance


def test_valid_structured_source() -> None:
    source = Provenance(
        source_url="https://example.com/api/vehicle/123",
        publisher="Synthetic Data Provider",
        source_type="technical_database",
        configuration_match="exact",
        origin="structured",
        confidence="high",
        retrieved_at=datetime(2026, 8, 29, tzinfo=UTC),
        relationship="supports",
    )

    assert source.origin.value == "structured"
    assert source.relationship.value == "supports"


def test_valid_researched_source_allows_missing_optional_metadata() -> None:
    source = Provenance(
        source_type="manufacturer",
        origin="researched",
        relationship="supports",
    )

    assert source.source_url is None
    assert source.configuration_match is None
    assert source.confidence is None


def test_conflicting_source_relationship_is_explicit() -> None:
    source = Provenance(
        source_url="https://example.com/conflicting-evidence",
        source_type="marketplace",
        configuration_match="partial",
        origin="researched",
        confidence="low",
        relationship="conflicts",
        notes="Synthetic disagreement",
    )

    assert source.relationship.value == "conflicts"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_type", "blog_guess"),
        ("configuration_match", "close_enough"),
        ("origin", "model_assertion"),
        ("confidence", "certain"),
        ("relationship", "maybe"),
    ],
)
def test_invalid_controlled_values_are_rejected(field: str, value: str) -> None:
    data = {
        "source_type": "manufacturer",
        "origin": "researched",
        "relationship": "supports",
        field: value,
    }

    with pytest.raises(ValidationError):
        Provenance.model_validate(data)
