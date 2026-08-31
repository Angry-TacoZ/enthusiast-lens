"""Local product API for the standalone Core 24 judge UI.

This module intentionally exposes only a fixed vehicle-family allowlist.  The
browser cannot choose a fixture path, submit vehicle data, or reach provider
credentials; it receives the canonical runner result and source provenance.
"""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Callable, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

from enthusiast_lens.evaluation.full_web import BaselineResult, FullWebBaselineRunner
from enthusiast_lens.evaluation.hybrid import HybridRunner


LOGGER = logging.getLogger(__name__)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_INPUTS_PATH = REPOSITORY_ROOT / "evals" / "inputs" / "benchmark_inputs.json"
FIELD_CATALOG_PATH = REPOSITORY_ROOT / "evals" / "task_definition" / "hackathon_core_24_v1_field_catalog.json"
PRODUCT_ARTIFACTS_ROOT = REPOSITORY_ROOT / "artifacts" / "product_runs"

# UI IDs are deliberately mapped at the trusted boundary, rather than accepting
# a fixture path or any evaluator-owned artifact from the browser.
VEHICLE_TO_FIXTURE: dict[str, str] = {
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

RunModeValue = Literal["full_web", "hybrid"]
JobStatus = Literal["queued", "running", "succeeded", "partial", "failed"]
FAILED_ANALYSIS_ERROR = "Analysis could not complete because the research provider was temporarily unavailable. Please try again."


class StartAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    vehicle_id: str
    mode: RunModeValue


class AnalysisJobResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    status: JobStatus
    result: dict[str, Any] | None = None
    error: str | None = None


Runner = Callable[[str], BaselineResult]


class Core24JobService:
    """Run one local Core 24 analysis at a time and retain its result in memory."""

    def __init__(
        self,
        *,
        full_web_runner: Runner | None = None,
        hybrid_runner: Runner | None = None,
    ) -> None:
        self._full_web_runner = full_web_runner or self._run_full_web
        self._hybrid_runner = hybrid_runner or self._run_hybrid
        self._jobs: dict[str, AnalysisJobResponse] = {}
        self._active_job_id: str | None = None
        self._lock = Lock()

    def start(self, request: StartAnalysisRequest) -> AnalysisJobResponse:
        if request.vehicle_id not in VEHICLE_TO_FIXTURE:
            raise ValueError("vehicle_id is not a supported Core 24 vehicle family")

        with self._lock:
            if self._active_job_id is not None:
                raise RuntimeError("another analysis is already running")
            job = AnalysisJobResponse(id=str(uuid4()), status="queued")
            self._jobs[job.id] = job
            self._active_job_id = job.id

        Thread(target=self._execute, args=(job.id, request), daemon=True).start()
        return job

    def get(self, job_id: str) -> AnalysisJobResponse | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _execute(self, job_id: str, request: StartAnalysisRequest) -> None:
        with self._lock:
            self._jobs[job_id] = AnalysisJobResponse(id=job_id, status="running")
        try:
            fixture_id = VEHICLE_TO_FIXTURE[request.vehicle_id]
            result = (
                self._full_web_runner(fixture_id)
                if request.mode == "full_web"
                else self._hybrid_runner(fixture_id)
            )
            if result.status.value == "failed":
                with self._lock:
                    self._jobs[job_id] = AnalysisJobResponse(
                        id=job_id,
                        status="failed",
                        error=FAILED_ANALYSIS_ERROR,
                    )
                return
            payload = result.model_dump(mode="json")
            # The report keeps fact provenance, but a local trajectory path is an
            # implementation detail and should not be disclosed to the browser.
            payload["trajectory_path"] = None
            status: JobStatus = "succeeded" if result.status.value == "succeeded" else "partial"
            with self._lock:
                self._jobs[job_id] = AnalysisJobResponse(id=job_id, status=status, result=payload)
        except Exception:  # Provider and vPIC details stay in local logs only.
            LOGGER.exception("Core 24 analysis job failed", extra={"job_id": job_id})
            with self._lock:
                self._jobs[job_id] = AnalysisJobResponse(
                    id=job_id,
                    status="failed",
                    error="Analysis did not complete. Check the local server configuration and logs.",
                )
        finally:
            with self._lock:
                if self._active_job_id == job_id:
                    self._active_job_id = None

    @staticmethod
    def _run_full_web(fixture_id: str) -> BaselineResult:
        runner = FullWebBaselineRunner(
            inputs_path=RUNTIME_INPUTS_PATH,
            field_catalog_path=FIELD_CATALOG_PATH,
            output_root=PRODUCT_ARTIFACTS_ROOT / "full_web_core_24",
        )
        item = runner.select(fixture_ids=(fixture_id,))[0]
        return runner.run_fixture(item)

    @staticmethod
    def _run_hybrid(fixture_id: str) -> BaselineResult:
        runner = HybridRunner(
            inputs_path=RUNTIME_INPUTS_PATH,
            field_catalog_path=FIELD_CATALOG_PATH,
            output_root=PRODUCT_ARTIFACTS_ROOT / "hybrid_core_24",
        )
        return runner.run_fixture(runner.select(fixture_id))


def create_app(service: Core24JobService | None = None) -> FastAPI:
    """Create a localhost development API; run with an explicit 127.0.0.1 bind."""

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5174", "http://localhost:5174"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["content-type"],
    )
    job_service = service or Core24JobService()

    @app.post("/api/analysis-runs", response_model=AnalysisJobResponse, status_code=202)
    def start_analysis(request: StartAnalysisRequest) -> AnalysisJobResponse:
        try:
            return job_service.start(request)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except RuntimeError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.get("/api/analysis-runs/{job_id}", response_model=AnalysisJobResponse)
    def get_analysis(job_id: str) -> AnalysisJobResponse:
        job = job_service.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="analysis run not found")
        return job

    return app


app = create_app()
