"""Offline integrity tests for the isolated Hackathon Core 24 task."""

from __future__ import annotations

from pathlib import Path

from enthusiast_lens.evaluation import full_web, hybrid
from enthusiast_lens.evaluation.field_catalog import (
    HACKATHON_CORE_24_FIELD_CATALOG_PATH,
    load_field_catalog,
)
from enthusiast_lens.evaluation.full_web import FullWebBaselineRunner
from enthusiast_lens.models import FactResult, FactState
from enthusiast_lens.research.agent import (
    PHASE_A_PARENT_DEADLINE_SECONDS,
    PHASE_B_PARENT_DEADLINE_SECONDS,
    ResearchAgent,
)


ROOT = Path(__file__).parents[2]
INPUTS = ROOT / "evals" / "inputs" / "benchmark_inputs.json"


def test_core_24_catalog_has_exactly_one_deterministic_field() -> None:
    catalog = load_field_catalog(HACKATHON_CORE_24_FIELD_CATALOG_PATH)

    assert catalog.catalog_version == "hackathon-core-24-v1"
    assert len(catalog.field_ids) == 24
    assert len(catalog.agent_research_field_ids) == 23
    assert catalog.deterministic_derived_field_ids == (
        "engine_and_measured_performance.pounds_per_horsepower",
    )


def test_core_24_workload_fits_one_batch_per_phase() -> None:
    catalog = load_field_catalog(HACKATHON_CORE_24_FIELD_CATALOG_PATH)

    assert ResearchAgent._phase_a_batches(catalog.agent_research_field_ids) == (
        catalog.agent_research_field_ids,
    )
    assert ResearchAgent._phase_b_batches(catalog.agent_research_field_ids) == (
        catalog.agent_research_field_ids,
    )
    assert ResearchAgent.maximum_model_calls_for(catalog.agent_research_field_ids) == 2


def test_full_web_and_hybrid_share_the_90_second_phase_envelope() -> None:
    assert PHASE_A_PARENT_DEADLINE_SECONDS == 90
    assert PHASE_B_PARENT_DEADLINE_SECONDS == 90
    assert full_web.ResearchAgent is ResearchAgent
    assert hybrid.ResearchAgent is ResearchAgent


def test_core_24_pounds_per_horsepower_is_deterministic() -> None:
    runner = FullWebBaselineRunner(
        inputs_path=INPUTS,
        field_catalog_path=HACKATHON_CORE_24_FIELD_CATALOG_PATH,
    )
    assert runner.system_version == "full-web-core-24-v1"
    facts = runner._append_deterministic_facts(
        (
            FactResult(
                field_id="engine_and_measured_performance.horsepower",
                value=181,
                unit="hp",
                state=FactState.KNOWN,
            ),
            FactResult(
                field_id="engine_and_measured_performance.curb_weight_lb",
                value=2403,
                unit="lb",
                state=FactState.KNOWN,
            ),
        )
    )

    derived = facts[-1]
    assert derived.field_id == "engine_and_measured_performance.pounds_per_horsepower"
    assert derived.value == 13.28
    assert derived.unit == "lb/hp"
    assert derived.state is FactState.KNOWN
    assert derived.origin is not None and derived.origin.value == "derived"


def test_core_24_compound_fields_are_explicitly_structured_in_catalog() -> None:
    descriptions = {
        entry.field_id: entry.description
        for entry in load_field_catalog(HACKATHON_CORE_24_FIELD_CATALOG_PATH).fields
    }

    assert "front_diameter_in" in descriptions["brakes_wheels_and_tires.rotor_diameters_in"]
    assert "brand_model" in descriptions["brakes_wheels_and_tires.default_tire"]
    assert "front_size" in descriptions["brakes_wheels_and_tires.default_tire"]
    assert "rear_size" in descriptions["brakes_wheels_and_tires.default_tire"]
    assert "fuel_tank_gal" in descriptions["energy_storage.capacity"]
    assert "battery_kwh" in descriptions["energy_storage.capacity"]
    assert "front" in descriptions["suspension_axles_and_chassis.suspension_layout"]
    assert "rear" in descriptions["suspension_axles_and_chassis.suspension_layout"]
