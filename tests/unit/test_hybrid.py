from pathlib import Path
from types import SimpleNamespace

import pytest

from enthusiast_lens.evaluation.field_catalog import load_field_catalog
from enthusiast_lens.evaluation.hybrid import HybridRunner, _seeds
from enthusiast_lens.models import (
    Confidence,
    ConfigurationMatch,
    EvidenceRelationship,
    OriginType,
    Provenance,
    SourceType,
)
from enthusiast_lens.models.structured_seed import StructuredFactState


ROOT = Path(__file__).resolve().parents[2]


def _fact(field, value, state=StructuredFactState.REPORTED):
    return SimpleNamespace(
        provider_field=field,
        normalized_value=value,
        state=state,
        provenance=Provenance(
            source_url="https://example.test/vpic",
            publisher="NHTSA",
            source_type=SourceType.GOVERNMENT_OR_REGULATORY,
            configuration_match=ConfigurationMatch.EXACT,
            origin=OriginType.STRUCTURED,
            confidence=Confidence.MEDIUM,
            relationship=EvidenceRelationship.SUPPORTS,
        ),
    )


def _targets(seed):
    runner = object.__new__(HybridRunner)
    runner.catalog = load_field_catalog(ROOT / "evals/task_definition/v1_objective_field_catalog.json")
    return runner.targets(seed)


def test_vpic_seeds_only_clean_high_value_canonical_matches():
    seed = SimpleNamespace(
        facts=(
            _fact("DisplacementCC", 1998),
            _fact("EngineHP", 181),
            _fact("EngineConfiguration", "In-Line"),
            _fact("EngineCylinders", 4),
            _fact("CurbWeightLB", 2403),
            _fact("TransmissionSpeeds", 6),
            _fact("DriveType", "Rear-Wheel Drive"),
        )
    )

    facts = _seeds(seed)

    assert {fact.field_id: fact.value for fact in facts} == {
        "engine_and_measured_performance.displacement_cc": 1998,
        "engine_and_measured_performance.horsepower": 181,
        "engine_and_measured_performance.engine_configuration": "inline 4-cylinder",
        "engine_and_measured_performance.curb_weight": 2403,
        "transmission.gear_count": 6,
        "drivetrain_and_differentials.layout": "RWD",
    }
    assert {fact.field_id: fact.unit for fact in facts} == {
        "engine_and_measured_performance.displacement_cc": "cc",
        "engine_and_measured_performance.horsepower": "hp",
        "engine_and_measured_performance.engine_configuration": None,
        "engine_and_measured_performance.curb_weight": "lb",
        "transmission.gear_count": None,
        "drivetrain_and_differentials.layout": None,
    }
    engine = next(
        fact
        for fact in facts
        if fact.field_id == "engine_and_measured_performance.engine_configuration"
    )
    assert len(engine.provenance) == 2
    assert all(fact.origin is OriginType.STRUCTURED and fact.provenance for fact in facts)


def test_blank_malformed_ambiguous_and_incompatible_values_do_not_seed():
    seed = SimpleNamespace(
        facts=(
            _fact("DisplacementCC", "not numeric"),
            _fact("EngineHP", 0),
            _fact("EngineConfiguration", "Rotary"),
            _fact("EngineCylinders", 2),
            _fact("CurbWeightLB", None, StructuredFactState.UNKNOWN),
            _fact("TransmissionSpeeds", 6.5),
            _fact("DriveType", "2WD"),
            _fact("AdaptiveCruiseControl", True),
            _fact("TransmissionStyle", "Automatic"),
        )
    )

    assert _seeds(seed) == ()


def test_engine_configuration_requires_supported_layout_and_cylinder_count():
    assert _seeds(SimpleNamespace(facts=(_fact("EngineConfiguration", "In-Line"),))) == ()
    assert _seeds(
        SimpleNamespace(
            facts=(_fact("EngineConfiguration", "In-Line"), _fact("EngineCylinders", 4))
        )
    )[0].value == "inline 4-cylinder"


@pytest.mark.parametrize(
    ("provider_value", "canonical_value"),
    [
        ("Rear-Wheel Drive", "RWD"),
        ("All-Wheel Drive (AWD)", "AWD"),
        ("4x4", "4WD"),
    ],
)
def test_unambiguous_vpic_drivetrain_aliases_seed_layout(provider_value, canonical_value):
    facts = _seeds(SimpleNamespace(facts=(_fact("DriveType", provider_value),)))

    assert [(fact.field_id, fact.value) for fact in facts] == [
        ("drivetrain_and_differentials.layout", canonical_value)
    ]


def test_transmission_style_is_not_collapsed_into_mechanism_or_control_type():
    seed = SimpleNamespace(facts=(_fact("TransmissionStyle", "Automatic"),))

    assert _seeds(seed) == ()
    targets = _targets(seed)
    assert "transmission.mechanism" in targets
    assert "transmission.control_type" in targets


def test_seeded_ids_are_removed_from_research_targets_without_duplicates():
    seed = SimpleNamespace(
        facts=(
            _fact("DisplacementCC", 1998),
            _fact("EngineHP", 181),
            _fact("EngineConfiguration", "V-Shaped"),
            _fact("EngineCylinders", 6),
            _fact("CurbWeightLB", 3500),
            _fact("TransmissionSpeeds", 10),
            _fact("DriveType", "All-Wheel Drive"),
        )
    )
    seeded_ids = {fact.field_id for fact in _seeds(seed)}
    targets = _targets(seed)

    assert seeded_ids.isdisjoint(targets)
    assert len(targets) == 85
    assert len(targets) == len(set(targets))


def test_duplicate_relevant_provider_fields_are_rejected():
    seed = SimpleNamespace(facts=(_fact("EngineHP", 181), _fact("EngineHP", 200)))

    with pytest.raises(ValueError, match="duplicate vPIC provider field"):
        _seeds(seed)
