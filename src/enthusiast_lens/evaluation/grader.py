"""Deterministic, answer-key-only benchmark scoring.

This module is the sole runtime-facing component permitted to load
``evals/ground_truth``.  It deliberately has no dependency on the research
agent or provider adapter: a completed canonical result is its input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field

from enthusiast_lens.deterministic import compare_exact, compare_with_range, compare_with_tolerance
from enthusiast_lens.models import FactState

from .full_web import BaselineResult


GRADER_VERSION = "deterministic-benchmark-grader-v1"
DEFAULT_GROUND_TRUTH_ROOT = Path("evals/ground_truth")
DEFAULT_SCORE_ROOT = Path("artifacts/evals/scores")

# This intentionally describes comparison mechanics, not benchmark answers.
COMPARISON_RULES = {
    "missing_or_non_known_output": "unknown",
    "known_output": "correct_when_accepted_value_range_or_normalized_exact_match_else_error",
    "strings": "casefolded_whitespace_normalized_exact; frozen accepted_aliases included",
    "numbers": "frozen accepted_range inclusive, then numeric_tolerance inclusive, else exact",
    "collections": "recursive exact comparison after string normalization",
    "provenance": "correct_known_non_derived facts require one source for provenance success",
    "derived": "correct known deterministic-derived facts count toward coverage but are provenance-exempt",
}
COMPARISON_RULES_SHA256 = hashlib.sha256(
    json.dumps(COMPARISON_RULES, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

Outcome = Literal["correct", "error", "unknown", "excluded"]


class ScoredField(BaseModel):
    """One deterministic ground-truth comparison, including answer-key value."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field_id: str
    outcome: Outcome
    expected_status: str
    expected_value: Any | None = None
    observed_state: str | None = None
    observed_value: Any | None = None
    provenance_present: bool = False
    provenance_required: bool = False
    notes: tuple[str, ...] = Field(default_factory=tuple)


class FixtureScore(BaseModel):
    """Score result for one frozen fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    grader_version: str
    comparison_rules_sha256: str
    ground_truth_corpus_sha256: str
    system_version: str
    fixture_id: str
    vehicle_family_id: str
    total_scorable_facts: int
    correct_count: int
    known_count: int
    error_count: int
    unknown_count: int
    provenance_bearing_correct_known_count: int
    provenance_eligible_correct_known_count: int
    correct_enthusiast_fact_coverage: float | None
    attempted_fact_accuracy: float | None
    attempted_fact_error_rate: float | None
    unknown_rate: float | None
    provenance_success_rate: float | None
    fields: tuple[ScoredField, ...]


class FamilyScore(BaseModel):
    """A family-level mean; MINI can contain two paired fixture scores."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    vehicle_family_id: str
    fixture_ids: tuple[str, ...]
    fixture_count: int
    correct_enthusiast_fact_coverage: float | None
    attempted_fact_accuracy: float | None
    attempted_fact_error_rate: float | None
    unknown_rate: float | None
    provenance_success_rate: float | None


