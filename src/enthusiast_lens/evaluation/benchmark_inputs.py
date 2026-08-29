"""Load and validate the frozen, answer-key-free benchmark input corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from enthusiast_lens.models.benchmark_input import BenchmarkInputCorpus


DISALLOWED_ANSWER_KEY_FIELDS = frozenset(
    {
        "accepted_range",
        "answer_key",
        "expected",
        "expected_value",
        "facts",
        "grader",
        "ground_truth",
        "provenance",
        "scorable",
        "tolerance",
    }
)
ALLOWED_EVIDENCE_RECORD_FIELDS = frozenset(
    {
        "advertised_identity",
        "fixture_id",
        "input_note",
        "publisher",
        "record_id",
        "source_identifier",
        "source_type",
        "source_url",
    }
)
ALLOWED_ADVERTISED_IDENTITY_FIELDS = frozenset(
    {
        "advertised_packages",
        "body_style",
        "drivetrain",
        "make",
        "model",
        "transmission",
        "trim",
        "vin",
        "year",
    }
)


class BenchmarkInputValidationError(ValueError):
    """The runtime-input corpus violates its deterministic boundary."""


def _reject_answer_key_fields(value: Any, location: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = key.casefold()
            if (
                normalized_key in DISALLOWED_ANSWER_KEY_FIELDS
                or normalized_key.startswith("expected_")
                or normalized_key.endswith("_facts")
            ):
                raise BenchmarkInputValidationError(
                    f"answer-key field {key!r} is forbidden at {location}"
                )
            _reject_answer_key_fields(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_answer_key_fields(child, f"{location}[{index}]")


def load_and_validate_benchmark_inputs(
    corpus_path: Path,
    manifest_path: Path,
) -> BenchmarkInputCorpus:
    """Validate schema, fixture mapping, evidence paths, and leakage guards."""

    try:
        raw_corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BenchmarkInputValidationError(str(error)) from error

    _reject_answer_key_fields(raw_corpus)
    try:
        corpus = BenchmarkInputCorpus.model_validate(raw_corpus)
    except ValidationError as error:
        raise BenchmarkInputValidationError(str(error)) from error

    manifest_fixtures = manifest.get("fixtures")
    if not isinstance(manifest_fixtures, list):
        raise BenchmarkInputValidationError("manifest fixtures must be a list")
    expected_mapping = {
        item.get("file"): item.get("vehicle_family_id")
        for item in manifest_fixtures
        if isinstance(item, dict)
    }
    actual_mapping = {item.fixture_id: item.vehicle_family_id for item in corpus.inputs}
    if actual_mapping != expected_mapping:
        missing = sorted(set(expected_mapping) - set(actual_mapping))
        extra = sorted(set(actual_mapping) - set(expected_mapping))
        mismatched = sorted(
            fixture_id
            for fixture_id in set(expected_mapping) & set(actual_mapping)
            if expected_mapping[fixture_id] != actual_mapping[fixture_id]
        )
        raise BenchmarkInputValidationError(
            f"fixture mapping mismatch: missing={missing}, extra={extra}, "
            f"family_mismatches={mismatched}"
        )

    repo_root = corpus_path.resolve().parents[2]
    evidence_documents: dict[Path, dict[str, tuple[str, dict[str, Any]]]] = {}
    for item in corpus.inputs:
        for source in item.source_evidence:
            evidence_path = (repo_root / source.evidence_path).resolve()
            if not evidence_path.is_relative_to(repo_root):
                raise BenchmarkInputValidationError("evidence path escapes repository root")
            if not evidence_path.is_file():
                raise BenchmarkInputValidationError(
                    f"missing evidence snapshot: {source.evidence_path}"
                )
            if evidence_path not in evidence_documents:
                try:
                    evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as error:
                    raise BenchmarkInputValidationError(str(error)) from error
                _reject_answer_key_fields(evidence_payload)
                records = evidence_payload.get("records")
                if not isinstance(records, list):
                    raise BenchmarkInputValidationError("evidence records must be a list")
                indexed_records: dict[str, tuple[str, dict[str, Any]]] = {}
                for record in records:
                    if not isinstance(record, dict):
                        raise BenchmarkInputValidationError("evidence record must be an object")
                    record_id = record.get("record_id")
                    fixture_id = record.get("fixture_id")
                    extra_record_fields = set(record) - ALLOWED_EVIDENCE_RECORD_FIELDS
                    if extra_record_fields:
                        raise BenchmarkInputValidationError(
                            f"unsupported evidence fields: {sorted(extra_record_fields)}"
                        )
                    advertised_identity = record.get("advertised_identity")
                    if not isinstance(advertised_identity, dict):
                        raise BenchmarkInputValidationError(
                            "evidence record requires advertised_identity"
                        )
                    extra_identity_fields = (
                        set(advertised_identity) - ALLOWED_ADVERTISED_IDENTITY_FIELDS
                    )
                    if extra_identity_fields:
                        raise BenchmarkInputValidationError(
                            "unsupported advertised identity fields: "
                            f"{sorted(extra_identity_fields)}"
                        )
                    if not isinstance(record_id, str) or not isinstance(fixture_id, str):
                        raise BenchmarkInputValidationError(
                            "evidence record requires string record_id and fixture_id"
                        )
                    if record_id in indexed_records:
                        raise BenchmarkInputValidationError(
                            f"duplicate evidence record ID: {record_id}"
                        )
                    indexed_records[record_id] = (fixture_id, record)
                evidence_documents[evidence_path] = indexed_records
            evidence_record = evidence_documents[evidence_path].get(source.evidence_record_id)
            if evidence_record is None:
                raise BenchmarkInputValidationError(
                    f"missing evidence record: {source.evidence_record_id}"
                )
            if evidence_record[0] != item.fixture_id:
                raise BenchmarkInputValidationError(
                    f"evidence record {source.evidence_record_id} maps to the wrong fixture"
                )
            record_payload = evidence_record[1]
            if record_payload.get("source_url") != str(source.source_url):
                raise BenchmarkInputValidationError(
                    f"source URL mismatch for evidence record {source.evidence_record_id}"
                )
            if record_payload.get("publisher") != source.publisher:
                raise BenchmarkInputValidationError(
                    f"publisher mismatch for evidence record {source.evidence_record_id}"
                )
    return corpus


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    corpus = load_and_validate_benchmark_inputs(args.corpus, args.manifest)
    ready = sum(item.runtime_ready for item in corpus.inputs)
    families = len({item.vehicle_family_id for item in corpus.inputs})
    print(
        f"benchmark inputs valid: fixtures={len(corpus.inputs)}, "
        f"families={families}, runtime_ready={ready}, unresolved={len(corpus.inputs) - ready}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
