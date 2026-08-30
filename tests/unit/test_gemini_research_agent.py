"""Offline contracts for isolated synchronous Gemini research and trajectories."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

import pytest
from pydantic import ValidationError

from enthusiast_lens.model import (
    GeminiModelClient,
    GeminiSettings,
    IsolatedGeminiWorkerProvider,
    MissingGeminiApiKeyError,
    ModelEvent,
    ModelExecution,
    ModelProviderError,
    ModelUsage,
    StructuredModelRequest,
    WorkerDeadlineExceededError,
)
from enthusiast_lens.model import sync_worker
from enthusiast_lens.models import VehicleContext
from enthusiast_lens.models import FactState
from enthusiast_lens.research import EvidenceBundle, GroundedSource, ProviderResearchOutput, ResearchAgent
from scripts.run_gemini_sync_ladder import _counts
from enthusiast_lens.research.result import ResearchModelOutput


def settings(**overrides: Any) -> GeminiSettings:
    values = {"model": "gemini-3.7-flash", "request_timeout_seconds": 1, "poll_interval_seconds": 1, "wall_clock_deadline_seconds": 10}
    values.update(overrides)
    return GeminiSettings(**values)


def vehicle() -> VehicleContext:
    return VehicleContext(year=2024, make="Synthetic Motors", model="Apex", trim="Track")


def test_gemini_model_selection_is_allowlisted_and_environment_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    assert GeminiSettings().model == "gemini-3.6-flash"
    assert GeminiSettings(model="gemini-3.7-flash").model == "gemini-3.7-flash"
    assert GeminiSettings(model="gemini-3.6-flash").model == "gemini-3.6-flash"
    with pytest.raises(ValidationError):
        GeminiSettings(model="arbitrary-model")

    monkeypatch.setenv("ENTHUSIAST_LENS_MODEL", "gemini-3.6-flash")
    configured = GeminiSettings.from_environment()
    assert configured.model == "gemini-3.6-flash"
    assert "GEMINI_API_KEY" not in configured.model_dump_json()


def test_configured_36_model_propagates_to_generate_content_without_provider_specific_research_contract() -> None:
    captured: dict[str, Any] = {}

    class Models:
        @staticmethod
        def generate_content(**kwargs: Any) -> Any:
            captured.update(kwargs)

            class Response:
                text = "done"
                response_id = None
                usage_metadata = None
                candidates: list[Any] = []

            return Response()

    class FakeClient:
        models = Models()

    configured = settings(model="gemini-3.6-flash")
    request = StructuredModelRequest(
        model="gemini-3.6-flash",
        prompt="test",
        timeout_seconds=1,
        thinking_level=None,
        enable_google_search=False,
    )
    GeminiModelClient(configured, client=FakeClient()).execute(request)
    assert captured["model"] == "gemini-3.6-flash"
    assert captured["contents"] == "test"
    assert captured["config"] is None

    research_source = Path(__file__).parents[2] / "src" / "enthusiast_lens" / "research"
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in research_source.glob("*.py"))
    assert "gemini-3.7-flash" not in source_text
    assert "gemini-3.6-flash" not in source_text


def test_generate_content_grounding_events_count_as_search_and_citations() -> None:
    execution = ModelExecution(
        provider="gemini",
        model="gemini-3.6-flash",
        events=(
            event("google_search_query", {"query": "example"}),
            event("grounding_source", {"url": "https://example.test/source"}),
            event("grounding_support", {"grounding_chunk_indices": [0]}),
        ),
    )
    assert _counts(execution) == (1, 1)


def payload() -> str:
    return json.dumps({"facts": [{"field_id": "engine.horsepower", "value": 315, "unit": "hp", "state": "known", "confidence": "high", "origin": "researched", "provenance": [{"source_url": "https://example.test/spec", "publisher": "Synthetic Motors", "source_type": "manufacturer", "configuration_match": "exact", "origin": "researched", "confidence": "high", "relationship": "supports", "notes": "Exact configuration."}]}]})


def event(event_type: str, details: dict[str, Any] | None = None) -> ModelEvent:
    return ModelEvent(sequence=1, event_type=event_type, observed_at="2026-08-30T00:00:00Z", details=details or {})


class StubProvider:
    def __init__(self, result: ModelExecution | None = None, error: ModelProviderError | None = None) -> None:
        self.result = result or ModelExecution(provider="stub", model="gemini-3.7-flash", request_id="int-test", status="completed", output_text=payload())
        self.error = error
        self.requests: list[StructuredModelRequest] = []

    def execute(self, request: StructuredModelRequest) -> ModelExecution:
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.result


class TwoPhaseStubProvider:
    def __init__(self, *, grounded: bool = True, synthesis_text: str | None = None, extra_events: tuple[ModelEvent, ...] = (), synthesis_error: ModelProviderError | None = None) -> None:
        self.requests: list[StructuredModelRequest] = []
        self.grounded = grounded
        self.extra_events = extra_events
        self.synthesis_error = synthesis_error
        self.synthesis_text = synthesis_text or json.dumps({
            "facts": [{"field_id": "engine.horsepower", "value": 315, "unit": "hp", "state": "known", "confidence": "high", "source_ids": ["S1"]}],
            "warnings": [],
            "configuration_notes": [],
        })

    def execute(self, request: StructuredModelRequest) -> ModelExecution:
        self.requests.append(request)
        if len(self.requests) == 1:
            events = [event("google_search_query", {"query": "Synthetic Apex horsepower"})]
            if self.grounded:
                events.extend([
                    event("grounding_source", {"index": 0, "url": "https://example.test/spec", "title": "Synthetic spec"}),
                    event("grounding_support", {"grounding_chunk_indices": [0], "segment": {"text": "315 hp"}}),
                    event("model_output", {"text": "Grounded summary"}),
                ])
            else:
                events.append(event("model_output", {"text": "The model mentioned https://model.example/only"}))
            events.extend(self.extra_events)
            return ModelExecution(provider="stub", model=request.model, request_id="phase-a", status="completed", output_text="Grounded summary", latency_ms=1200, events=tuple(events), usage=ModelUsage(input_tokens=100, output_tokens=20, total_tokens=120))
        if self.synthesis_error:
            raise self.synthesis_error
        return ModelExecution(provider="stub", model=request.model, request_id="phase-b", status="completed", output_text=self.synthesis_text, latency_ms=800, usage=ModelUsage(input_tokens=80, output_tokens=30, thinking_tokens=10, total_tokens=120))


def test_research_uses_two_phases_and_captures_grounded_steps(tmp_path: Path) -> None:
    provider = TwoPhaseStubProvider()
    result = ResearchAgent(settings(), provider).run(vehicle(), ("engine.horsepower",), development_trace_root=tmp_path)

    assert result.analysis.status.value == "succeeded"
    assert len(provider.requests) == 2
    assert provider.requests[0].enable_google_search is True
    assert provider.requests[0].response_schema is None
    assert provider.requests[1].enable_google_search is False
    assert provider.requests[1].response_schema is not None
    assert provider.requests[1].thinking_level == "medium"
    assert result.analysis.web_search_count == 1
    assert result.trajectory.grounded_source_count == 1
    assert result.trajectory.model_call_count == 2
    assert result.trajectory.usage.total_tokens == 240
    assert str(result.facts[0].provenance[0].source_url) == "https://example.test/spec"
    assert result.trajectory.retry_count == 0
    trace = (tmp_path / f"{result.trajectory.trajectory_id}.json").read_text(encoding="utf-8")
    assert "grounding_source" in trace and "evidence_bundle_created" in trace


def test_deadline_is_a_failure_not_unknown_and_never_retries() -> None:
    provider = StubProvider(error=WorkerDeadlineExceededError("deadline"))
    result = ResearchAgent(settings(), provider).run(vehicle(), ("engine.horsepower",))

    assert result.analysis.status.value == "failed"
    assert result.facts == ()
    assert result.trajectory.failures == ("phase_a_deadline_exceeded",)
    assert result.trajectory.model_call_count == 1
    assert result.analysis.model_call_count == 1
    assert result.trajectory.retry_count == 0
    assert len(provider.requests) == 1


def test_provider_failure_and_malformed_output_are_preserved_without_retry() -> None:
    failed = ResearchAgent(settings(), StubProvider(error=ModelProviderError("provider down"))).run(vehicle(), ("engine.horsepower",))
    malformed_provider = TwoPhaseStubProvider(synthesis_text="not json")
    malformed = ResearchAgent(settings(), malformed_provider).run(vehicle(), ("engine.horsepower",))

    assert failed.analysis.status.value == "failed"
    assert "provider down" in failed.trajectory.failures[0]
    assert failed.trajectory.model_call_count == 1
    assert failed.analysis.model_call_count == 1
    assert failed.trajectory.retry_count == 0
    assert malformed.analysis.status.value == "failed"
    assert malformed.trajectory.retry_count == 0
    assert len(malformed_provider.requests) == 2


def test_phase_b_provider_failure_counts_both_attempted_calls() -> None:
    provider = TwoPhaseStubProvider(synthesis_error=ModelProviderError("synthesis down"))
    result = ResearchAgent(settings(), provider).run(vehicle(), ("engine.horsepower",))
    assert result.analysis.status.value == "failed"
    assert result.trajectory.model_call_count == 2
    assert result.analysis.model_call_count == 2
    assert result.trajectory.retry_count == 0
    assert len(provider.requests) == 2


def test_zero_grounded_sources_fails_without_synthesis_and_rejects_model_urls() -> None:
    provider = TwoPhaseStubProvider(grounded=False)
    result = ResearchAgent(settings(), provider).run(vehicle(), ("engine.horsepower",))
    assert result.analysis.status.value == "failed"
    assert result.trajectory.status == "ungrounded_research_failure"
    assert result.trajectory.failures == ("ungrounded_research_failure",)
    assert len(provider.requests) == 1
    assert result.facts == ()


def test_synthesis_request_contains_grounded_bundle_and_source_ids_only() -> None:
    provider = TwoPhaseStubProvider()
    ResearchAgent(settings(), provider).run(vehicle(), ("engine.horsepower",))
    synthesis_prompt = provider.requests[1].prompt
    assert "EvidenceBundle" in synthesis_prompt
    assert "S1" in synthesis_prompt
    assert "source_ids" in synthesis_prompt
    assert "Do not use model memory" in synthesis_prompt
    assert "model.example" not in synthesis_prompt


def test_evidence_bundle_source_ids_are_deterministic_and_supports_preserved() -> None:
    execution = ModelExecution(
        provider="stub", model="gemini-3.6-flash", output_text="summary",
        events=(
            event("google_search_query", {"query": "q1"}),
            event("google_search_query", {"query": "q1"}),
            event("google_search_query", {"query": "q2"}),
            event("grounding_source", {"index": 1, "url": "https://example.test/two", "title": "Two"}),
            event("grounding_source", {"index": 0, "url": "https://example.test/one", "title": "One"}),
            event("grounding_support", {"grounding_chunk_indices": [0, 1], "segment": {"text": "support"}}),
        ),
    )
    bundle = ResearchAgent._build_evidence_bundle(vehicle(), ("engine.horsepower",), execution)
    assert bundle is not None
    assert bundle.search_queries == ("q1", "q2")
    assert [source.source_id for source in bundle.sources] == ["S1", "S2"]
    assert [str(source.url) for source in bundle.sources] == ["https://example.test/two", "https://example.test/one"]
    assert all(source.grounded_text == ("support",) for source in bundle.sources)


def test_synthesis_source_ids_resolve_and_unknown_ids_are_rejected() -> None:
    bundle = EvidenceBundle(
        vehicle=vehicle(), requested_field_ids=("engine.horsepower",), research_summary="summary",
        sources=(GroundedSource(source_id="S1", title="Source", url="https://example.test/spec"),),
    )
    valid = ProviderResearchOutput.model_validate({"facts": [{"field_id": "engine.horsepower", "value": 315, "unit": "hp", "state": FactState.KNOWN, "confidence": "high", "source_ids": ["S1"]}]})
    canonical = ResearchAgent._provider_to_canonical(valid, bundle, ("engine.horsepower",))
    assert str(canonical[0].provenance[0].source_url) == "https://example.test/spec"
    invalid = ProviderResearchOutput.model_validate({"facts": [{"field_id": "engine.horsepower", "value": 315, "unit": "hp", "state": FactState.KNOWN, "confidence": "high", "source_ids": ["S99"]}]})
    with pytest.raises(ValueError, match="unknown source ID"):
        ResearchAgent._provider_to_canonical(invalid, bundle, ("engine.horsepower",))


def test_subjective_field_is_rejected_before_provider_call() -> None:
    provider = StubProvider()
    with pytest.raises(ValueError, match="subjective"):
        ResearchAgent(settings(), provider).run(vehicle(), ("handling.steering_feel",))
    assert provider.requests == []


def test_validation_failure_before_provider_call_counts_zero_attempts() -> None:
    provider = StubProvider()
    with pytest.raises(ValueError, match="non-empty"):
        ResearchAgent(settings(), provider).run(vehicle(), ())
    assert provider.requests == []


def test_trace_excludes_secrets_and_hidden_reasoning(tmp_path: Path) -> None:
    provider = TwoPhaseStubProvider(extra_events=(event("provider_metadata", {"api_key": "secret", "thought": "hidden"}),))
    result = ResearchAgent(settings(), provider).run(vehicle(), ("engine.horsepower",), development_trace_root=tmp_path)
    trace = (tmp_path / f"{result.trajectory.trajectory_id}.json").read_text(encoding="utf-8")
    assert "secret" not in trace and '"thought"' not in trace


def test_sync_adapter_uses_sdk_create_without_background_and_retains_steps() -> None:
    captured: dict[str, Any] = {}

    class Response:
        text = "done"
        response_id = "resp-sdk"
        usage_metadata = None
        candidates = [{"grounding_metadata": {"web_search_queries": ["Apex"], "grounding_chunks": [{"web": {"uri": "https://example.test/spec", "title": "Synthetic"}}], "grounding_supports": [{"grounding_chunk_indices": [0]}]}}]

    class Models:
        @staticmethod
        def generate_content(**kwargs: Any) -> Response:
            captured.update(kwargs)
            return Response()

    class FakeClient:
        models = Models()

    request = StructuredModelRequest(model="gemini-3.7-flash", thinking_level="medium", prompt="test", response_schema={"type": "object"}, timeout_seconds=1)
    execution = GeminiModelClient(settings(), client=FakeClient()).execute(request)
    assert captured["model"] == "gemini-3.7-flash"
    assert captured["contents"] == "test"
    config = captured["config"].model_dump(exclude_none=True)
    assert config["tools"][0]["google_search"] == {}
    assert config["thinking_config"]["thinking_level"].value.lower() == "medium"
    assert config["response_mime_type"] == "application/json"
    assert config["response_json_schema"] == {"type": "object"}
    assert "response_schema" not in config
    assert execution.request_id == "resp-sdk"
    assert {item.event_type for item in execution.events} >= {"google_search_query", "grounding_source", "grounding_support", "citation"}


def test_structured_provider_schema_uses_raw_json_schema_keywords_and_keeps_search() -> None:
    captured: dict[str, Any] = {}

    class Models:
        @staticmethod
        def generate_content(**kwargs: Any) -> Any:
            captured.update(kwargs)

            class Response:
                text = '{"facts": []}'
                response_id = None
                usage_metadata = None
                candidates: list[Any] = []

            return Response()

    class FakeClient:
        models = Models()

    schema = ResearchModelOutput.model_json_schema()
    request = StructuredModelRequest(
        model="gemini-3.7-flash",
        thinking_level="medium",
        prompt="research",
        response_schema=schema,
        timeout_seconds=1,
        enable_google_search=True,
    )
    GeminiModelClient(settings(), client=FakeClient()).execute(request)
    config = captured["config"].model_dump(by_alias=True, exclude_none=True)
    raw_schema = config["responseJsonSchema"]
    assert config["responseMimeType"] == "application/json"
    assert config["tools"][0]["googleSearch"] == {}
    assert raw_schema["additionalProperties"] is False
    assert "additional_properties" not in json.dumps(raw_schema)
    assert raw_schema["properties"]["facts"]["items"]["$ref"] == "#/$defs/FactResult"


def test_minimal_sync_request_omits_tools_schema_and_thinking_configuration() -> None:
    captured: dict[str, Any] = {}

    class Models:
        @staticmethod
        def generate_content(**kwargs: Any) -> Any:
            captured.update(kwargs)
            class Response:
                text = "2024 Honda Civic Type R"
                response_id = None
                usage_metadata = None
                candidates: list[Any] = []
            return Response()

    class FakeClient:
        models = Models()

    request = StructuredModelRequest(model="gemini-3.7-flash", prompt="Return exactly: 2024 Honda Civic Type R", timeout_seconds=1, thinking_level=None, enable_google_search=False)
    GeminiModelClient(settings(), client=FakeClient()).execute(request)
    assert captured["model"] == "gemini-3.7-flash"
    assert captured["contents"] == "Return exactly: 2024 Honda Civic Type R"
    assert captured["config"] is None


def test_sync_adapter_preserves_sanitized_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "never-serialize"
    monkeypatch.setenv("GEMINI_API_KEY", secret)

    class Error(RuntimeError):
        status_code = 403
        message = f"Authorization: Bearer {secret}"

    class Models:
        @staticmethod
        def generate_content(**kwargs: Any) -> dict[str, Any]:
            raise Error("denied")

    class FakeClient:
        models = Models()

    with pytest.raises(ModelProviderError) as caught:
        GeminiModelClient(settings(), client=FakeClient()).execute(StructuredModelRequest(model="gemini-3.7-flash", thinking_level="medium", prompt="test", timeout_seconds=1, enable_google_search=False))
    assert caught.value.diagnostic is not None
    assert caught.value.diagnostic.request_stage == "generate_content"
    assert secret not in caught.value.diagnostic.provider_message


def test_missing_key_fails_before_sdk_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(MissingGeminiApiKeyError):
        GeminiModelClient(settings()).execute(StructuredModelRequest(model="gemini-3.7-flash", thinking_level="medium", prompt="test", timeout_seconds=1, enable_google_search=False))


def test_worker_receives_validated_request_and_returns_sanitized_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_execute(self: GeminiModelClient, request: StructuredModelRequest) -> ModelExecution:
        captured["request"] = request
        return ModelExecution(provider="gemini", model="gemini-3.7-flash", request_id="int-worker", status="completed", output_text="done")

    monkeypatch.setattr(sync_worker.GeminiModelClient, "execute", fake_execute)
    envelope = sync_worker.run_payload({"settings": settings().model_dump(mode="json"), "request": StructuredModelRequest(model="gemini-3.7-flash", thinking_level="medium", prompt="test", timeout_seconds=1, enable_google_search=False).model_dump(mode="json")})
    assert envelope["status"] == "completed"
    assert captured["request"].prompt == "test"


class FakeProcess:
    def __init__(self, stdout: str | None = None, timeout: bool = False) -> None:
        self.stdout = stdout or ""
        self.timeout = timeout
        self.terminated = False
        self.killed = False
        self.calls = 0

    def communicate(self, input: str | None = None, timeout: float | None = None) -> tuple[str, str]:
        self.calls += 1
        if self.timeout and self.calls == 1:
            raise subprocess.TimeoutExpired("worker", timeout)
        return self.stdout, ""

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True


def test_parent_protocol_uses_stdin_not_key_command_line_and_receives_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "worker-secret")
    process = FakeProcess(json.dumps({"status": "completed", "execution": ModelExecution(provider="gemini", model="gemini-3.7-flash", request_id="int-child", status="completed", output_text="done", latency_ms=10).model_dump(mode="json")}))
    captured: dict[str, Any] = {}

    def fake_popen(command: list[str], **kwargs: Any) -> FakeProcess:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return process

    execution = IsolatedGeminiWorkerProvider(settings(), popen=fake_popen).execute(StructuredModelRequest(model="gemini-3.7-flash", thinking_level="medium", prompt="test", timeout_seconds=1, enable_google_search=False))
    assert execution.request_id == "int-child"
    assert "worker-secret" not in " ".join(captured["command"])
    assert "worker-secret" not in captured["kwargs"].get("args", [])
    assert captured["kwargs"]["env"]["GEMINI_API_KEY"] == "worker-secret"
    assert execution.provider_latency_ms == 10


def test_parent_deadline_terminates_worker_without_orphan() -> None:
    process = FakeProcess(timeout=True)
    provider = IsolatedGeminiWorkerProvider(settings(), popen=lambda *args, **kwargs: process)
    with pytest.raises(WorkerDeadlineExceededError):
        provider.execute(StructuredModelRequest(model="gemini-3.7-flash", thinking_level="medium", prompt="test", timeout_seconds=1, enable_google_search=False))
    assert process.terminated is True
    assert process.calls == 2


def test_parent_handles_malformed_or_provider_error_worker_envelopes() -> None:
    request = StructuredModelRequest(model="gemini-3.7-flash", thinking_level="medium", prompt="test", timeout_seconds=1, enable_google_search=False)
    malformed = IsolatedGeminiWorkerProvider(settings(), popen=lambda *args, **kwargs: FakeProcess("not-json"))
    provider_error = IsolatedGeminiWorkerProvider(settings(), popen=lambda *args, **kwargs: FakeProcess(json.dumps({"status": "provider_error", "error": {"normalized_error": "safe failure"}})))
    with pytest.raises(ModelProviderError, match="malformed"):
        malformed.execute(request)
    with pytest.raises(ModelProviderError, match="provider_error"):
        provider_error.execute(request)


def test_research_source_does_not_import_frozen_ground_truth() -> None:
    source_root = Path(__file__).parents[2] / "src" / "enthusiast_lens" / "research"
    assert "ground_truth" not in "\n".join(path.read_text(encoding="utf-8") for path in source_root.glob("*.py"))
