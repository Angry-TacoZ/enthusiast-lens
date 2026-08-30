"""Run the authorized three-probe, non-benchmark Gemini validation ladder.

Each probe creates at most one paid Gemini interaction. The ladder stops at
the first failure and deliberately provides no retry path.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Any
from uuid import uuid4

from enthusiast_lens.model import (
    GeminiModelClient,
    GeminiSettings,
    ModelExecution,
    ModelProviderError,
    StructuredModelRequest,
    sanitize_for_trace,
)
from enthusiast_lens.models import VehicleContext
from enthusiast_lens.research import ResearchAgent


TRACE_ROOT = Path("artifacts/trajectories/dev")
TERMINAL_STATUSES = {"completed", "failed", "cancelled", "incomplete", "budget_exceeded"}


def _write_trace(path: Path, trace: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_for_trace(trace), indent=2, default=str), encoding="utf-8")


def _append_execution(trace: dict[str, Any], execution: ModelExecution) -> None:
    trace["interaction_id"] = execution.request_id or trace.get("interaction_id")
    trace["last_provider_status"] = execution.status
    trace["usage"] = execution.usage.model_dump(mode="json")
    existing_events = trace.get("observable_events", [])
    incoming_events = [event.model_dump(mode="json") for event in execution.events]
    fingerprints = {
        json.dumps(
            {"event_type": event.get("event_type"), "details": event.get("details")},
            sort_keys=True,
            default=str,
        )
        for event in existing_events
    }
    for event in incoming_events:
        fingerprint = json.dumps(
            {"event_type": event.get("event_type"), "details": event.get("details")},
            sort_keys=True,
            default=str,
        )
        if fingerprint not in fingerprints:
            existing_events.append(event)
            fingerprints.add(fingerprint)
    trace["observable_events"] = existing_events
    if execution.output_text:
        trace["output_text"] = execution.output_text


def _error_details(error: ModelProviderError) -> dict[str, Any]:
    details: dict[str, Any] = {"normalized_error": str(error)}
    if error.diagnostic is not None:
        details["provider_diagnostic"] = error.diagnostic.model_dump(mode="json")
    return details


def _event_count(trace: dict[str, Any], event_type: str) -> int:
    return sum(event.get("event_type") == event_type for event in trace["observable_events"])


def _probe_settings(configured: GeminiSettings, deadline_seconds: float) -> GeminiSettings:
    return configured.model_copy(update={"wall_clock_deadline_seconds": deadline_seconds})


def run_direct_probe(
    client: GeminiModelClient,
    settings: GeminiSettings,
    *,
    name: str,
    vehicle: VehicleContext,
    prompt: str,
    search: bool,
) -> dict[str, Any]:
    """Run one plain-text interaction and persist its sanitized lifecycle."""

    started = time.perf_counter()
    trace_path = TRACE_ROOT / f"gemini-diagnostic-{name.lower()}-{uuid4()}.json"
    trace: dict[str, Any] = {
        "probe": name,
        "vehicle": vehicle.model_dump(mode="json", exclude_none=True),
        "provider": "gemini",
        "model": settings.model,
        "thinking_level": settings.thinking_level,
        "background": True,
        "google_search_enabled": search,
        "structured_output_enabled": False,
        "request_timeout_seconds": settings.request_timeout_seconds,
        "poll_interval_seconds": settings.poll_interval_seconds,
        "wall_clock_deadline_seconds": settings.wall_clock_deadline_seconds,
        "status": "starting",
        "interaction_id": None,
        "last_provider_status": None,
        "creation_latency_ms": None,
        "total_latency_ms": None,
        "search_call_count": 0,
        "citation_count": 0,
        "usage": None,
        "observable_events": [],
        "provider_error": None,
        "cancellation": None,
    }
    _write_trace(trace_path, trace)
    request = StructuredModelRequest(
        model=settings.model,
        thinking_level=settings.thinking_level,
        prompt=prompt,
        enable_google_search=search,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        created = client.start_background(request)
    except ModelProviderError as error:
        trace["status"] = "failed"
        trace["provider_error"] = _error_details(error)
        trace["creation_latency_ms"] = error.diagnostic.elapsed_ms if error.diagnostic else None
        trace["total_latency_ms"] = round((time.perf_counter() - started) * 1000)
        _write_trace(trace_path, trace)
        return {**trace, "trace_path": str(trace_path)}

    trace["creation_latency_ms"] = created.latency_ms
    _append_execution(trace, created)
    trace["status"] = "polling"
    _write_trace(trace_path, trace)
    deadline = started + settings.wall_clock_deadline_seconds
    current = created
    while (current.status or "unknown").casefold() not in TERMINAL_STATUSES:
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            trace["status"] = "timed_out"
            try:
                cancelled = client.cancel_interaction(
                    created.request_id or "", min(settings.request_timeout_seconds, 1)
                )
                trace["cancellation"] = {"attempted": True, "provider_status": cancelled.status}
                _append_execution(trace, cancelled)
            except ModelProviderError as error:
                trace["cancellation"] = {"attempted": True, "error": _error_details(error)}
            break
        time.sleep(min(settings.poll_interval_seconds, remaining))
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            continue
        try:
            current = client.get_interaction(
                created.request_id or "", min(settings.request_timeout_seconds, remaining)
            )
        except ModelProviderError as error:
            trace["status"] = "failed"
            trace["provider_error"] = _error_details(error)
            break
        _append_execution(trace, current)
        trace["status"] = "polling"
        _write_trace(trace_path, trace)

    if trace["status"] == "polling":
        trace["status"] = "succeeded" if current.status == "completed" else "failed"
    trace["search_call_count"] = _event_count(trace, "google_search_call")
    trace["citation_count"] = _event_count(trace, "citation")
    if trace["status"] == "succeeded" and not trace.get("output_text"):
        trace["status"] = "failed"
        trace["provider_error"] = {"normalized_error": "completed_interaction_missing_text"}
    if search and trace["status"] == "succeeded" and not trace["search_call_count"]:
        trace["status"] = "failed"
        trace["provider_error"] = {"normalized_error": "google_search_not_observed"}
    trace["total_latency_ms"] = round((time.perf_counter() - started) * 1000)
    _write_trace(trace_path, trace)
    return {**trace, "trace_path": str(trace_path)}


def run_research_probe(client: GeminiModelClient, settings: GeminiSettings) -> dict[str, Any]:
    """Run the actual canonical research path for the final non-benchmark probe."""

    vehicle = VehicleContext(
        year=2024,
        make="Toyota",
        model="GR Corolla",
        trim="Circuit Edition",
        body_style="5-door hatchback",
        transmission="6-speed manual",
        drivetrain="all-wheel drive",
        market="US",
    )
    requested_fields = (
        "engine.horsepower",
        "transmission.type",
        "drivetrain.front_differential.type",
        "suspension.front.type",
    )
    result = ResearchAgent(settings=settings, provider=client).run(
        vehicle,
        requested_fields,
        development_trace_root=TRACE_ROOT,
    )
    trace_path = TRACE_ROOT / f"{result.trajectory.trajectory_id}.json"
    return {
        "probe": "C",
        "vehicle": vehicle.model_dump(mode="json", exclude_none=True),
        "provider": result.trajectory.provider,
        "model": result.trajectory.model,
        "thinking_level": result.trajectory.thinking_level,
        "background": True,
        "google_search_enabled": True,
        "structured_output_enabled": True,
        "request_timeout_seconds": settings.request_timeout_seconds,
        "poll_interval_seconds": settings.poll_interval_seconds,
        "wall_clock_deadline_seconds": settings.wall_clock_deadline_seconds,
        "status": "succeeded" if result.analysis.status.value == "succeeded" else "failed",
        "interaction_id": result.trajectory.interaction_id,
        "last_provider_status": result.trajectory.last_provider_status,
        "creation_latency_ms": next(
            (
                event.details.get("creation_latency_ms")
                for event in result.trajectory.events
                if event.event_type == "background_interaction_created"
            ),
            None,
        ),
        "total_latency_ms": result.trajectory.elapsed_ms,
        "search_call_count": result.analysis.web_search_count,
        "citation_count": sum(event.event_type == "citation" for event in result.trajectory.events),
        "usage": result.trajectory.usage.model_dump(mode="json"),
        "observable_events": [event.model_dump(mode="json") for event in result.trajectory.events],
        "structured_validation": "passed" if result.analysis.status.value == "succeeded" else "failed",
        "facts": [fact.model_dump(mode="json") for fact in result.facts],
        "warnings": list(result.warnings),
        "configuration_notes": list(result.configuration_notes),
        "failures": list(result.trajectory.failures),
        "trace_path": str(trace_path),
    }


def main() -> int:
    configured = GeminiSettings.from_environment()
    client = GeminiModelClient(configured)
    civic = VehicleContext(year=2024, make="Honda", model="Civic", trim="Type R", market="US")
    corolla = VehicleContext(year=2024, make="Toyota", model="Corolla", trim="XSE", market="US")
    probes = (
        lambda: run_direct_probe(
            client,
            _probe_settings(configured, 15),
            name="A",
            vehicle=civic,
            search=False,
            prompt="Given the supplied vehicle context, return one short sentence identifying the vehicle.",
        ),
        lambda: run_direct_probe(
            client,
            _probe_settings(configured, 30),
            name="B",
            vehicle=corolla,
            search=True,
            prompt=(
                "For the 2024 Toyota Corolla XSE in the US market, verify its published "
                "combined EPA fuel-economy rating using public web evidence. Return one short "
                "sentence with a source citation."
            ),
        ),
        lambda: run_research_probe(client, _probe_settings(configured, 60)),
    )
    results: list[dict[str, Any]] = []
    for probe in probes:
        result = probe()
        results.append(result)
        print(json.dumps(sanitize_for_trace(result), indent=2, default=str))
        if result["status"] != "succeeded":
            break
    return 0 if len(results) == 3 and all(result["status"] == "succeeded" for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
