"""Offline contract tests for the standalone judge UI API."""

from __future__ import annotations

from datetime import UTC, datetime
import time
from typing import Any

from fastapi.testclient import TestClient

from enthusiast_lens.api import (
    FIELD_CATALOG_PATH,
    PRODUCT_ARTIFACTS_ROOT,
    RUNTIME_INPUTS_PATH,
    VEHICLE_TO_FIXTURE,
    Core24JobService,
    create_app,
)
from enthusiast_lens.evaluation.full_web import BaselineResult
from enthusiast_lens.models import RunMode, RunStatus, VehicleContext


def _result(fixture_id: str, mode: RunMode = RunMode.FULL_WEB) -> BaselineResult:
    now = datetime.now(UTC)
    return BaselineResult(
        system_version="test-core-24",
        fixture_id=fixture_id,
        vehicle_family_id="test",
        vehicle=VehicleContext(year=2026, make="Test", model="Vehicle"),
        run_mode=mode,
        model="test-provider",
        instruction_version="test",
        instruction_sha256="0" * 64,
        field_catalog_version="hackathon-core-24-v1",
        field_catalog_sha256="1" * 64,
        started_at=now,
        completed_at=now,
        status=RunStatus.SUCCEEDED,
        requested_field_ids=(),
        canonical_field_ids=(),
        trajectory_path="C:/private/product-run.json",
    )


def _wait_for_terminal(client: TestClient, job_id: str) -> dict[str, Any]:
    for _ in range(100):
        response = client.get(f"/api/analysis-runs/{job_id}")
        body = response.json()
        if body["status"] not in {"queued", "running"}:
            return body
        time.sleep(0.01)
    raise AssertionError("analysis job did not complete")


def test_ui_vehicle_mapping_is_the_exact_core_24_allowlist() -> None:
    assert VEHICLE_TO_FIXTURE == {
        "miata-gt-auto": "01_miata_gt_auto_ground_truth.json",
        "mini-cooper-s": "02a_mini_acc_true_positive_ground_truth.json",
        "gr86-base": "03_gr86_base_ground_truth.json",
        "mustang-ecoboost": "04_mustang_ecoboost_premium_ground_truth.json",
        "elantra-n-line": "05_elantra_n_line_ground_truth.json",
        "cadillac-ats": "06_cadillac_ats_base_ground_truth.json",
        "wrangler-4xe": "07_jeep_wrangler_rubicon_4xe_ground_truth.json",
        "charger-daytona": "08_charger_daytona_ground_truth.json",
        "kia-soul-turbo": "09_kia_soul_turbo_ground_truth.json",
        "tesla-model-y": "10_tesla_model_y_long_range_awd_ground_truth.json",
        "wrx-limited": "11_wrx_limited_cvt_ground_truth.json",
    }
    assert "ground_truth" not in RUNTIME_INPUTS_PATH.parts
    assert "ground_truth" not in FIELD_CATALOG_PATH.parts
    assert "evals" not in PRODUCT_ARTIFACTS_ROOT.parts


def test_api_runs_allowlisted_request_and_returns_canonical_result() -> None:
    invoked: list[tuple[str, str]] = []

    def full_web(fixture_id: str) -> BaselineResult:
        invoked.append(("full_web", fixture_id))
        return _result(fixture_id)

    def hybrid(fixture_id: str) -> BaselineResult:
        invoked.append(("hybrid", fixture_id))
        return _result(fixture_id, RunMode.HYBRID)

    client = TestClient(create_app(Core24JobService(full_web_runner=full_web, hybrid_runner=hybrid)))
    started = client.post("/api/analysis-runs", json={"vehicle_id": "wrx-limited", "mode": "hybrid"})

    assert started.status_code == 202
    result = _wait_for_terminal(client, started.json()["id"])
    assert result["status"] == "succeeded"
    assert result["result"]["fixture_id"] == "11_wrx_limited_cvt_ground_truth.json"
    assert result["result"]["run_mode"] == "hybrid"
    assert result["result"]["trajectory_path"] is None
    assert invoked == [("hybrid", "11_wrx_limited_cvt_ground_truth.json")]


def test_api_rejects_unknown_and_browser_supplied_fixture_values() -> None:
    client = TestClient(create_app(Core24JobService(full_web_runner=_result, hybrid_runner=_result)))

    unknown = client.post("/api/analysis-runs", json={"vehicle_id": "../../ground_truth", "mode": "full_web"})
    extra = client.post(
        "/api/analysis-runs",
        json={"vehicle_id": "miata-gt-auto", "mode": "full_web", "fixture_id": "anything.json"},
    )

    assert unknown.status_code == 422
    assert extra.status_code == 422
