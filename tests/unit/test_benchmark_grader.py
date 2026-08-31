import hashlib
import json
from pathlib import Path

import pytest

from enthusiast_lens.evaluation.full_web import BaselineResult
from enthusiast_lens.evaluation.grader import (
    COMPARISON_RULES_SHA256,
    GRADER_VERSION,
    FixtureScore,
    grade_fixture_result,
    summarize_scores,
    write_score_artifacts,
)
from enthusiast_lens.models import (
    Confidence,
    ConfigurationMatch,
    EvidenceRelationship,
    FactResult,
    FactState,
    OriginType,
    Provenance,
    SourceType,
)


ROOT = Path(__file__).resolve().parents[2]
FORMAL_RESULT = ROOT / "artifacts" / "evals" / "full_web" / "01_miata_gt_auto_ground_truth.json" / "result.json"


def _result_with(*facts: FactResult, fixture_id: str = "fixture.json") -> BaselineResult:
    result = BaselineResult.model_validate_json(FORMAL_RESULT.read_text(encoding="utf-8"))
    return result.model_copy(update={"facts": facts, "fixture_id": fixture_id})


def _provenance() -> Provenance:
    return Provenance(
        source_url="https://example.test/source",
        source_type=SourceType.MANUFACTURER,
        configuration_match=ConfigurationMatch.EXACT,
        origin=OriginType.RESEARCHED,
        confidence=Confidence.HIGH,
        relationship=EvidenceRelationship.SUPPORTS,
    )


def _write_fixture(root: Path) -> Path:
    root.mkdir()
    (root / "benchmark_lock.json").write_text('{"files": {}}\n', encoding="utf-8")
    fixture = {
        "schema_version": "1.0",
        "vehicle_id": "test_vehicle",
        "vehicle": {"year": 2026, "make": "Test", "model": "Vehicle", "trim": "Base", "market": "US"},
        "fixture_metadata": {"status": "frozen", "frozen": True, "created_at": "2026-01-01T00:00:00Z", "last_verified_at": "2026-01-01T00:00:00Z"},
        "facts": [
            {"field_id": "engine.output", "category": "engine_and_measured_performance", "label": "Output", "status": "known", "scorable": True, "verification_status": "verified", "sources": [{"url": "https://example.test/gt", "source_type": "manufacturer", "title": "GT", "supports_value": True}], "value_type": "number", "value": 100, "numeric_tolerance": 1},
            {"field_id": "transmission.mechanism", "category": "transmission", "label": "Mechanism", "status": "known", "scorable": True, "verification_status": "verified", "sources": [{"url": "https://example.test/gt", "source_type": "manufacturer", "title": "GT", "supports_value": True}], "value_type": "string", "value": "torque-converter automatic", "normalization": {"case_insensitive": True, "trim_whitespace": True, "accepted_aliases": ["torque converter automatic"]}},
            {"field_id": "drivetrain.locking_differential", "category": "drivetrain_and_differentials", "label": "Locking differential", "status": "known", "scorable": True, "verification_status": "verified", "sources": [{"url": "https://example.test/gt", "source_type": "manufacturer", "title": "GT", "supports_value": True}], "value_type": "boolean", "value": False},
            {"field_id": "audio.system_brand", "category": "audio", "label": "Brand", "status": "not_available", "scorable": False, "verification_status": "verified", "sources": [{"url": "https://example.test/gt", "source_type": "manufacturer", "title": "GT", "supports_value": True}], "value_type": "string"},
            {"field_id": "audio.subwoofer", "category": "audio", "label": "Subwoofer", "status": "not_applicable", "scorable": False, "verification_status": "verified", "sources": [{"url": "https://example.test/gt", "source_type": "manufacturer", "title": "GT", "supports_value": True}], "value_type": "boolean"},
        ],
    }
    path = root / "fixture.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")
    return path


