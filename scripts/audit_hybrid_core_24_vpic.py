#!/usr/bin/env python3
"""Run a vPIC-only Core 24 coverage audit; never imports or calls Gemini."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path

from enthusiast_lens.adapters import VPICClient
from enthusiast_lens.evaluation.field_catalog import DEFAULT_FIELD_CATALOG_PATH, load_field_catalog
from enthusiast_lens.evaluation.full_web import DEFAULT_INPUTS_PATH, _load_inputs_only
from enthusiast_lens.evaluation.hybrid import _research_context, _seeds


CONTEXT_TO_CORE = {
    "AdaptiveCruiseControl": "driver_assistance_and_highway_automation.adaptive_cruise_control",
    "LaneCenteringAssistance": "driver_assistance_and_highway_automation.active_lane_centering",
    "Turbo": "engine_and_measured_performance.aspiration",
    "TransmissionStyle": "transmission.type",
    "BatteryEnergyFrom": "energy_storage.capacity",
    "BatteryEnergyTo": "energy_storage.capacity",
    "BatteryEnergyUnits": "energy_storage.capacity",
}


def audit(inputs_path: Path, output_path: Path) -> dict[str, object]:
    corpus = _load_inputs_only(inputs_path)
    catalog = load_field_catalog(DEFAULT_FIELD_CATALOG_PATH)
    client = VPICClient()
    rows: list[dict[str, object]] = []
    for item in corpus.inputs:
        if not item.vehicle.vin:
            rows.append({"fixture_id": item.fixture_id, "status": "missing_vin"})
            continue
        seed = client.decode_vin(item.vehicle.vin, item.vehicle.year)
        complete = _seeds(seed)
        context = _research_context(seed)
        nonblank = sorted({fact.provider_field for fact in seed.facts if fact.provider_value is not None} | {fact.provider_field for fact in context})
        complete_ids = sorted(fact.field_id for fact in complete)
        partial = sorted({CONTEXT_TO_CORE[fact.provider_field] for fact in context if fact.provider_field in CONTEXT_TO_CORE and CONTEXT_TO_CORE[fact.provider_field] not in complete_ids})
        context_only = sorted({fact.provider_field for fact in context if fact.provider_field not in CONTEXT_TO_CORE})
        rows.append({
            "fixture_id": item.fixture_id,
            "vehicle_family_id": item.vehicle_family_id,
            "vehicle": item.vehicle.model_dump(mode="json"),
            "vin": item.vehicle.vin,
            "status": "decoded",
            "vpic_source_url": str(seed.source_url),
            "identity": seed.identity.model_dump(mode="json"),
            "nonblank_provider_fields": nonblank,
            "complete_canonical_seeds": [fact.model_dump(mode="json") for fact in complete],
            "partial_canonical_contributions": partial,
            "research_context_only_fields": context_only,
            "research_context": [fact.model_dump(mode="json") for fact in context],
            "core_fields_with_any_vpic_contribution": sorted(set(complete_ids) | set(partial)),
            "core_fields_still_requiring_web": sorted(set(catalog.agent_research_field_ids) - set(complete_ids)),
        })
    decoded = [row for row in rows if row.get("status") == "decoded"]
    complete_counts = [len(row["complete_canonical_seeds"]) for row in decoded]
    partial_counts = [len(row["partial_canonical_contributions"]) for row in decoded]
    coverage_counts = [len(row["core_fields_with_any_vpic_contribution"]) for row in decoded]
    provider_counts = Counter(field for row in decoded for field in row["nonblank_provider_fields"])
    report = {
        "audit_version": "hybrid-core-24-vpic-only-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "gemini_called": False,
        "catalog_version": catalog.catalog_version,
        "fixture_count": len(rows),
        "decoded_fixture_count": len(decoded),
        "results": rows,
        "aggregate": {
            "average_core_fields_with_any_vpic_contribution": round(sum(coverage_counts) / len(coverage_counts), 3) if coverage_counts else 0,
            "min_core_fields_with_any_vpic_contribution": min(coverage_counts) if coverage_counts else 0,
            "max_core_fields_with_any_vpic_contribution": max(coverage_counts) if coverage_counts else 0,
            "average_complete_canonical_seeds": round(sum(complete_counts) / len(complete_counts), 3) if complete_counts else 0,
            "average_partial_canonical_contributions": round(sum(partial_counts) / len(partial_counts), 3) if partial_counts else 0,
            "most_common_nonblank_provider_fields": provider_counts.most_common(),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS_PATH)
    parser.add_argument("--output", type=Path, default=Path("artifacts/audits/hybrid_core_24_vpic_audit.json"))
    args = parser.parse_args()
    report = audit(args.inputs, args.output)
    print(json.dumps(report["aggregate"], indent=2))
    print(f"fixtures={report['fixture_count']} decoded={report['decoded_fixture_count']} gemini_called={report['gemini_called']}")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
