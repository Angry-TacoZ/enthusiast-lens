from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from enthusiast_lens.models import AnalysisRunMetadata, VehicleContext


def synthetic_context() -> VehicleContext:
    return VehicleContext(year=2025, make="Synthetic Motors", model="Apex")


def test_basic_successful_run() -> None:
    started = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
    run = AnalysisRunMetadata(
        run_id="run-1",
        mode="hybrid",
        started_at=started,
        completed_at=started + timedelta(seconds=2),
        status="succeeded",
        input_context=synthetic_context(),
        model_call_count=1,
        tool_call_count=2,
        web_search_count=1,
        latency_ms=2000,
        estimated_cost_usd=0.02,
        unknown_count=3,
        retry_count=0,
        event_references=("trajectory://run-1/events",),
    )

    assert run.mode.value == "hybrid"
    assert run.status.value == "succeeded"
    assert run.unknown_count == 3


def test_partial_run_allows_missing_optional_metrics() -> None:
    run = AnalysisRunMetadata(
        run_id="run-partial",
        mode="full_web",
        started_at=datetime(2026, 8, 29, tzinfo=UTC),
        status="partial",
        input_context=synthetic_context(),
        failures=("Synthetic source unavailable",),
    )

    assert run.completed_at is None
    assert run.model_call_count is None
    assert run.estimated_cost_usd is None


@pytest.mark.parametrize(
    ("field", "value"),
    [("mode", "cached_only"), ("status", "perfect")],
)
def test_invalid_mode_or_status_is_rejected(field: str, value: str) -> None:
    data = {
        "run_id": "run-invalid",
        "mode": "full_web",
        "started_at": datetime(2026, 8, 29, tzinfo=UTC),
        "status": "started",
        "input_context": synthetic_context(),
        field: value,
    }

    with pytest.raises(ValidationError):
        AnalysisRunMetadata.model_validate(data)


def test_completed_at_cannot_precede_started_at() -> None:
    started = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
    with pytest.raises(ValidationError, match="completed_at"):
        AnalysisRunMetadata(
            run_id="run-backwards",
            mode="full_web",
            started_at=started,
            completed_at=started - timedelta(seconds=1),
            status="failed",
            input_context=synthetic_context(),
        )