def test_grader_applies_frozen_tolerance_aliases_and_provenance_exemption(tmp_path: Path) -> None:
    ground_truth_root = tmp_path / "ground_truth"
    fixture_path = _write_fixture(ground_truth_root)
    result = _result_with(
        FactResult(field_id="engine.output", value=101, state=FactState.KNOWN, provenance=(_provenance(),), origin=OriginType.RESEARCHED),
        FactResult(field_id="transmission.mechanism", value=" Torque converter automatic ", state=FactState.KNOWN, provenance=(_provenance(),), origin=OriginType.RESEARCHED),
        FactResult(field_id="drivetrain.locking_differential", value=True, state=FactState.KNOWN, provenance=(_provenance(),), origin=OriginType.RESEARCHED),
    )

    score = grade_fixture_result(result, ground_truth_path=fixture_path, ground_truth_root=ground_truth_root)

    assert score.total_scorable_facts == 3
    assert (score.correct_count, score.known_count, score.error_count, score.unknown_count) == (2, 3, 1, 0)
    assert score.correct_enthusiast_fact_coverage == pytest.approx(2 / 3)
    assert score.attempted_fact_accuracy == pytest.approx(2 / 3)
    assert score.error_rate == pytest.approx(1 / 3)
    assert score.provenance_success_rate == 1.0
    assert score.excluded_not_available_count == 1
    assert score.excluded_not_applicable_count == 1
    assert score.fields[0].comparison_rule == "numeric_tolerance"
    assert score.fields[0].reason == "within frozen numeric tolerance"
    assert score.fields[1].comparison_rule == "accepted_alias"
    assert score.fields[3].comparison_rule == "excluded_not_available"
    assert score.fields[4].comparison_rule == "excluded_not_applicable"
    assert score.ground_truth_corpus_sha256 == hashlib.sha256((ground_truth_root / "benchmark_lock.json").read_bytes()).hexdigest()


def test_grader_marks_missing_scorable_fact_unknown_and_derived_fact_provenance_exempt(tmp_path: Path) -> None:
    ground_truth_root = tmp_path / "ground_truth"
    fixture_path = _write_fixture(ground_truth_root)
    result = _result_with(
        FactResult(field_id="engine.output", value=100, state=FactState.KNOWN, origin=OriginType.DERIVED),
    )

    score = grade_fixture_result(result, ground_truth_path=fixture_path, ground_truth_root=ground_truth_root)

    assert (score.correct_count, score.known_count, score.error_count, score.unknown_count) == (1, 1, 0, 2)
    assert score.provenance_eligible_correct_known_count == 0
    assert score.provenance_success_rate is None
    assert score.fields[0].notes == ("deterministic_derived_provenance_exempt",)
    assert score.fields[1].comparison_rule == "output_unknown_or_missing"


def test_summary_averages_paired_mini_fixtures_before_family_macro() -> None:
    base = dict(
        grader_version=GRADER_VERSION,
        comparison_rules_sha256=COMPARISON_RULES_SHA256,
        ground_truth_corpus_sha256="corpus",
        system_version="system",
        total_scorable_facts=1,
        correct_count=1,
        known_count=1,
        error_count=0,
        unknown_count=0,
        excluded_not_available_count=0,
        excluded_not_applicable_count=0,
        provenance_bearing_correct_known_count=1,
        provenance_eligible_correct_known_count=1,
        correct_enthusiast_fact_coverage=1.0,
        attempted_fact_accuracy=1.0,
        error_rate=0.0,
        attempted_fact_error_rate=0.0,
        unknown_rate=0.0,
        provenance_success_rate=1.0,
        fields=(),
    )
    mini_true = FixtureScore(fixture_id="02a", vehicle_family_id="02_mini", **base)
    mini_false = FixtureScore.model_validate({**base, "fixture_id": "02b", "vehicle_family_id": "02_mini", "correct_count": 0, "known_count": 0, "unknown_count": 1, "correct_enthusiast_fact_coverage": 0.0, "attempted_fact_accuracy": None, "error_rate": 0.0, "attempted_fact_error_rate": None, "unknown_rate": 1.0, "provenance_bearing_correct_known_count": 0, "provenance_eligible_correct_known_count": 0, "provenance_success_rate": None})
    other = FixtureScore(fixture_id="03", vehicle_family_id="03_other", **base)

    summary = summarize_scores((mini_true, mini_false, other))

    assert summary.scored_vehicle_family_count == 2
    assert summary.headline_family_macro_cefc == pytest.approx(0.75)
    assert summary.family_scores[0].fixture_count == 2
    assert summary.family_scores[0].attempted_fact_accuracy == 1.0
    assert summary.family_scores[0].known_count == 1
    assert summary.family_scores[0].unknown_count == 1


