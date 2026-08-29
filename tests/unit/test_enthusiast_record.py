from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from enthusiast_lens.models import (
    AnalysisRunMetadata,
    EnthusiastRecord,
    FactResult,
    Provenance,
    VehicleContext,
)


def synthetic_context() -> VehicleContext:
    return VehicleContext(year=2025, make="Synthetic Motors", model="Apex")


def synthetic_run(context: VehicleContext) -> AnalysisRunMetadata:
    started = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
    return AnalysisRunMetadata(
        run_id="run-synthetic-1",
        mode="full_web",
        started_at=started,
        completed_at=started + timedelta(seconds=1),
        status="succeeded",
        input_context=context,
        unknown_count=1,
    )


def synthetic_source() -> Provenance:
    return Provenance(
        source_url="https://example.com/specification",
        publisher="Synthetic Motors",
        source_type="manufacturer",
        configuration_match="exact",
        origin="researched",
        confidence="high",
        relationship="supports",
    )


def test_known_fact_requires_and_preserves_value() -> None:
    fact = FactResult(
        field_id="engine.horsepower",
        value=300,
        unit="hp",
        state="known",
        confidence="high",
        provenance=(synthetic_source(),),
        origin="researched",
    )

    assert fact.value == 300
    assert fact.provenance[0].publisher == "Synthetic Motors"


def test_unknown_fact_has_no_invented_value() -> None:
    fact = FactResult(field_id="audio.speaker_count", state="unknown")

    assert fact.value is None
    assert fact.state.value == "unknown"


def test_unknown_fact_rejects_a_value() -> None:
    with pytest.raises(ValidationError):
        FactResult(field_id="audio.speaker_count", state="unknown", value="Unknown")


@pytest.mark.parametrize("state", ["not_available", "not_applicable"])
def test_non_value_states_are_explicit(state: str) -> None:
    fact = FactResult(field_id="performance.skidpad", state=state)

    assert fact.state.value == state
    assert fact.value is None


def test_conflicted_fact_requires_conflict_information() -> None:
    with pytest.raises(ValidationError):
        FactResult(field_id="driver_assistance.acc", state="conflicted")

    fact = FactResult(
        field_id="driver_assistance.acc",
        state="conflicted",
        conflict_information="Synthetic sources disagree",
        provenance=(synthetic_source(),),
    )
    assert fact.value is None


def test_invalid_canonical_field_identifier_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FactResult(field_id="Horse Power", value=300, state="known")


def test_valid_record_serialization_preserves_unknown_and_provenance() -> None:
    context = synthetic_context()
    record = EnthusiastRecord(
        vehicle=context,
        facts=(
            FactResult(
                field_id="engine.horsepower",
                value=300,
                unit="hp",
                state="known",
                provenance=(synthetic_source(),),
                origin="researched",
            ),
            FactResult(field_id="audio.speaker_count", state="unknown"),
        ),
        analysis=synthetic_run(context),
        warnings=("Synthetic warning",),
    )

    restored = EnthusiastRecord.model_validate_json(record.model_dump_json())

    assert restored.facts[1].state.value == "unknown"
    assert restored.facts[1].value is None
    assert restored.facts[0].provenance[0].source_type.value == "manufacturer"
    assert restored == record


def test_duplicate_field_ids_are_rejected() -> None:
    context = synthetic_context()
    duplicate = FactResult(field_id="engine.horsepower", value=300, state="known")

    with pytest.raises(ValidationError, match="duplicate canonical field_id"):
        EnthusiastRecord(
            vehicle=context,
            facts=(duplicate, duplicate),
            analysis=synthetic_run(context),
        )


def test_record_rejects_mismatched_analysis_context() -> None:
    context = synthetic_context()
    other_context = VehicleContext(year=2024, make="Synthetic Motors", model="Apex")

    with pytest.raises(ValidationError, match="analysis input_context"):
        EnthusiastRecord(
            vehicle=context,
            facts=(FactResult(field_id="engine.horsepower", value=300, state="known"),),
            analysis=synthetic_run(other_context),
        )
