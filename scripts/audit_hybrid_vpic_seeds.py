"""Run a vPIC-only Hybrid seed audit using only frozen runtime inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from enthusiast_lens.adapters import VPICClient
from enthusiast_lens.evaluation.benchmark_inputs import load_and_validate_benchmark_inputs
from enthusiast_lens.evaluation.field_catalog import DEFAULT_FIELD_CATALOG_PATH, load_field_catalog
from enthusiast_lens.evaluation.hybrid import VPIC_SEED_MAPPINGS, _seeds
from enthusiast_lens.research.agent import PHASE_A_MAX_FIELDS_PER_BATCH, PHASE_B_MAX_FIELDS_PER_BATCH


DEFAULT_INPUTS_PATH = Path("evals/inputs/benchmark_inputs.json")
DEFAULT_MANIFEST_PATH = Path("evals/ground_truth/manifest.json")

EXCLUSION_REASONS = {
    "TransmissionStyle": "broad style does not establish exact mechanism or control type",
    "Turbo": "equipment/aspiration field intentionally remains Web-researched",
    "AdaptiveCruiseControl": "equipment availability is not exact equipped-hardware evidence",
    "LaneDepartureWarning": "equipment availability is not exact equipped-hardware evidence",
    "LaneKeepSystem": "equipment availability is not exact equipped-hardware evidence",
    "BrakeSystemType": "broad brake-system type is not a canonical exact hardware match",
    "Axles": "axle count is intentionally excluded from V2 structured seeding",
}


def _batch_count(field_count: int, maximum_per_batch: int) -> int:
    return (field_count + maximum_per_batch - 1) // maximum_per_batch


def _rejected_nonblank_fields(seed: Any, seeded_provider_fields: set[str]) -> list[dict[str, str]]:
    relevant_mapping_fields = {
        field for mapping in VPIC_SEED_MAPPINGS for field in mapping.provider_fields
    }
    rejected: list[dict[str, str]] = []
    for fact in seed.facts:
        if fact.provider_value is None or fact.provider_field in seeded_provider_fields:
            continue
        if fact.provider_field in {"EngineConfiguration", "EngineCylinders"}:
            reason = "engine configuration requires a recognized layout and positive cylinder count"
        elif fact.provider_field in relevant_mapping_fields:
            reason = "provider value was blank, malformed, unsupported, or ambiguous for its canonical match"
        else:
            reason = EXCLUSION_REASONS.get(
                fact.provider_field,
                "no clean V2 canonical structured-seed mapping",
            )
        rejected.append({"provider_field": fact.provider_field, "reason": reason})
    return rejected


def build_audit(
    *,
    inputs_path: Path = DEFAULT_INPUTS_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    field_catalog_path: Path = DEFAULT_FIELD_CATALOG_PATH,
    vpic_client: VPICClient | None = None,
) -> dict[str, Any]:
    """Decode every frozen runtime-input VIN without invoking the research model."""

    corpus = load_and_validate_benchmark_inputs(inputs_path, manifest_path)
    catalog = load_field_catalog(field_catalog_path)
    client = vpic_client or VPICClient()
    researched_ids = catalog.agent_research_field_ids
    baseline_phase_a_batches = _batch_count(len(researched_ids), PHASE_A_MAX_FIELDS_PER_BATCH)
    baseline_phase_b_batches = _batch_count(len(researched_ids), PHASE_B_MAX_FIELDS_PER_BATCH)
    fixtures: list[dict[str, Any]] = []

    for item in corpus.inputs:
        if item.vehicle.vin is None:
            raise ValueError(f"runtime input lacks exact VIN: {item.fixture_id}")
        seed = client.decode_vin(item.vehicle.vin, item.vehicle.year)
        seeds = _seeds(seed)
        seeded_ids = {fact.field_id for fact in seeds}
        targets = tuple(field_id for field_id in researched_ids if field_id not in seeded_ids)
        seeded_provider_fields = {
            provider_field
            for mapping in VPIC_SEED_MAPPINGS
            if mapping.field_id in seeded_ids
            for provider_field in mapping.provider_fields
        }
        phase_a_batches = _batch_count(len(targets), PHASE_A_MAX_FIELDS_PER_BATCH)
        phase_b_batches = _batch_count(len(targets), PHASE_B_MAX_FIELDS_PER_BATCH)
        fixtures.append(
            {
                "fixture_id": item.fixture_id,
                "vin": item.vehicle.vin,
                "vpic_nonblank_provider_fields": [
                    fact.provider_field for fact in seed.facts if fact.provider_value is not None
                ],
                "accepted_canonical_seeds": [
                    {"field_id": fact.field_id, "value": fact.value, "unit": fact.unit}
                    for fact in seeds
                ],
                "rejected_nonblank_fields": _rejected_nonblank_fields(
                    seed, seeded_provider_fields
                ),
                "remaining_research_targets": len(targets),
                "expected_phase_a_batches": phase_a_batches,
                "expected_phase_b_batches": phase_b_batches,
                "estimated_model_calls": phase_a_batches + phase_b_batches,
                "estimated_model_call_reduction": (
                    baseline_phase_a_batches
                    + baseline_phase_b_batches
                    - phase_a_batches
                    - phase_b_batches
                ),
            }
        )

    seed_counts = [len(item["accepted_canonical_seeds"]) for item in fixtures]
    target_counts = [item["remaining_research_targets"] for item in fixtures]
    return {
        "audit_version": "hybrid-vpic-seed-audit-v1",
        "system_version": "hybrid-vpic-web-v2",
        "provider": "nhtsa_vpic",
        "gemini_called": False,
        "fixture_count": len(fixtures),
        "researchable_canonical_field_count": len(researched_ids),
        "baseline_expected_model_calls": baseline_phase_a_batches + baseline_phase_b_batches,
        "fixtures": fixtures,
        "aggregate": {
            "average_structured_seeds_per_fixture": sum(seed_counts) / len(seed_counts),
            "minimum_structured_seeds_per_fixture": min(seed_counts),
            "maximum_structured_seeds_per_fixture": max(seed_counts),
            "total_structured_facts": sum(seed_counts),
            "average_remaining_research_targets": sum(target_counts) / len(target_counts),
            "total_estimated_model_call_reduction": sum(
                item["estimated_model_call_reduction"] for item in fixtures
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit["aggregate"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
