"""Run the authorized three-probe isolated synchronous Gemini validation ladder."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any
from uuid import uuid4

from enthusiast_lens.model import (
    GeminiSettings,
    IsolatedGeminiWorkerProvider,
    ModelExecution,
    ModelProviderError,
    StructuredModelRequest,
    sanitize_for_trace,
)
from enthusiast_lens.models import VehicleContext
from enthusiast_lens.research import ResearchAgent


TRACE_ROOT = Path("artifacts/trajectories/dev")


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_for_trace(value), indent=2, default=str), encoding="utf-8")


def _events(execution: ModelExecution) -> list[dict[str, Any]]:
    return [event.model_dump(mode="json") for event in execution.events]


def _counts(execution: ModelExecution) -> tuple[int, int]:
    return (
        sum(event.event_type in {"google_search_call", "google_search_query"} for event in execution.events),
        sum(event.event_type in {"citation", "grounding_support"} for event in execution.events),
    )


def run_plain_probe(
    settings: GeminiSettings, *, name: str, vehicle: VehicleContext, prompt: str, search: bool,
    thinking_level: str | None = None,
) -> dict[str, Any]:
    """Run one worker-owned synchronous interaction without a retry path."""

    trace_path = TRACE_ROOT / f"gemini-sync-{name.lower()}-{uuid4()}.json"
    request = StructuredModelRequest(
        model=settings.model,
        prompt=prompt,
        thinking_level=thinking_level,
        enable_google_search=search,
        timeout_seconds=settings.request_timeout_seconds,
    )
    trace: dict[str, Any] = {
        "probe": name,
        "vehicle": vehicle.model_dump(mode="json", exclude_none=True),
        "provider": "gemini",
        "model": settings.model,
        "thinking_level": settings.thinking_level,
        "execution_mode": "synchronous_isolated_worker",
        "google_search_enabled": search,
        "parent_deadline_seconds": settings.wall_clock_deadline_seconds,
        "request_timeout_seconds": settings.request_timeout_seconds,
    }
    try:
        execution = IsolatedGeminiWorkerProvider(settings).execute(request)
    except ModelProviderError as error:
        trace.update(
            {
                "status": "failed",
                "parent_terminated_worker": error.__class__.__name__ == "WorkerDeadlineExceededError",
                "provider_error": {
                    "normalized_error": str(error),
                    "provider_diagnostic": error.diagnostic.model_dump(mode="json") if error.diagnostic else None,
                },
            }
        )
    else:
        search_count, citation_count = _counts(execution)
        successful = (execution.status or "completed") == "completed" and bool(execution.output_text)
        if search:
            successful = successful and search_count > 0 and citation_count > 0
        trace.update(
            {
                "status": "succeeded" if successful else "failed",
                "parent_terminated_worker": False,
                "interaction_id": execution.request_id,
                "provider_status": execution.status,
                "api_call_latency_ms": execution.provider_latency_ms or execution.latency_ms,
                "parent_total_latency_ms": execution.latency_ms,
                "search_call_count": search_count,
                "citation_count": citation_count,
                "usage": execution.usage.model_dump(mode="json"),
                "observable_events": _events(execution),
                "output_text": execution.output_text,
            }
        )
        if not successful:
            trace["provider_error"] = {"normalized_error": "completed_interaction_missing_required_observable_output"}
    _write(trace_path, trace)
    return {**trace, "trace_path": str(trace_path)}


def run_research_probe(settings: GeminiSettings) -> dict[str, Any]:
    vehicle = VehicleContext(year=2024, make="Toyota", model="GR Corolla", trim="Circuit Edition", body_style="5-door hatchback", transmission="6-speed manual", drivetrain="all-wheel drive", market="US")
    result = ResearchAgent(settings=settings).run(
        vehicle,
        ("engine.horsepower", "transmission.type", "drivetrain.front_differential.type", "suspension.front.type"),
        development_trace_root=TRACE_ROOT,
    )
    trace_path = TRACE_ROOT / f"{result.trajectory.trajectory_id}.json"
    phase_a_events = [event for event in result.trajectory.events if event.details.get("phase") == "evidence_acquisition"]
    phase_b_events = [event for event in result.trajectory.events if event.details.get("phase") == "synthesis"]
    return {
        "probe": "two_phase_research",
        "status": "succeeded" if result.analysis.status.value == "succeeded" else "failed",
        "vehicle": vehicle.model_dump(mode="json", exclude_none=True),
        "model": result.trajectory.model,
        "execution_mode": "synchronous_isolated_worker",
        "interaction_id": result.trajectory.interaction_id,
        "provider_status": result.trajectory.last_provider_status,
        "phase_a_latency_ms": result.trajectory.phase_a_latency_ms,
        "phase_b_latency_ms": result.trajectory.phase_b_latency_ms,
        "parent_total_latency_ms": result.trajectory.elapsed_ms,
        "search_call_count": result.trajectory.search_query_count,
        "grounded_source_count": result.trajectory.grounded_source_count,
        "citation_count": sum(event.event_type == "citation" for event in result.trajectory.events),
        "usage": result.trajectory.usage.model_dump(mode="json"),
        "phase_a_usage": result.trajectory.phase_a_usage.model_dump(mode="json"),
        "phase_b_usage": result.trajectory.phase_b_usage.model_dump(mode="json"),
        "phase_a_event_count": len(phase_a_events),
        "phase_b_event_count": len(phase_b_events),
        "structured_validation": "passed" if result.analysis.status.value == "succeeded" else "failed",
        "facts": [fact.model_dump(mode="json") for fact in result.facts],
        "failures": list(result.trajectory.failures),
        "trace_path": str(trace_path),
    }


def main() -> int:
    configured = GeminiSettings.from_environment()
    civic = VehicleContext(year=2024, make="Honda", model="Civic", trim="Type R", market="US")
    corolla = VehicleContext(year=2024, make="Toyota", model="Corolla", trim="XSE", market="US")
    settings_a = configured.model_copy(update={"request_timeout_seconds": 15, "wall_clock_deadline_seconds": 20})
    settings_b = configured.model_copy(update={"wall_clock_deadline_seconds": 30})
    settings_c = configured.model_copy(update={"wall_clock_deadline_seconds": 60})
    probes = (
        lambda: run_plain_probe(settings_a, name="A", vehicle=civic, search=False, thinking_level=None, prompt="Given the supplied vehicle context, return one short sentence identifying the vehicle."),
        lambda: run_plain_probe(settings_b, name="B", vehicle=corolla, search=True, thinking_level=None, prompt="For the 2024 Toyota Corolla XSE in the US market, verify its published combined EPA fuel-economy rating using public web evidence. Return one short sentence with a source citation."),
        lambda: run_research_probe(settings_c),
    )
    results: list[dict[str, Any]] = []
    for probe in probes:
        result = probe()
        results.append(result)
        print(json.dumps(sanitize_for_trace(result), indent=2, default=str))
        if result["status"] != "succeeded":
            break
    return 0 if len(results) == 3 and all(item["status"] == "succeeded" for item in results) else 1


if __name__ == "__main__":
    sys.exit(main())