class BenchmarkSummary(BaseModel):
    """Family-macro and fixture-micro score summary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    grader_version: str
    comparison_rules_sha256: str
    ground_truth_corpus_sha256: str
    system_version: str
    scored_fixture_count: int
    scored_vehicle_family_count: int
    family_scores: tuple[FamilyScore, ...]
    headline_family_macro_cefc: float | None
    family_macro_attempted_fact_accuracy: float | None
    family_macro_attempted_fact_error_rate: float | None
    family_macro_unknown_rate: float | None
    family_macro_provenance_success_rate: float | None
    micro_total_scorable_facts: int
    micro_correct_count: int
    micro_known_count: int
    micro_error_count: int
    micro_unknown_count: int
    micro_provenance_bearing_correct_known_count: int
    micro_provenance_eligible_correct_known_count: int
    micro_cefc: float | None
    micro_attempted_fact_accuracy: float | None
    micro_attempted_fact_error_rate: float | None
    micro_unknown_rate: float | None
    micro_provenance_success_rate: float | None


@dataclass(frozen=True)
class _GroundTruthContext:
    fixture: dict[str, Any]
    corpus_sha256: str


def _mean(values: Iterable[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return sum(present) / len(present) if present else None


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _canonical_string(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _deep_exact(actual: Any, expected: Any) -> bool:
    """Compare nested canonical JSON without inventing equivalences."""

    if isinstance(actual, str) and isinstance(expected, str):
        return compare_exact(actual, expected)
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, list):
        return len(actual) == len(expected) and all(
            _deep_exact(left, right) for left, right in zip(actual, expected, strict=True)
        )
    if isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(
            _deep_exact(actual[key], expected[key]) for key in actual
        )
    return compare_exact(actual, expected)


def _matches_expected(actual: Any, expected: dict[str, Any]) -> bool:
    """Apply only the comparison metadata frozen with the ground truth fact."""

    if actual is None:
        return False
    accepted_range = expected.get("accepted_range")
    if accepted_range is not None:
        try:
            return compare_with_range(actual, accepted_range["min"], accepted_range["max"])
        except (TypeError, ValueError):
            return False
    if expected.get("numeric_tolerance") is not None and "value" in expected:
        try:
            return compare_with_tolerance(actual, expected["value"], expected["numeric_tolerance"])
        except (TypeError, ValueError):
            return False

    candidates = list(expected.get("accepted_values") or [])
    if "value" in expected:
        candidates.append(expected["value"])
    normalization = expected.get("normalization") or {}
    if isinstance(actual, str) and all(isinstance(candidate, str) for candidate in candidates):
        candidates.extend(normalization.get("accepted_aliases") or [])
        actual_normalized = _canonical_string(actual)
        return any(actual_normalized == _canonical_string(candidate) for candidate in candidates)
    return any(_deep_exact(actual, candidate) for candidate in candidates)


def _ground_truth_context(path: Path, ground_truth_root: Path) -> _GroundTruthContext:
    resolved = path.resolve()
    root = ground_truth_root.resolve()
    if root not in resolved.parents:
        raise ValueError("ground-truth fixture must be inside the configured ground-truth root")
    try:
        fixture = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"ground-truth fixture could not be loaded: {error}") from error
    lock_path = root / "benchmark_lock.json"
    if not lock_path.is_file():
        raise ValueError("ground-truth benchmark lock is missing")
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        locked_files = lock["files"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError("ground-truth benchmark lock is malformed") from error
    mismatches: list[str] = []
    for relative_path, expected_hash in locked_files.items():
        locked_path = root / relative_path
        if not locked_path.is_file() or hashlib.sha256(locked_path.read_bytes()).hexdigest() != expected_hash:
            mismatches.append(relative_path)
    if mismatches:
        raise ValueError(f"ground-truth benchmark lock mismatch: {', '.join(sorted(mismatches))}")
    return _GroundTruthContext(
        fixture=fixture,
        corpus_sha256=hashlib.sha256(lock_path.read_bytes()).hexdigest(),
    )


def grade_fixture_result(
    result: BaselineResult,
    *,
    ground_truth_path: Path,
    ground_truth_root: Path = DEFAULT_GROUND_TRUTH_ROOT,
) -> FixtureScore:
    """Grade one canonical result against its frozen fixture, locally only."""

    context = _ground_truth_context(ground_truth_path, ground_truth_root)
    expected_facts = context.fixture.get("facts", [])
    observed_by_id = {fact.field_id: fact for fact in result.facts}
    fields: list[ScoredField] = []

    for expected in expected_facts:
        if not expected.get("scorable", False):
            fields.append(
                ScoredField(
                    field_id=expected["field_id"],
                    outcome="excluded",
                    expected_status=expected["status"],
                    expected_value=expected.get("value"),
                    notes=("non_scorable_ground_truth",),
                )
            )
            continue
        observed = observed_by_id.get(expected["field_id"])
        observed_state = observed.state.value if observed is not None else None
        known = observed is not None and observed.state is FactState.KNOWN
        correct = known and _matches_expected(observed.value, expected)
        outcome: Outcome = "correct" if correct else "error" if known else "unknown"
        derived = observed is not None and getattr(observed.origin, "value", observed.origin) == "derived"
        provenance_required = correct and not derived
        fields.append(
            ScoredField(
                field_id=expected["field_id"],
                outcome=outcome,
                expected_status=expected["status"],
                expected_value=expected.get("value"),
                observed_state=observed_state,
                observed_value=observed.value if observed is not None else None,
                provenance_present=bool(observed and observed.provenance),
                provenance_required=provenance_required,
                notes=("deterministic_derived_provenance_exempt",) if correct and derived else (),
            )
        )

    scorable = [field for field in fields if field.outcome != "excluded"]
    correct_count = sum(field.outcome == "correct" for field in scorable)
    error_count = sum(field.outcome == "error" for field in scorable)
    unknown_count = sum(field.outcome == "unknown" for field in scorable)
    known_count = correct_count + error_count
    provenance_eligible = [field for field in scorable if field.provenance_required]
    provenance_bearing = sum(field.provenance_present for field in provenance_eligible)
    return FixtureScore(
        grader_version=GRADER_VERSION,
        comparison_rules_sha256=COMPARISON_RULES_SHA256,
        ground_truth_corpus_sha256=context.corpus_sha256,
        system_version=result.system_version,
        fixture_id=result.fixture_id,
        vehicle_family_id=result.vehicle_family_id,
        total_scorable_facts=len(scorable),
        correct_count=correct_count,
        known_count=known_count,
        error_count=error_count,
        unknown_count=unknown_count,
        provenance_bearing_correct_known_count=provenance_bearing,
        provenance_eligible_correct_known_count=len(provenance_eligible),
        correct_enthusiast_fact_coverage=_ratio(correct_count, len(scorable)),
        attempted_fact_accuracy=_ratio(correct_count, known_count),
        attempted_fact_error_rate=_ratio(error_count, known_count),
        unknown_rate=_ratio(unknown_count, len(scorable)),
        provenance_success_rate=_ratio(provenance_bearing, len(provenance_eligible)),
        fields=tuple(fields),
    )


def summarize_scores(scores: Iterable[FixtureScore]) -> BenchmarkSummary:
    """Aggregate fixture scores, averaging paired MINI fixtures within family."""

    items = tuple(scores)
    if not items:
        raise ValueError("at least one fixture score is required")
    identities = {(item.grader_version, item.comparison_rules_sha256, item.ground_truth_corpus_sha256, item.system_version) for item in items}
    if len(identities) != 1:
        raise ValueError("scores must share grader, corpus, comparison rules, and system identity")
    grouped: dict[str, list[FixtureScore]] = defaultdict(list)
    for item in items:
        grouped[item.vehicle_family_id].append(item)
    family_scores = tuple(
        FamilyScore(
            vehicle_family_id=family_id,
            fixture_ids=tuple(item.fixture_id for item in family_items),
            fixture_count=len(family_items),
            correct_enthusiast_fact_coverage=_mean(item.correct_enthusiast_fact_coverage for item in family_items),
            attempted_fact_accuracy=_mean(item.attempted_fact_accuracy for item in family_items),
            attempted_fact_error_rate=_mean(item.attempted_fact_error_rate for item in family_items),
            unknown_rate=_mean(item.unknown_rate for item in family_items),
            provenance_success_rate=_mean(item.provenance_success_rate for item in family_items),
        )
        for family_id, family_items in sorted(grouped.items())
    )
    version, rules_hash, corpus_hash, system_version = identities.pop()
    total = sum(item.total_scorable_facts for item in items)
    correct = sum(item.correct_count for item in items)
    known = sum(item.known_count for item in items)
    errors = sum(item.error_count for item in items)
    unknown = sum(item.unknown_count for item in items)
    provenance = sum(item.provenance_bearing_correct_known_count for item in items)
    provenance_eligible = sum(item.provenance_eligible_correct_known_count for item in items)
    return BenchmarkSummary(
        grader_version=version,
        comparison_rules_sha256=rules_hash,
        ground_truth_corpus_sha256=corpus_hash,
        system_version=system_version,
        scored_fixture_count=len(items),
        scored_vehicle_family_count=len(family_scores),
        family_scores=family_scores,
        headline_family_macro_cefc=_mean(item.correct_enthusiast_fact_coverage for item in family_scores),
        family_macro_attempted_fact_accuracy=_mean(item.attempted_fact_accuracy for item in family_scores),
        family_macro_attempted_fact_error_rate=_mean(item.attempted_fact_error_rate for item in family_scores),
        family_macro_unknown_rate=_mean(item.unknown_rate for item in family_scores),
        family_macro_provenance_success_rate=_mean(item.provenance_success_rate for item in family_scores),
        micro_total_scorable_facts=total,
        micro_correct_count=correct,
        micro_known_count=known,
        micro_error_count=errors,
        micro_unknown_count=unknown,
        micro_provenance_bearing_correct_known_count=provenance,
        micro_provenance_eligible_correct_known_count=provenance_eligible,
        micro_cefc=_ratio(correct, total),
        micro_attempted_fact_accuracy=_ratio(correct, known),
        micro_attempted_fact_error_rate=_ratio(errors, known),
        micro_unknown_rate=_ratio(unknown, total),
        micro_provenance_success_rate=_ratio(provenance, provenance_eligible),
    )


def write_score_artifacts(score: FixtureScore, summary: BenchmarkSummary, output_root: Path) -> tuple[Path, Path, Path]:
    """Write deterministic JSON and concise Markdown artifacts for review."""

    destination = output_root / score.system_version / score.fixture_id
    destination.mkdir(parents=True, exist_ok=True)
    score_path = destination / "score.json"
    summary_json_path = destination / "benchmark_summary.json"
    summary_markdown_path = destination / "benchmark_summary.md"
    score_path.write_text(score.model_dump_json(indent=2) + "\n", encoding="utf-8")
    summary_json_path.write_text(summary.model_dump_json(indent=2) + "\n", encoding="utf-8")
    summary_markdown_path.write_text(
        "\n".join(
            (
                "# Deterministic Benchmark Score Summary",
                "",
                f"- Grader: `{summary.grader_version}`",
                f"- Ground-truth corpus SHA-256: `{summary.ground_truth_corpus_sha256}`",
                f"- Comparison rules SHA-256: `{summary.comparison_rules_sha256}`",
                f"- System: `{summary.system_version}`",
                f"- Scored fixtures / families: {summary.scored_fixture_count} / {summary.scored_vehicle_family_count}",
                f"- Headline family-macro CEFC: {summary.headline_family_macro_cefc!r}",
                f"- Micro CEFC: {summary.micro_cefc!r}",
                f"- Micro C / K / E / U: {summary.micro_correct_count} / {summary.micro_known_count} / {summary.micro_error_count} / {summary.micro_unknown_count}",
                f"- Provenance-bearing correct known facts: {summary.micro_provenance_bearing_correct_known_count} / {summary.micro_provenance_eligible_correct_known_count} ({summary.micro_provenance_success_rate!r})",
                "",
                "`null` metric values mean their denominator was zero; they are not converted to zero.",
                "",
            )
        ),
        encoding="utf-8",
    )
    return score_path, summary_json_path, summary_markdown_path


def _main() -> None:
    parser = argparse.ArgumentParser(description="Deterministically grade one completed benchmark result.")
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--ground-truth-root", type=Path, default=DEFAULT_GROUND_TRUTH_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_SCORE_ROOT)
    args = parser.parse_args()
    result = BaselineResult.model_validate_json(args.result.read_text(encoding="utf-8"))
    score = grade_fixture_result(result, ground_truth_path=args.ground_truth, ground_truth_root=args.ground_truth_root)
    summary = summarize_scores((score,))
    for path in write_score_artifacts(score, summary, args.output_root):
        print(path)


if __name__ == "__main__":
    _main()
