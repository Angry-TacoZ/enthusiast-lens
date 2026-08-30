"""Audit the V1 task catalog against frozen scoring metadata without reading values.

This evaluation-only tool deliberately extracts only ``field_id``, ``category``,
``label``, and ``scorable`` from frozen fixtures.  It never accesses expected
values, units, evidence, confidence, notes, or configuration answers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DERIVED_FIELD_IDS = {
    "engine_and_measured_performance.power_to_weight_hp_per_us_ton": (
        "Deterministically calculated from canonical horsepower and curb_weight."
    ),
}

# These are structural naming reconciliations only.  They contain no values.
OBVIOUS_SEMANTIC_RENAMES = {
    "engine_and_measured_performance.engine_displacement": "engine_and_measured_performance.displacement_cc",
    "audio.audio_brand": "audio.system_brand",
    "audio.system_wattage": "audio.amplifier_power_w",
    "brakes_wheels_tires.front_brake_type": "brakes_wheels_and_tires.front_brake_type",
    "brakes_wheels_tires.rear_brake_type": "brakes_wheels_and_tires.rear_brake_type",
    "brakes_wheels_tires.front_rotor_size": "brakes_wheels_and_tires.front_rotor_diameter_in",
    "brakes_wheels_tires.rear_rotor_size": "brakes_wheels_and_tires.rear_rotor_diameter_in",
    "brakes_wheels_tires.wheel_size": "brakes_wheels_and_tires.wheel_size",
    "brakes_wheels_tires.tire_size": "brakes_wheels_and_tires.tire_size",
    "brakes_wheels_tires.tire_category": "brakes_wheels_and_tires.tire_type",
    "drivetrain_and_differentials.drive_layout": "drivetrain_and_differentials.layout",
    "suspension_axles_chassis.front_suspension_architecture": "suspension_axles_and_chassis.front_suspension",
    "suspension_axles_chassis.rear_suspension_architecture": "suspension_axles_and_chassis.rear_suspension",
    "suspension_axles_chassis.front_axle_type": "suspension_axles_and_chassis.front_axle_type",
    "suspension_axles_chassis.rear_axle_type": "suspension_axles_and_chassis.rear_axle_type",
    "driver_assistance.adaptive_cruise_control": "driver_assistance_and_highway_automation.adaptive_cruise_control",
    "driver_assistance.acc_min_activation_speed": "driver_assistance_and_highway_automation.acc_min_operating_speed_mph",
    "driver_assistance.active_lane_keep_assist": "driver_assistance_and_highway_automation.lane_keeping_assist",
    "driver_assistance.lane_centering": "driver_assistance_and_highway_automation.lane_centering",
    "driver_assistance.lane_departure_warning": "driver_assistance_and_highway_automation.lane_departure_warning",
    "transmission.manual_shift_mode": "transmission.manual_mode",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _catalog_metadata(catalog_path: Path) -> tuple[dict[str, str], dict[str, Any]]:
    catalog = _read_json(catalog_path)
    fields = {field["field_id"]: field["category"] for field in catalog["fields"]}
    return fields, catalog


def _frozen_scorable_metadata(fixtures_root: Path) -> dict[str, dict[str, set[str]]]:
    metadata: dict[str, dict[str, set[str]]] = {}
    for path in sorted(fixtures_root.glob("*_ground_truth.json")):
        fixture = _read_json(path)
        for fact in fixture["facts"]:
            # Do not access fact keys other than this structural metadata.
            if not fact["scorable"]:
                continue
            record = metadata.setdefault(
                fact["field_id"],
                {"categories": set(), "labels": set(), "fixtures": set()},
            )
            record["categories"].add(fact["category"])
            record["labels"].add(fact["label"])
            record["fixtures"].add(path.name)
    return metadata


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_audit(catalog_path: Path, fixtures_root: Path) -> dict[str, Any]:
    catalog_fields, catalog = _catalog_metadata(catalog_path)
    frozen = _frozen_scorable_metadata(fixtures_root)
    catalog_ids = set(catalog_fields)
    frozen_ids = set(frozen)
    intersection = sorted(catalog_ids & frozen_ids)
    category_mismatches = [
        {
            "field_id": field_id,
            "catalog_category": catalog_fields[field_id],
            "frozen_categories": sorted(frozen[field_id]["categories"]),
        }
        for field_id in intersection
        if catalog_fields[field_id] not in frozen[field_id]["categories"]
    ]
    renames = [
        {"catalog_field_id": old, "canonical_frozen_field_id": new}
        for old, new in OBVIOUS_SEMANTIC_RENAMES.items()
        if old in catalog_ids and new in frozen_ids
    ]
    return {
        "schema_version": "1.0",
        "purpose": (
            "Metadata-only V1 field-ID alignment audit. Expected values, units, source evidence, "
            "confidence, notes, and configuration answers are neither extracted nor recorded."
        ),
        "catalog": {
            "catalog_version": catalog["catalog_version"],
            "sha256": _sha256(catalog_path),
            "field_count": len(catalog_ids),
        },
        "frozen_scoring_contract": {
            "fixture_count": len(list(fixtures_root.glob("*_ground_truth.json"))),
            "scorable_field_id_count": len(frozen_ids),
            "fields": [
                {
                    "field_id": field_id,
                    "categories": sorted(metadata["categories"]),
                    "labels": sorted(metadata["labels"]),
                    "fixture_count": len(metadata["fixtures"]),
                }
                for field_id, metadata in sorted(frozen.items())
            ],
        },
        "intersection": intersection,
        "intersection_count": len(intersection),
        "frozen_scorable_missing_from_catalog": [
            {
                "field_id": field_id,
                "categories": sorted(frozen[field_id]["categories"]),
                "labels": sorted(frozen[field_id]["labels"]),
            }
            for field_id in sorted(frozen_ids - catalog_ids)
        ],
        "catalog_fields_absent_from_frozen_scoring": [
            {"field_id": field_id, "category": catalog_fields[field_id]}
            for field_id in sorted(catalog_ids - frozen_ids)
        ],
        "category_mismatches": category_mismatches,
        "duplicate_or_alias_concerns": {
            "frozen_field_ids_with_multiple_categories": [
                {"field_id": field_id, "categories": sorted(metadata["categories"])}
                for field_id, metadata in sorted(frozen.items())
                if len(metadata["categories"]) > 1
            ],
            "obvious_semantic_renames": renames,
        },
        "canonical_acquisition_classification": [
            {
                "field_id": field_id,
                "classification": "deterministic_derived"
                if field_id in DERIVED_FIELD_IDS
                else "agent_researched",
                "reason": DERIVED_FIELD_IDS.get(field_id),
            }
            for field_id in sorted(frozen_ids)
        ],
    }


def build_reconciled_catalog(fixtures_root: Path, catalog_version: str) -> dict[str, Any]:
    frozen = _frozen_scorable_metadata(fixtures_root)
    return {
        "catalog_version": catalog_version,
        "provenance": (
            "Pre-execution structural reconciliation of the human-readable V1 Schema and "
            "Evaluation Specification with the frozen scoring contract. This task definition "
            "contains only field identifiers, categories, labels-derived descriptions, and "
            "acquisition classification; it contains no expected values."
        ),
        "fields": [
            {
                "field_id": field_id,
                "category": sorted(metadata["categories"])[0],
                "description": f"Canonical V1 scorable field: {sorted(metadata['labels'])[0]}.",
                "acquisition": "deterministic_derived"
                if field_id in DERIVED_FIELD_IDS
                else "agent_researched",
            }
            for field_id, metadata in sorted(frozen.items())
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("evals/task_definition/v1_objective_field_catalog.json"))
    parser.add_argument("--fixtures-root", type=Path, default=Path("evals/ground_truth"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--write-reconciled-catalog", type=Path)
    parser.add_argument("--catalog-version", default="v1-objective-fields-2026-08-30-structural-alignment")
    args = parser.parse_args()
    audit = build_audit(args.catalog, args.fixtures_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    if args.write_reconciled_catalog is not None:
        reconciled = build_reconciled_catalog(args.fixtures_root, args.catalog_version)
        args.write_reconciled_catalog.write_text(json.dumps(reconciled, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "catalog_field_count": audit["catalog"]["field_count"],
        "scorable_field_id_count": audit["frozen_scoring_contract"]["scorable_field_id_count"],
        "intersection_count": audit["intersection_count"],
        "frozen_missing_from_catalog_count": len(audit["frozen_scorable_missing_from_catalog"]),
        "catalog_absent_from_frozen_count": len(audit["catalog_fields_absent_from_frozen_scoring"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
