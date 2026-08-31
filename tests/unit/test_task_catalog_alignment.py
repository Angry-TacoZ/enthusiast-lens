"""Evaluation-only structural compatibility checks for the frozen scoring contract."""

from __future__ import annotations

import json
from pathlib import Path

from enthusiast_lens.evaluation.field_catalog import load_field_catalog


ROOT = Path(__file__).parents[2]
CATALOG = ROOT / "evals" / "task_definition" / "v1_objective_field_catalog.json"
FIXTURES = ROOT / "evals" / "ground_truth"


def _scorable_field_ids() -> set[str]:
    """Read only fixture structural metadata; expected values are never accessed."""

    field_ids: set[str] = set()
    for path in FIXTURES.glob("*_ground_truth.json"):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        for fact in fixture["facts"]:
            if fact["scorable"]:
                field_ids.add(fact["field_id"])
    return field_ids


def test_catalog_covers_every_frozen_scorable_field_with_explicit_acquisition() -> None:
    catalog = load_field_catalog(CATALOG)
    frozen_scorable = _scorable_field_ids()

    assert set(catalog.field_ids) == frozen_scorable
    assert set(catalog.agent_research_field_ids) | set(catalog.deterministic_derived_field_ids) == frozen_scorable
    assert set(catalog.agent_research_field_ids).isdisjoint(catalog.deterministic_derived_field_ids)
    assert catalog.deterministic_derived_field_ids == (
        "engine_and_measured_performance.power_to_weight_hp_per_us_ton",
    )


def test_full_web_runtime_has_no_answer_key_import_or_provider_prompt_path() -> None:
    runtime_sources = [
        ROOT / "src" / "enthusiast_lens" / "evaluation" / "full_web.py",
        ROOT / "src" / "enthusiast_lens" / "evaluation" / "field_catalog.py",
        ROOT / "src" / "enthusiast_lens" / "research" / "agent.py",
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in runtime_sources)

    assert "evals/ground_truth" not in source
    assert "from enthusiast_lens.evaluation.alignment" not in source
    assert "from enthusiast_lens.ground_truth" not in source


def test_ground_truth_path_is_confined_to_the_deterministic_grader() -> None:
    grader = ROOT / "src" / "enthusiast_lens" / "evaluation" / "grader.py"
    runtime = ROOT / "src" / "enthusiast_lens" / "evaluation" / "full_web.py"

    assert "evals/ground_truth" in grader.read_text(encoding="utf-8")
    assert "evals/ground_truth" not in runtime.read_text(encoding="utf-8")
