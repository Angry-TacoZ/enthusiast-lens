"""Run exactly one minimal, non-benchmark synchronous Gemini Probe A."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Any
from uuid import uuid4

from enthusiast_lens.model import (
    GeminiSettings,
    IsolatedGeminiWorkerProvider,
    ModelProviderError,
    StructuredModelRequest,
    WorkerDeadlineExceededError,
    sanitize_for_trace,
)
from enthusiast_lens.models import VehicleContext


TRACE_ROOT = Path("artifacts/trajectories/dev")


def main() -> int:
    configured = GeminiSettings.from_environment()
    settings = configured.model_copy(
        update={"request_timeout_seconds": 30, "wall_clock_deadline_seconds": 40}
    )
    vehicle = VehicleContext(year=2024, make="Honda", model="Civic", trim="Type R", market="US")
    request = StructuredModelRequest(
        model="gemini-3.7-flash",
        prompt="Return exactly: 2024 Honda Civic Type R",
        timeout_seconds=30,
        thinking_level=None,
        enable_google_search=False,
    )
    serialized_request = json.dumps(
        {"model": request.model, "input": request.prompt}, separators=(",", ":")
    ).encode("utf-8")
    trace_path = TRACE_ROOT / f"gemini-sync-a-minimal-{uuid4()}.json"
    trace: dict[str, Any] = {
        "probe": "A",
        "vehicle": vehicle.model_dump(mode="json", exclude_none=True),
        "provider": "gemini",
        "model": request.model,
        "execution_mode": "synchronous_isolated_worker",
        "google_search_enabled": False,
        "structured_output_enabled": False,
        "thinking_configuration_sent": False,
        "serialized_provider_request_bytes": len(serialized_request),
        "worker_sdk_timeout_seconds": 30,
        "parent_deadline_seconds": 40,
        "status": "starting",
        "interaction_id": None,
        "provider_status": None,
        "api_call_latency_ms": None,
        "total_worker_latency_ms": None,
        "output_text": None,
        "usage": None,
        "provider_error": None,
        "sdk_timeout_fired": False,
        "parent_deadline_fired": False,
        "parent_terminated_worker": False,
        "observable_events": [],
    }
    TRACE_ROOT.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(json.dumps(sanitize_for_trace(trace), indent=2), encoding="utf-8")
    started = time.perf_counter()
    try:
        execution = IsolatedGeminiWorkerProvider(settings).execute(request)
    except WorkerDeadlineExceededError as error:
        trace.update(
            {
                "status": "deadline_exceeded",
                "parent_deadline_fired": True,
                "parent_terminated_worker": True,
                "total_worker_latency_ms": round((time.perf_counter() - started) * 1000),
                "provider_error": {"normalized_error": str(error), "provider_diagnostic": error.diagnostic.model_dump(mode="json") if error.diagnostic else None},
            }
        )
    except ModelProviderError as error:
        diagnostic = error.diagnostic.model_dump(mode="json") if error.diagnostic else None
        trace.update(
            {
                "status": "failed",
                "total_worker_latency_ms": round((time.perf_counter() - started) * 1000),
                "sdk_timeout_fired": bool(diagnostic and diagnostic.get("exception_class") == "APITimeoutError"),
                "provider_error": {"normalized_error": str(error), "provider_diagnostic": diagnostic},
            }
        )
    else:
        trace.update(
            {
                "status": "succeeded" if execution.status == "completed" else "failed",
                "interaction_id": execution.request_id,
                "provider_status": execution.status,
                "api_call_latency_ms": execution.provider_latency_ms or execution.latency_ms,
                "total_worker_latency_ms": execution.latency_ms,
                "output_text": execution.output_text,
                "usage": execution.usage.model_dump(mode="json"),
                "observable_events": [event.model_dump(mode="json") for event in execution.events],
            }
        )
    trace_path.write_text(json.dumps(sanitize_for_trace(trace), indent=2), encoding="utf-8")
    print(json.dumps(sanitize_for_trace(trace), indent=2))
    print("trace_path=" + str(trace_path))
    return 0 if trace["status"] == "succeeded" else 1


if __name__ == "__main__":
    sys.exit(main())
