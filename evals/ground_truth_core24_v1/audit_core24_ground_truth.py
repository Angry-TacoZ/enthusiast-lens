"""Audit and lock the independent Hackathon Core 24 answer-key corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
CATALOG_PATH = REPO / "evals" / "task_definition" / "hackathon_core_24_v1_field_catalog.json"
INPUTS_PATH = REPO / "evals" / "inputs" / "benchmark_inputs.json"
REPORT_PATH = REPO / "artifacts" / "audits" / "core24_ground_truth_audit.json"
LOCKED_SUPPORT_FILES = ("SCORING_POLICY.md", "audit_core24_ground_truth.py", "comparison_rules.json", "ground_truth.schema.json", "manifest.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_files() -> list[Path]:
    return sorted(ROOT.glob("*_ground_truth.json")) + [ROOT / name for name in LOCKED_SUPPORT_FILES]


def write_lock() -> None:
    payload = {
        "benchmark_version": "hackathon-core-24-ground-truth-v1",
        "hash_algorithm": "sha256",
        "file_count": len(lock_files()),
        "files": {path.relative_to(ROOT).as_posix(): sha(path) for path in lock_files()},
    }
    (ROOT / "benchmark_lock.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def verify_lock() -> tuple[int, list[str]]:
    lock = json.loads((ROOT / "benchmark_lock.json").read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in lock["files"].items():
        path = ROOT / relative
        if not path.is_file() or sha(path) != expected:
            mismatches.append(relative)
    return len(lock["files"]), mismatches


def audit() -> dict:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog_ids = [item["field_id"] for item in catalog["fields"]]
    schema = json.loads((ROOT / "ground_truth.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    runtime_inputs = json.loads(INPUTS_PATH.read_text(encoding="utf-8"))["inputs"]
    runtime_by_fixture = {item["fixture_id"]: item for item in runtime_inputs}
    identity_matches = 0
    fixtures = []
    errors = []
    source_types = Counter()
    publishers = Counter()
    car_and_driver = {field: 0 for field in ("engine_and_measured_performance.zero_to_60_mph", "engine_and_measured_performance.skidpad_g", "brakes_wheels_and_tires.braking_70_to_0_mph_ft")}
    for path in sorted(ROOT.glob("*_ground_truth.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        schema_errors = sorted(validator.iter_errors(data), key=lambda item: list(item.path))
        errors.extend(f"{path.name}: schema: {item.message}" for item in schema_errors)
        if data["fixture_id"] != path.name:
            errors.append(f"{path.name}: fixture_id mismatch")
        runtime = runtime_by_fixture.get(path.name)
        identity_fields = ("year", "make", "model", "trim", "body_style", "transmission", "drivetrain", "market", "vin")
        if runtime is None or runtime["vehicle_family_id"] != data["vehicle_family_id"] or any(
            runtime["vehicle"].get(field) != data["vehicle"].get(field) for field in identity_fields
        ):
            errors.append(f"{path.name}: answer-key vehicle identity differs from runtime input")
        else:
            identity_matches += 1
        ids = [fact["field_id"] for fact in data["facts"]]
        if ids != catalog_ids:
            errors.append(f"{path.name}: field IDs/order differ from task catalog")
        if len(ids) != len(set(ids)):
            errors.append(f"{path.name}: duplicate field IDs")
        counts = Counter(fact["ground_truth_status"] for fact in data["facts"])
        provenance = 0
        for fact in data["facts"]:
            status = fact["ground_truth_status"]
            expected_scorable = status == "known" and fact["applicability"] == "applicable"
            if fact["scorable"] != expected_scorable:
                errors.append(f"{path.name}: {fact['field_id']}: status/scorable mismatch")
            if status == "known":
                if fact["value"] is None or not fact["sources"]:
                    errors.append(f"{path.name}: {fact['field_id']}: known fact lacks value/provenance")
                else:
                    provenance += 1
                for item in fact["sources"]:
                    if item["vpic_role"] != "none" or "vpic" in item["url"].casefold():
                        errors.append(f"{path.name}: {fact['field_id']}: vPIC cannot be answer-key provenance")
                    source_types[item["source_type"]] += 1
                    publishers[item["publisher"]] += 1
                    if fact["field_id"] in car_and_driver and item["publisher"] == "Car and Driver":
                        car_and_driver[fact["field_id"]] += 1
                    evidence_path = item.get("evidence_path")
                    if evidence_path and not (REPO / evidence_path).is_file():
                        errors.append(f"{path.name}: {fact['field_id']}: local evidence path is missing: {evidence_path}")
            elif fact["value"] is not None or fact["sources"]:
                errors.append(f"{path.name}: {fact['field_id']}: excluded fact contains answer/provenance")
            if status == "not_applicable" and fact["applicability"] != "not_applicable":
                errors.append(f"{path.name}: {fact['field_id']}: N/A applicability mismatch")
            if status == "unresolved" and fact["applicability"] != "applicable":
                errors.append(f"{path.name}: {fact['field_id']}: unresolved must remain applicable")
        fixtures.append({
            "fixture_id": path.name,
            "vehicle_family_id": data["vehicle_family_id"],
            "canonical_fields": len(data["facts"]),
            "applicable_count": counts["known"] + counts["unresolved"],
            "not_applicable_count": counts["not_applicable"],
            "known_ground_truth_count": counts["known"],
            "unresolved_count": counts["unresolved"],
            "facts_with_provenance": provenance,
            "facts_lacking_required_provenance": counts["known"] - provenance,
            "configuration_match_status": data["fixture_metadata"]["configuration_match_status"],
        })
    manifest_files = [item["file"] for item in manifest["fixtures"]]
    fixture_files = [item["fixture_id"] for item in fixtures]
    if manifest_files != fixture_files:
        errors.append("manifest fixture list/order mismatch")
    if len(fixtures) != 12 or len({item["vehicle_family_id"] for item in fixtures}) != 11:
        errors.append("corpus must contain 12 fixtures and 11 families")
    lock_count, lock_mismatches = verify_lock()
    errors.extend(f"lock mismatch: {item}" for item in lock_mismatches)
    known = sum(item["known_ground_truth_count"] for item in fixtures)
    unresolved = sum(item["unresolved_count"] for item in fixtures)
    not_applicable = sum(item["not_applicable_count"] for item in fixtures)
    report = {
        "audit_version": "hackathon-core-24-ground-truth-audit-v1",
        "status": "passed" if not errors else "failed",
        "benchmark_version": manifest["benchmark_version"],
        "task_catalog_version": catalog["catalog_version"],
        "task_catalog_sha256": sha(CATALOG_PATH),
        "comparison_rules_version": json.loads((ROOT / "comparison_rules.json").read_text(encoding="utf-8"))["comparison_rules_version"],
        "comparison_rules_sha256": sha(ROOT / "comparison_rules.json"),
        "benchmark_lock_sha256": sha(ROOT / "benchmark_lock.json"),
        "locked_files_verified": lock_count - len(lock_mismatches),
        "locked_files_total": lock_count,
        "fixture_count": len(fixtures),
        "vehicle_family_count": len({item["vehicle_family_id"] for item in fixtures}),
        "runtime_input_identity_matches": identity_matches,
        "runtime_input_identity_total": len(fixtures),
        "total_canonical_facts": len(fixtures) * len(catalog_ids),
        "total_applicable_facts": known + unresolved,
        "total_applicable_scorable_facts": known,
        "not_applicable_count": not_applicable,
        "unresolved_count": unresolved,
        "provenance_coverage": {"facts_with_required_provenance": known, "scorable_facts": known, "rate": 1.0 if known else None},
        "source_citation_breakdown_by_type": dict(sorted(source_types.items())),
        "source_citation_breakdown_by_publisher": dict(sorted(publishers.items())),
        "car_and_driver_instrumented_fact_coverage": car_and_driver,
        "fixtures": fixtures,
        "errors": errors,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-lock", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    if args.write_lock:
        write_lock()
    report = audit()
    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
