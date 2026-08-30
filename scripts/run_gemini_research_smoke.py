"""Run one deliberate, non-benchmark Gemini research smoke test.

Run only after the offline suite passes and ``GEMINI_API_KEY`` is set in the
process environment. The runner deliberately permits the two evidence-first
model calls and no repair calls so a smoke run has a bounded paid external effect.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

from enthusiast_lens.model import GeminiSettings
from enthusiast_lens.models import VehicleContext
from enthusiast_lens.research import ResearchAgent


def main() -> int:
    configured = GeminiSettings.from_environment()
    settings = GeminiSettings(
        model=configured.model,
        thinking_level=configured.thinking_level,
        request_timeout_seconds=configured.request_timeout_seconds,
        poll_interval_seconds=configured.poll_interval_seconds,
        wall_clock_deadline_seconds=configured.wall_clock_deadline_seconds,
        max_repair_attempts=0,
        max_model_calls=2,
        max_search_calls=configured.max_search_calls,
    )
    vehicle = VehicleContext(
        year=2024,
        make="Honda",
        model="Civic",
        trim="Type R",
        body_style="5-door hatchback",
        transmission="6-speed manual",
        drivetrain="front-wheel drive",
        market="US",
    )
    result = ResearchAgent(settings=settings).run(
        vehicle,
        ("engine_and_measured_performance.horsepower",),
        development_trace_root=Path("artifacts/trajectories/dev"),
    )
    trace_path = Path("artifacts/trajectories/dev") / f"{result.trajectory.trajectory_id}.json"
    print(
        json.dumps(
            {
                "status": result.analysis.status.value,
                "model": result.trajectory.model,
                "thinking_level": result.trajectory.thinking_level,
                "model_call_count": result.trajectory.model_call_count,
                "interaction_id": result.trajectory.interaction_id,
                "last_provider_status": result.trajectory.last_provider_status,
                "elapsed_ms": result.trajectory.elapsed_ms,
                "trace_path": str(trace_path),
                "citation_count": sum(
                    event.event_type == "citation" for event in result.trajectory.events
                ),
                "failures": result.trajectory.failures,
            },
            indent=2,
        )
    )
    return 0 if result.analysis.status.value == "succeeded" else 1


if __name__ == "__main__":
    sys.exit(main())
