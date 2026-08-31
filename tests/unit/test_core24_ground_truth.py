"""Offline freeze, grading, isolation, and aggregation tests for Core 24."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from enthusiast_lens.evaluation.core24_grader import (
    GRADER_VERSION,
    compare_core24_value,
    grade_core24_fixture_result,
)
from enthusiast_lens.evaluation.full_web import BaselineResult
from enthusiast_lens.evaluation.grader import FixtureScore, summarize_scores
from enthusiast_lens.models import (
    Confidence,
    ConfigurationMatch,
    EvidenceRelationship,
    FactResult,
    FactState,
    OriginType,
    Provenance,
    RunMode,
    RunStatus,
    SourceType,
    VehicleContext,
)


ROOT = Path(__file__).parents[2]
GT = ROOT / "evals" / "ground_truth_core24_v1"
CATALOG = ROOT / "evals" / "task_definition" / "hackathon_core_24_v1_field_catalog.json"
RULES = json.loads((GT / "comparison_rules.json").read_text(encoding="utf-8"))


def _fixture_paths() -> list[Path]:
    return sorted(GT.glob("*_ground_truth.json"))


def _provenance() -> Provenance:
    return Provenance(
        source_url="https://example.test/evidence",
        publisher="Test evidence",
        source_type=SourceType.MANUFACTURER,
        configuration_match=ConfigurationMatch.EXACT,
        origin=OriginType.RESEARCHED,
        confidence=Confidence.HIGH,
        relationship=EvidenceRelationship.SUPPORTS,
    )


def _result(fixture: dict, facts: tuple[FactResult, ...]) -> BaselineResult:
    vehicle = VehicleContext.model_validate(fixture["vehicle"])
    now = datetime(2026, 8, 31, tzinfo=UTC)
    return BaselineResult(
        system_version="test-core24-system",
        fixture_id=fixture["fixture_id"],
        vehicle_family_id=fixture["vehicle_family_id"],
        vehicle=vehicle,
        run_mode=RunMode.FULL_WEB,
        model="offline-test",
        instruction_version="offline-test",
        instruction_sha256="0" * 64,
        field_catalog_version="hackathon-core-24-v1",
        field_catalog_sha256=hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
        started_at=now,
        completed_at=now,
        status=RunStatus.SUCCEEDED,
        requested_field_ids=(),
        canonical_field_ids=tuple(fact["field_id"] for fact in fixture["facts"]),
        facts=facts,
    )


def test_core24_corpus_schema_catalog_counts_and_freeze_state() -> None:
    schema = json.loads((GT / "ground_truth.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    catalog_ids = [item["field_id"] for item in json.loads(CATALOG.read_text(encoding="utf-8"))["fields"]]
    fixtures = [json.loads(path.read_text(encoding="utf-8")) for path in _fixture_paths()]

    assert len(fixtures) == 12
    assert len({item["vehicle_family_id"] for item in fixtures}) == 11
    for fixture in fixtures:
        assert not list(validator.iter_errors(fixture))
        assert fixture["fixture_metadata"]["frozen"] is True
        assert [fact["field_id"] for fact in fixture["facts"]] == catalog_ids
        assert len(fixture["facts"]) == 24


def test_core24_lock_verifies_every_locked_file() -> None:
    lock = json.loads((GT / "benchmark_lock.json").read_text(encoding="utf-8"))
    assert lock["file_count"] == 17
    assert len(lock["files"]) == 17
    for relative, expected in lock["files"].items():
        assert hashlib.sha256((GT / relative).read_bytes()).hexdigest() == expected


def test_every_scorable_fact_has_non_vpic_provenance_and_excluded_states_are_clean() -> None:
    for path in _fixture_paths():
        fixture = json.loads(path.read_text(encoding="utf-8"))
        for fact in fixture["facts"]:
            if fact["scorable"]:
                assert fact["ground_truth_status"] == "known"
                assert fact["value"] is not None
                assert fact["sources"]
                assert all(source["vpic_role"] == "none" for source in fact["sources"])
                assert all("vpic" not in source["url"].casefold() for source in fact["sources"])
            else:
                assert fact["ground_truth_status"] in {"unresolved", "not_applicable"}
                assert fact["value"] is None
                assert fact["sources"] == []


def test_comparison_rules_freeze_all_required_tolerances() -> None:
    tolerances = RULES["numeric_tolerances"]
    required = {
        "brakes_wheels_and_tires.rotor_diameters_in.*",
        "brakes_wheels_and_tires.braking_70_to_0_mph_ft",
        "engine_and_measured_performance.displacement_l",
        "engine_and_measured_performance.horsepower",
        "engine_and_measured_performance.torque_lb_ft",
        "engine_and_measured_performance.curb_weight_lb",
        "engine_and_measured_performance.pounds_per_horsepower",
        "engine_and_measured_performance.zero_to_60_mph",
        "engine_and_measured_performance.skidpad_g",
        "energy_storage.capacity.fuel_tank_gal",
        "energy_storage.capacity.battery_kwh",
    }
    assert required <= set(tolerances)
    assert all(item["absolute"] > 0 for item in tolerances.values())


@pytest.mark.parametrize(
    ("field_id", "expected", "accepted", "rejected"),
    [
        ("brakes_wheels_and_tires.rotor_diameters_in", {"front_diameter_in": 11.6, "rear_diameter_in": 11.4}, {"front_diameter_in": 11.5, "rear_diameter_in": 11.5}, {"front_diameter_in": 11.6, "rear_diameter_in": 11.6}),
        ("brakes_wheels_and_tires.default_tire", {"brand_model": "Michelin Primacy HP", "front_size": "215/45R17", "rear_size": "215/45R17"}, {"brand_model": "michelin primacy hp", "front_size": "215 / 45 R17", "rear_size": "215/45R17"}, {"brand_model": "Michelin Pilot Sport 4", "front_size": "215/45R17", "rear_size": "215/45R17"}),
        ("energy_storage.capacity", {"fuel_tank_gal": 17.2, "battery_kwh": 17.3}, {"fuel_tank_gal": 17.1, "battery_kwh": 17.8}, {"fuel_tank_gal": None, "battery_kwh": 17.3}),
        ("suspension_axles_and_chassis.suspension_layout", {"front": "MacPherson strut", "rear": "multilink"}, {"front": "MacPherson-type strut", "rear": "multi-link"}, {"front": "double wishbone", "rear": "multi-link"}),
    ],
)
def test_compound_fields_require_every_component(field_id: str, expected: dict, accepted: dict, rejected: dict) -> None:
    assert compare_core24_value(field_id, accepted, expected, RULES)[0]
    assert not compare_core24_value(field_id, rejected, expected, RULES)[0]


def test_core24_grader_self_test_scores_known_facts_and_excludes_ground_truth_unknown_na() -> None:
    path = GT / "08_charger_daytona_ground_truth.json"
    fixture = json.loads(path.read_text(encoding="utf-8"))
    facts = []
    for expected in fixture["facts"]:
        if not expected["scorable"]:
            continue
        derived = expected["field_id"] == "engine_and_measured_performance.pounds_per_horsepower"
        facts.append(FactResult(
            field_id=expected["field_id"],
            value=expected["value"],
            unit=expected.get("unit"),
            state=FactState.KNOWN,
            provenance=() if derived else (_provenance(),),
            origin=OriginType.DERIVED if derived else OriginType.RESEARCHED,
        ))
    score = grade_core24_fixture_result(_result(fixture, tuple(facts)), ground_truth_path=path, ground_truth_root=GT)

    assert score.total_scorable_facts == 15
    assert (score.correct_count, score.error_count, score.unknown_count) == (15, 0, 0)
    assert score.excluded_not_available_count == 6
    assert score.excluded_not_applicable_count == 3
    assert score.provenance_success_rate == 1.0


def test_core24_na_and_unresolved_outputs_do_not_enter_n() -> None:
    fixture = json.loads((GT / "10_tesla_model_y_long_range_awd_ground_truth.json").read_text(encoding="utf-8"))
    score = grade_core24_fixture_result(_result(fixture, ()), ground_truth_path=GT / fixture["fixture_id"], ground_truth_root=GT)
    assert score.total_scorable_facts == 11
    assert score.unknown_count == 11
    assert score.excluded_not_available_count == 10
    assert score.excluded_not_applicable_count == 3


def test_core24_pounds_per_horsepower_is_frozen_to_two_decimals() -> None:
    for path in _fixture_paths():
        fixture = json.loads(path.read_text(encoding="utf-8"))
        by_id = {fact["field_id"]: fact for fact in fixture["facts"]}
        derived = by_id["engine_and_measured_performance.pounds_per_horsepower"]
        hp = by_id["engine_and_measured_performance.horsepower"]
        weight = by_id["engine_and_measured_performance.curb_weight_lb"]
        if hp["scorable"] and weight["scorable"]:
            assert derived["value"] == round(weight["value"] / hp["value"], 2)
        else:
            assert derived["ground_truth_status"] == "unresolved"


def test_core24_family_macro_averages_paired_mini_before_headline() -> None:
    base = dict(
        grader_version=GRADER_VERSION,
        comparison_rules_sha256="rules",
        ground_truth_corpus_sha256="corpus",
        system_version="system",
        total_scorable_facts=1,
        known_count=1,
        error_count=0,
        unknown_count=0,
        excluded_not_available_count=0,
        excluded_not_applicable_count=0,
        provenance_bearing_correct_known_count=1,
        provenance_eligible_correct_known_count=1,
        attempted_fact_accuracy=1.0,
        error_rate=0.0,
        attempted_fact_error_rate=0.0,
        unknown_rate=0.0,
        provenance_success_rate=1.0,
        fields=(),
    )
    one = FixtureScore(fixture_id="02a", vehicle_family_id="02_mini", correct_count=1, correct_enthusiast_fact_coverage=1.0, **base)
    zero = FixtureScore(fixture_id="02b", vehicle_family_id="02_mini", correct_count=0, correct_enthusiast_fact_coverage=0.0, **{**base, "known_count": 0, "unknown_count": 1, "attempted_fact_accuracy": None, "unknown_rate": 1.0, "provenance_bearing_correct_known_count": 0, "provenance_eligible_correct_known_count": 0, "provenance_success_rate": None})
    other = FixtureScore(fixture_id="03", vehicle_family_id="03_gr86", correct_count=1, correct_enthusiast_fact_coverage=1.0, **base)
    summary = summarize_scores((one, zero, other))
    assert summary.scored_vehicle_family_count == 2
    assert summary.headline_family_macro_cefc == pytest.approx(0.75)


def test_runtime_and_provider_modules_do_not_import_or_name_core24_answer_key() -> None:
    allowed = {ROOT / "src" / "enthusiast_lens" / "evaluation" / "core24_grader.py"}
    offenders = []
    for path in (ROOT / "src" / "enthusiast_lens").rglob("*.py"):
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        if "ground_truth_core24_v1" in text or "core24_grader" in text:
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_runtime_inputs_contain_no_core24_answer_key_fields() -> None:
    raw = (ROOT / "evals" / "inputs" / "benchmark_inputs.json").read_text(encoding="utf-8").casefold()
    for forbidden in ("ground_truth_status", "numeric_tolerances", "comparison_rules_version", "expected_value", "answer_key"):
        assert forbidden not in raw