def test_score_artifacts_include_identity_and_explicit_null_semantics(tmp_path: Path) -> None:
    score = FixtureScore(
        grader_version=GRADER_VERSION, comparison_rules_sha256=COMPARISON_RULES_SHA256, ground_truth_corpus_sha256="corpus", system_version="system", fixture_id="fixture", vehicle_family_id="family", total_scorable_facts=1, correct_count=0, known_count=0, error_count=0, unknown_count=1, excluded_not_available_count=0, excluded_not_applicable_count=0, provenance_bearing_correct_known_count=0, provenance_eligible_correct_known_count=0, correct_enthusiast_fact_coverage=0.0, attempted_fact_accuracy=None, error_rate=0.0, attempted_fact_error_rate=None, unknown_rate=1.0, provenance_success_rate=None, fields=(),
    )
    summary = summarize_scores((score,))

    paths = write_score_artifacts(score, summary, tmp_path)

    assert all(path.is_file() for path in paths)
    assert "null` metric values" in paths[2].read_text(encoding="utf-8")
    assert json.loads(paths[0].read_text(encoding="utf-8"))["grader_version"] == GRADER_VERSION
    assert paths[1].parent == tmp_path / "system"


def test_grader_refuses_a_ground_truth_file_that_fails_its_lock(tmp_path: Path) -> None:
    ground_truth_root = tmp_path / "ground_truth"
    fixture_path = _write_fixture(ground_truth_root)
    lock_path = ground_truth_root / "benchmark_lock.json"
    lock_path.write_text(
        json.dumps({"files": {"fixture.json": "0" * 64}}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="benchmark lock mismatch"):
        grade_fixture_result(
            _result_with(),
            ground_truth_path=fixture_path,
            ground_truth_root=ground_truth_root,
        )


def test_grader_uses_required_error_and_unknown_denominators(tmp_path: Path) -> None:
    ground_truth_root = tmp_path / "ground_truth"
    fixture_path = _write_fixture(ground_truth_root)
    result = _result_with(
        FactResult(field_id="engine.output", value=100, state=FactState.KNOWN, provenance=(_provenance(),), origin=OriginType.RESEARCHED),
        FactResult(field_id="drivetrain.locking_differential", value=True, state=FactState.KNOWN, provenance=(_provenance(),), origin=OriginType.RESEARCHED),
    )

    score = grade_fixture_result(result, ground_truth_path=fixture_path, ground_truth_root=ground_truth_root)

    assert (score.correct_count, score.error_count, score.unknown_count) == (1, 1, 1)
    assert score.attempted_fact_accuracy == pytest.approx(1 / 2)
    assert score.error_rate == pytest.approx(1 / 3)
    assert score.unknown_rate == pytest.approx(1 / 3)


def test_grader_refuses_mismatched_result_and_ground_truth_fixture(tmp_path: Path) -> None:
    ground_truth_root = tmp_path / "ground_truth"
    fixture_path = _write_fixture(ground_truth_root)

    with pytest.raises(ValueError, match="does not match result fixture_id"):
        grade_fixture_result(
            _result_with(fixture_id="different_fixture.json"),
            ground_truth_path=fixture_path,
            ground_truth_root=ground_truth_root,
        )


def test_fixture_score_rejects_broken_c_e_u_invariant() -> None:
    with pytest.raises(ValueError, match=r"correct_count \+ error_count \+ unknown_count"):
        FixtureScore(
            grader_version=GRADER_VERSION,
            comparison_rules_sha256=COMPARISON_RULES_SHA256,
            ground_truth_corpus_sha256="corpus",
            system_version="system",
            fixture_id="fixture",
            vehicle_family_id="family",
            total_scorable_facts=3,
            correct_count=1,
            known_count=2,
            error_count=1,
            unknown_count=0,
            excluded_not_available_count=0,
            excluded_not_applicable_count=0,
            provenance_bearing_correct_known_count=0,
            provenance_eligible_correct_known_count=0,
            correct_enthusiast_fact_coverage=1 / 3,
            attempted_fact_accuracy=1 / 2,
            error_rate=1 / 3,
            attempted_fact_error_rate=1 / 2,
            unknown_rate=0.0,
            provenance_success_rate=None,
            fields=(),
        )
