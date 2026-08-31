"""Deterministic grader for the independently frozen Hackathon Core 24 corpus.

This module is evaluation-only. Runtime runners and provider code must never
import it or read the answer-key directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from enthusiast_lens.models import FactState

from .full_web import BaselineResult
from .grader import FixtureScore, ScoredField, summarize_scores, write_score_artifacts


GRADER_VERSION = "deterministic-core-24-grader-v1"
DEFAULT_GROUND_TRUTH_ROOT = Path("evals/ground_truth_core24_v1")
DEFAULT_COMPARISON_RULES_PATH = DEFAULT_GROUND_TRUTH_ROOT / "comparison_rules.json"
DEFAULT_SCORE_ROOT = Path("artifacts/evals/core24_scores")


def _canonical(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _normalized_size(value: str) -> str:
    return "".join(value.casefold().split())


def _rules(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _verify_lock(root: Path) -> str:
    lock_path = root / "benchmark_lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in lock["files"].items():
        path = root / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            mismatches.append(relative)
    if mismatches:
        raise ValueError(f"Core 24 benchmark lock mismatch: {', '.join(sorted(mismatches))}")
    return hashlib.sha256(lock_path.read_bytes()).hexdigest()


def _number_matches(actual: Any, expected: Any, tolerance: float) -> bool:
    if isinstance(actual, bool) or isinstance(expected, bool):
        return False
    try:
        return abs(float(actual) - float(expected)) <= tolerance
    except (TypeError, ValueError):
        return False


def _enum_matches(field_id: str, actual: Any, expected: Any, rules: dict[str, Any]) -> bool:
    if not isinstance(actual, str) or not isinstance(expected, str):
        return actual == expected
    aliases = rules.get("enum_aliases", {}).get(field_id, {}).get(expected, [])
    return _canonical(actual) in {_canonical(expected), *(_canonical(item) for item in aliases)}


def _suspension_component_matches(actual: Any, expected: Any, rules: dict[str, Any]) -> bool:
    if not isinstance(actual, str) or not isinstance(expected, str):
        return False
    aliases = rules["compound_fields"]["suspension_axles_and_chassis.suspension_layout"]["aliases"].get(expected, [])
    return _canonical(actual) in {_canonical(expected), *(_canonical(item) for item in aliases)}


def _compound_matches(field_id: str, actual: Any, expected: Any, rules: dict[str, Any]) -> tuple[bool, str]:
    contract = rules["compound_fields"][field_id]
    required = contract["required_keys"]
    if not isinstance(actual, dict) or set(actual) != set(required):
        return False, "compound object keys do not match frozen shape"
    if not isinstance(expected, dict) or set(expected) != set(required):
        raise ValueError(f"malformed frozen compound answer for {field_id}")
    failures = []
    for key in required:
        left, right = actual[key], expected[key]
        if right is None:
            matched = left is None
        elif field_id == "brakes_wheels_and_tires.rotor_diameters_in":
            matched = _number_matches(left, right, rules["numeric_tolerances"][f"{field_id}.*"]["absolute"])
        elif field_id == "energy_storage.capacity":
            matched = _number_matches(left, right, rules["numeric_tolerances"][f"{field_id}.{key}"]["absolute"])
        elif field_id == "brakes_wheels_and_tires.default_tire" and key in {"front_size", "rear_size"}:
            matched = isinstance(left, str) and _normalized_size(left) == _normalized_size(right)
        elif field_id == "brakes_wheels_and_tires.default_tire":
            matched = isinstance(left, str) and _canonical(left) == _canonical(right)
        elif field_id == "suspension_axles_and_chassis.suspension_layout":
            matched = _suspension_component_matches(left, right, rules)
        else:
            matched = left == right
        if not matched:
            failures.append(key)
    return not failures, "all frozen components match" if not failures else f"component mismatch: {', '.join(failures)}"


def compare_core24_value(field_id: str, actual: Any, expected: Any, rules: dict[str, Any]) -> tuple[bool, str, str]:
    if field_id in rules["compound_fields"]:
        matched, reason = _compound_matches(field_id, actual, expected, rules)
        return matched, "compound_all_components", reason
    tolerance = rules["numeric_tolerances"].get(field_id)
    if tolerance is not None:
        matched = _number_matches(actual, expected, tolerance["absolute"])
        return matched, "numeric_absolute_tolerance", "within frozen tolerance" if matched else "outside frozen tolerance"
    if field_id in rules.get("enum_aliases", {}):
        matched = _enum_matches(field_id, actual, expected, rules)
        return matched, "frozen_enum_alias", "matches frozen enum/alias" if matched else "does not match frozen enum/alias"
    if isinstance(expected, str):
        matched = isinstance(actual, str) and _canonical(actual) == _canonical(expected)
        return matched, "normalized_exact", "matches normalized value" if matched else "does not match normalized value"
    matched = type(actual) is type(expected) and actual == expected
    return matched, "exact", "matches exact value" if matched else "does not match exact value"


def grade_core24_fixture_result(
    result: BaselineResult,
    *,
    ground_truth_path: Path,
    ground_truth_root: Path = DEFAULT_GROUND_TRUTH_ROOT,
    comparison_rules_path: Path | None = None,
) -> FixtureScore:
    if ground_truth_path.name != result.fixture_id:
        raise ValueError("ground-truth fixture name does not match result fixture_id")
    corpus_hash = _verify_lock(ground_truth_root)
    fixture = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    rules, rules_hash = _rules(comparison_rules_path or ground_truth_root / "comparison_rules.json")
    if rules["grader_version"] != GRADER_VERSION:
        raise ValueError("comparison rules target a different grader version")
    observed = {fact.field_id: fact for fact in result.facts}
    fields = []
    excluded_unresolved = 0
    excluded_na = 0
    for expected in fixture["facts"]:
        status = expected["ground_truth_status"]
        if not expected["scorable"]:
            excluded_unresolved += status == "unresolved"
            excluded_na += status == "not_applicable"
            fields.append(ScoredField(field_id=expected["field_id"], outcome="excluded", expected_status=status, comparison_rule=f"excluded_{status}", reason=expected["notes"], notes=("non_scorable_ground_truth",)))
            continue
        actual = observed.get(expected["field_id"])
        known = actual is not None and actual.state is FactState.KNOWN
        matched, comparison_rule, reason = compare_core24_value(expected["field_id"], actual.value if known else None, expected["value"], rules) if known else (False, "output_unknown_or_missing", "output is missing or non-known")
        correct = known and matched
        derived = bool(actual and getattr(actual.origin, "value", actual.origin) == "derived")
        fields.append(ScoredField(
            field_id=expected["field_id"],
            outcome="correct" if correct else "error" if known else "unknown",
            expected_status=status,
            expected_value=expected["value"],
            observed_state=actual.state.value if actual else None,
            observed_value=actual.value if actual else None,
            provenance_present=bool(actual and actual.provenance),
            provenance_required=correct and not derived,
            comparison_rule=comparison_rule,
            reason=reason,
            notes=("deterministic_derived_provenance_exempt",) if correct and derived else (),
        ))
    scored = [field for field in fields if field.outcome != "excluded"]
    c = sum(field.outcome == "correct" for field in scored)
    e = sum(field.outcome == "error" for field in scored)
    u = sum(field.outcome == "unknown" for field in scored)
    k = c + e
    eligible = [field for field in scored if field.provenance_required]
    bearing = sum(field.provenance_present for field in eligible)
    ratio = lambda a, b: a / b if b else None
    return FixtureScore(
        grader_version=GRADER_VERSION,
        comparison_rules_sha256=rules_hash,
        ground_truth_corpus_sha256=corpus_hash,
        system_version=result.system_version,
        fixture_id=result.fixture_id,
        vehicle_family_id=result.vehicle_family_id,
        total_scorable_facts=len(scored),
        correct_count=c,
        known_count=k,
        error_count=e,
        unknown_count=u,
        excluded_not_available_count=excluded_unresolved,
        excluded_not_applicable_count=excluded_na,
        provenance_bearing_correct_known_count=bearing,
        provenance_eligible_correct_known_count=len(eligible),
        correct_enthusiast_fact_coverage=ratio(c, len(scored)),
        attempted_fact_accuracy=ratio(c, k),
        error_rate=ratio(e, len(scored)),
        attempted_fact_error_rate=ratio(e, k),
        unknown_rate=ratio(u, len(scored)),
        provenance_success_rate=ratio(bearing, len(eligible)),
        fields=tuple(fields),
    )


def _main() -> None:
    parser = argparse.ArgumentParser(description="Grade one preserved Core 24 result.")
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--ground-truth-root", type=Path, default=DEFAULT_GROUND_TRUTH_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_SCORE_ROOT)
    args = parser.parse_args()
    result = BaselineResult.model_validate_json(args.result.read_text(encoding="utf-8"))
    score = grade_core24_fixture_result(result, ground_truth_path=args.ground_truth, ground_truth_root=args.ground_truth_root)
    summary = summarize_scores((score,))
    for path in write_score_artifacts(score, summary, args.output_root):
        print(path)


if __name__ == "__main__":
    _main()
