from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from enthusiast_lens.evaluation.field_catalog import load_field_catalog
from enthusiast_lens.evaluation.full_web import BaselineResult
from enthusiast_lens.evaluation.hybrid import HybridRunner, SYSTEM_VERSION, _seeds
from enthusiast_lens.model import GeminiSettings
from enthusiast_lens.models import (
    Confidence,
    ConfigurationMatch,
    EvidenceRelationship,
    OriginType,
    Provenance,
    RunMode,
    RunStatus,
    SourceType,
)
from enthusiast_lens.models.structured_seed import StructuredFactState
from enthusiast_lens.research.instructions import INSTRUCTION_VERSION, instruction_hash


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
        "engine_and_measured_performance.curb_weight": 2403,
        "transmission.gear_count": 6,
        "drivetrain_and_differentials.layout": "RWD",
    }
    assert {fact.field_id: fact.unit for fact in facts} == {
        "engine_and_measured_performance.displacement_cc": "cc",
        "engine_and_measured_performance.horsepower": "hp",
        "engine_and_measured_performance.curb_weight": "lb",
        "transmission.gear_count": None,
        "drivetrain_and_differentials.layout": None,
    }
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


def test_engine_configuration_stays_a_research_target_even_when_vpic_fields_are_present():
    seed = SimpleNamespace(
        facts=(_fact("EngineConfiguration", "In-Line"), _fact("EngineCylinders", 4))
    )

    assert all(
        fact.field_id != "engine_and_measured_performance.engine_configuration"
        for fact in _seeds(seed)
    )
    assert "engine_and_measured_performance.engine_configuration" in _targets(seed)


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
    assert len(targets) == 86
    assert len(targets) == len(set(targets))


def test_duplicate_relevant_provider_fields_are_rejected():
    seed = SimpleNamespace(facts=(_fact("EngineHP", 181), _fact("EngineHP", 200)))

    with pytest.raises(ValueError, match="duplicate vPIC provider field"):
        _seeds(seed)


def _runner_with_output(output_root):
    runner = HybridRunner(output_root=output_root, settings=GeminiSettings())
    item = runner.select("01_miata_gt_auto_ground_truth.json")
    return runner, item


def _persisted_result(runner, item, *, version, status):
    return BaselineResult(
        system_version=version,
        fixture_id=item.fixture_id,
        vehicle_family_id=item.vehicle_family_id,
        vehicle=item.vehicle,
        run_mode=RunMode.HYBRID,
        model=runner.settings.model,
        instruction_version=INSTRUCTION_VERSION,
        instruction_sha256=instruction_hash(),
        field_catalog_version=runner.catalog.catalog_version,
        field_catalog_sha256=runner.catalog_hash,
        started_at=datetime.now(UTC),
        status=status,
        requested_field_ids=(),
        canonical_field_ids=runner.catalog.field_ids,
    )


@pytest.mark.parametrize("status", [RunStatus.SUCCEEDED, RunStatus.FAILED])
@pytest.mark.parametrize("version", ["hybrid-vpic-web-v1", "hybrid-vpic-web-v2"])
def test_stale_prior_version_results_are_archived_byte_for_byte_before_current_execution(
    tmp_path, monkeypatch, status, version
):
    runner, item = _runner_with_output(tmp_path)
    result_path = runner._result_path(item)
    result_path.parent.mkdir(parents=True)
    stale = _persisted_result(runner, item, version=version, status=status)
    original = stale.model_dump_json(indent=2).encode("utf-8")
    result_path.write_bytes(original)
    executed = object()
    calls = []
    monkeypatch.setattr(runner, "run_fixture", lambda selected: calls.append(selected) or executed)

    assert runner.run(item, live=True) is executed
    assert calls == [item]
    archives = list(result_path.parent.glob("attempt-*.json"))
    assert len(archives) == 1
    assert archives[0].read_bytes() == original


def test_current_v3_success_is_skipped_and_current_failed_result_waits_for_retry(tmp_path, monkeypatch):
    runner, item = _runner_with_output(tmp_path)
    result_path = runner._result_path(item)
    result_path.parent.mkdir(parents=True)
    succeeded = _persisted_result(runner, item, version=SYSTEM_VERSION, status=RunStatus.SUCCEEDED)
    result_path.write_text(succeeded.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(runner, "run_fixture", lambda selected: pytest.fail("unexpected execution"))

    assert runner.run(item, live=True) is None

    failed = _persisted_result(runner, item, version=SYSTEM_VERSION, status=RunStatus.FAILED)
    result_path.write_text(failed.model_dump_json(), encoding="utf-8")
    assert runner.run(item, live=True) == failed
    assert not list(result_path.parent.glob("attempt-*.json"))


@pytest.mark.parametrize(
    "identity_update",
    [
        {"model": "gemini-3.7-flash"},
        {"instruction_version": "research-v0"},
        {"instruction_sha256": "0" * 64},
        {"field_catalog_version": "catalog-v0"},
        {"field_catalog_sha256": "0" * 64},
    ],
)
def test_hybrid_result_reuse_requires_matching_runtime_identity(tmp_path, identity_update):
    runner, item = _runner_with_output(tmp_path)
    result = _persisted_result(
        runner, item, version=SYSTEM_VERSION, status=RunStatus.SUCCEEDED
    )

    assert not runner._identity_matches(result.model_copy(update=identity_update))
