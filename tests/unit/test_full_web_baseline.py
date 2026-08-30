"""Offline contracts for the answer-key-free Full-Web baseline runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from enthusiast_lens.evaluation.field_catalog import load_field_catalog
from enthusiast_lens.evaluation.full_web import FullWebBaselineRunner, main
from enthusiast_lens.model import GeminiSettings, ModelUsage
from enthusiast_lens.models import AnalysisRunMetadata, RunMode, RunStatus, VehicleContext
from enthusiast_lens.research.result import ResearchRunResult, ResearchTrajectory
from enthusiast_lens.research.instructions import INSTRUCTION_VERSION, instruction_hash


ROOT = Path(__file__).parents[2]
INPUTS = ROOT / "evals" / "inputs" / "benchmark_inputs.json"
CATALOG = ROOT / "evals" / "task_definition" / "v1_objective_field_catalog.json"


def _fake_result(
    vehicle: VehicleContext,
    fields: tuple[str, ...],
    status: str = "succeeded",
    *,
    estimated_cost_usd: float | None = None,
    search_query_count: int = 0,
) -> ResearchRunResult:
    from datetime import UTC, datetime

    started = datetime.now(UTC)
    trajectory = ResearchTrajectory(
        trajectory_id="research-test",
        started_at=started,
        completed_at=started,
        status=status,
        provider="stub",
        model="gemini-3.6-flash",
        thinking_level="medium",
        instruction_version=INSTRUCTION_VERSION,
        instruction_sha256=instruction_hash(),
        vehicle=vehicle,
        requested_field_ids=fields,
        usage=ModelUsage(estimated_cost_usd=estimated_cost_usd),
        model_call_count=2,
        search_query_count=search_query_count,
    )
    analysis = AnalysisRunMetadata(
        run_id=trajectory.trajectory_id,
        mode=RunMode.FULL_WEB,
        started_at=started,
        completed_at=started,
        status=RunStatus(status),
        input_context=vehicle,
        model_call_count=2,
        retry_count=0,
    )
    return ResearchRunResult(trajectory=trajectory, analysis=analysis)


class FakeAgent:
    calls: list[tuple[VehicleContext, tuple[str, ...]]] = []
    status = "succeeded"
    estimated_cost_usd: float | None = None
    search_query_count = 0

    def __init__(self, settings: GeminiSettings, provider: Any = None) -> None:
        self.settings = settings
        self.provider = provider

    def run(self, vehicle: VehicleContext, fields: tuple[str, ...], *, development_trace_root: Path) -> ResearchRunResult:
        self.calls.append((vehicle, fields))
        development_trace_root.mkdir(parents=True, exist_ok=True)
        result = _fake_result(
            vehicle,
            fields,
            self.status,
            estimated_cost_usd=self.estimated_cost_usd,
            search_query_count=self.search_query_count,
        )
        (development_trace_root / "research-test.json").write_text(
            result.trajectory.model_dump_json(indent=2), encoding="utf-8"
        )
        return result


def runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FullWebBaselineRunner:
    monkeypatch.setattr("enthusiast_lens.evaluation.full_web.ResearchAgent", FakeAgent)
    FakeAgent.calls = []
    FakeAgent.status = "succeeded"
    FakeAgent.estimated_cost_usd = None
    FakeAgent.search_query_count = 0
    return FullWebBaselineRunner(
        inputs_path=INPUTS,
        field_catalog_path=CATALOG,
        output_root=tmp_path / "full_web",
        settings=GeminiSettings(model="gemini-3.6-flash", request_timeout_seconds=1, wall_clock_deadline_seconds=10),
    )


def test_catalog_is_fixed_and_answer_key_independent() -> None:
    catalog = load_field_catalog(CATALOG)
    assert len(catalog.fields) == 69
    assert len(catalog.field_ids) == len(set(catalog.field_ids))
    assert all("ground_truth" not in field.field_id for field in catalog.fields)
    source = (ROOT / "src" / "enthusiast_lens" / "evaluation" / "full_web.py").read_text(encoding="utf-8")
    assert "ground_truth" in source  # only the defensive path-name guard is allowed
    assert "from enthusiast_lens.adapters" not in source
    assert "from enthusiast_lens.models.structured_seed" not in source


def test_one_fixture_maps_to_vehicle_context_and_full_web_uses_catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = runner(tmp_path, monkeypatch)
    item = run.select(fixture_ids=("01_miata_gt_auto_ground_truth.json",))[0]
    result = run.run((item,), live=True)[0]
    assert result is not None
    assert result.fixture_id == item.fixture_id
    assert result.vehicle == item.vehicle
    assert result.run_mode is RunMode.FULL_WEB
    assert result.requested_field_ids == load_field_catalog(CATALOG).field_ids
    assert FakeAgent.calls[0][0] == item.vehicle


def test_result_artifact_and_failed_result_are_persisted_without_retry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = runner(tmp_path, monkeypatch)
    FakeAgent.status = "failed"
    item = run.select(fixture_ids=("01_miata_gt_auto_ground_truth.json",))[0]
    result = run.run((item,), live=True)[0]
    assert result is not None and result.status is RunStatus.FAILED
    artifact = tmp_path / "full_web" / item.fixture_id / "result.json"
    assert artifact.is_file()
    assert json.loads(artifact.read_text(encoding="utf-8"))["facts"] == []
    calls = len(FakeAgent.calls)
    again = run.run((item,), live=True)[0]
    assert again is not None and again.status is RunStatus.FAILED
    assert len(FakeAgent.calls) == calls


def test_completed_identity_skips_only_matching_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = runner(tmp_path, monkeypatch)
    item = run.select(fixture_ids=("01_miata_gt_auto_ground_truth.json",))[0]
    first = run.run((item,), live=True)[0]
    assert first is not None
    calls = len(FakeAgent.calls)
    skipped = run.run((item,), live=True)[0]
    assert skipped is None
    assert len(FakeAgent.calls) == calls
    fixture_dir = tmp_path / "full_web" / item.fixture_id
    assert tuple(fixture_dir.glob("attempt-*.json")) == ()


def test_live_cli_requires_explicit_selector_before_runner_construction(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    constructed = False

    def fail_if_constructed(**_: object) -> None:
        nonlocal constructed
        constructed = True
        pytest.fail("runner must not be constructed for selector-less live execution")

    monkeypatch.setattr("enthusiast_lens.evaluation.full_web.FullWebBaselineRunner", fail_if_constructed)
    with pytest.raises(SystemExit) as error:
        main(["--live"])
    assert error.value.code == 2
    assert constructed is False
    assert "requires either --fixture <fixture-id> or --all" in capsys.readouterr().err


def test_selection_and_all_fixture_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = runner(tmp_path, monkeypatch)
    fixtures = run.select(all_fixtures=True)
    plan = run.dry_run(fixtures)
    assert plan.fixture_count == 12
    assert plan.maximum_total_model_calls == 24
    assert plan.declared_search_budget == 4
    assert plan.rough_projected_cost_usd < plan.maximum_total_cost_usd
    assert len(run.select(fixture_ids=(fixtures[0].fixture_id,))) == 1
    with pytest.raises(ValueError, match="choose --all"):
        run.select(fixture_ids=(fixtures[0].fixture_id,), all_fixtures=True)


def test_cost_ceiling_blocks_before_provider_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = runner(tmp_path, monkeypatch)
    run.max_total_cost_usd = 0
    item = run.select(fixture_ids=("01_miata_gt_auto_ground_truth.json",))[0]
    with pytest.raises(RuntimeError, match="cost ceiling"):
        run.run((item,), live=True)
    assert FakeAgent.calls == []


def test_failed_attempt_is_archived_before_successful_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = runner(tmp_path, monkeypatch)
    item = run.select(fixture_ids=("01_miata_gt_auto_ground_truth.json",))[0]
    FakeAgent.status = "failed"
    FakeAgent.estimated_cost_usd = 0.05
    failed = run.run((item,), live=True)[0]
    assert failed is not None and failed.status is RunStatus.FAILED

    FakeAgent.status = "succeeded"
    FakeAgent.estimated_cost_usd = 0.06
    succeeded = run.run((item,), live=True, retry_failed=True)[0]
    assert succeeded is not None and succeeded.status is RunStatus.SUCCEEDED

    fixture_dir = tmp_path / "full_web" / item.fixture_id
    archives = tuple(fixture_dir.glob("attempt-*-failed-*.json"))
    assert len(archives) == 1
    preserved = json.loads(archives[0].read_text(encoding="utf-8"))
    current = json.loads((fixture_dir / "result.json").read_text(encoding="utf-8"))
    assert preserved["status"] == "failed"
    assert preserved["estimated_cost_usd"] == 0.05
    assert preserved["trajectory_path"].endswith("research-test.json")
    assert current["status"] == "succeeded"
    assert current["estimated_cost_usd"] == 0.06


def test_identity_change_archives_superseded_current_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = runner(tmp_path, monkeypatch)
    item = run.select(fixture_ids=("01_miata_gt_auto_ground_truth.json",))[0]
    first = run.run((item,), live=True)[0]
    assert first is not None
    result_path = tmp_path / "full_web" / item.fixture_id / "result.json"
    stale = json.loads(result_path.read_text(encoding="utf-8"))
    stale["system_version"] = "superseded-system"
    result_path.write_text(json.dumps(stale, indent=2), encoding="utf-8")

    replacement = run.run((item,), live=True)[0]
    assert replacement is not None and replacement.status is RunStatus.SUCCEEDED
    archives = tuple(result_path.parent.glob("attempt-*-succeeded-*.json"))
    assert len(archives) == 1
    assert json.loads(archives[0].read_text(encoding="utf-8"))["system_version"] == "superseded-system"


def test_resumed_cost_includes_matching_current_results_before_provider_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_run = runner(tmp_path, monkeypatch)
    fixtures = first_run.select(all_fixtures=True)
    FakeAgent.estimated_cost_usd = 0.20
    first_run.run((fixtures[0],), live=True)

    resumed = runner(tmp_path, monkeypatch)
    resumed.max_total_cost_usd = 0.30
    with pytest.raises(RuntimeError, match="cost ceiling"):
        resumed.run((fixtures[1],), live=True)
    assert FakeAgent.calls == []


def test_resumed_unknown_cost_stops_before_another_provider_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_run = runner(tmp_path, monkeypatch)
    fixtures = first_run.select(all_fixtures=True)
    first_run.run((fixtures[0],), live=True)

    resumed = runner(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError, match="cost is unknown"):
        resumed.run((fixtures[1],), live=True)
    assert FakeAgent.calls == []


def test_resumed_cost_uses_current_result_without_counting_archived_attempts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initial = runner(tmp_path, monkeypatch)
    fixtures = initial.select(all_fixtures=True)
    FakeAgent.status = "failed"
    FakeAgent.estimated_cost_usd = 1.50
    initial.run((fixtures[0],), live=True)
    FakeAgent.status = "succeeded"
    FakeAgent.estimated_cost_usd = 0.01
    initial.run((fixtures[0],), live=True, retry_failed=True)

    resumed = runner(tmp_path, monkeypatch)
    resumed.max_total_cost_usd = 0.20
    FakeAgent.estimated_cost_usd = 0.01
    result = resumed.run((fixtures[1],), live=True)[0]
    assert result is not None and result.status is RunStatus.SUCCEEDED
    assert len(FakeAgent.calls) == 1


def test_declared_search_budget_does_not_replace_observed_query_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = runner(tmp_path, monkeypatch)
    item = run.select(fixture_ids=("01_miata_gt_auto_ground_truth.json",))[0]
    FakeAgent.search_query_count = 5
    result = run.run((item,), live=True)[0]
    assert result is not None
    assert run.dry_run((item,)).declared_search_budget == 4
    assert result.search_query_count == 5


def test_ground_truth_path_is_rejected_before_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = runner(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="ground-truth"):
        FullWebBaselineRunner(
            inputs_path=ROOT / "evals" / "ground_truth" / "manifest.json",
            field_catalog_path=CATALOG,
            output_root=tmp_path / "full_web",
        )
    assert FakeAgent.calls == []
