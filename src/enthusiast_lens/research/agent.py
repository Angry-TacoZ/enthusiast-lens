"""Evidence-first, two-phase V1 research/reconciliation agent."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from enthusiast_lens.model import (
    IsolatedGeminiWorkerProvider,
    ModelEvent,
    ModelExecution,
    ModelProvider,
    ModelProviderError,
    ModelUsage,
    StructuredModelRequest,
    WorkerDeadlineExceededError,
    sanitize_for_trace,
    utc_now,
)
from enthusiast_lens.model.gemini import GeminiSettings
from enthusiast_lens.models import (
    AnalysisRunMetadata,
    ConfigurationMatch,
    Confidence,
    EvidenceRelationship,
    FactResult,
    FactState,
    OriginType,
    Provenance,
    RunMode,
    RunStatus,
    SourceType,
    VehicleContext,
)

from .evidence import EvidenceBundle, GroundedSource, ProviderResearchOutput
from .instructions import INSTRUCTION_VERSION, instruction_hash, system_instruction_text
from .result import ResearchRunResult, ResearchTrajectory, write_development_trace


SUBJECTIVE_FIELD_TERMS = ("feel", "fun", "best", "worst", "beautiful", "desirable", "opinion")


class ResearchAgent:
    """Acquire grounded evidence, then synthesize once from that evidence."""

    def __init__(
        self,
        settings: GeminiSettings | None = None,
        provider: ModelProvider | None = None,
    ) -> None:
        self.settings = settings or GeminiSettings.from_environment()
        self.provider = provider
        self._uses_default_provider = provider is None

    def run(
        self,
        vehicle: VehicleContext,
        requested_field_ids: tuple[str, ...],
        *,
        development_trace_root: Path | None = None,
    ) -> ResearchRunResult:
        """Run evidence acquisition and evidence-constrained synthesis once each."""

        self._validate_requested_fields(requested_field_ids)
        started_at = utc_now()
        trajectory_id = f"research-{uuid4()}"
        events: list[ModelEvent] = []
        failures: list[str] = []
        facts: tuple[FactResult, ...] = ()
        warnings: tuple[str, ...] = ()
        configuration_notes: tuple[str, ...] = ()
        phase_a_execution: ModelExecution | None = None
        phase_b_execution: ModelExecution | None = None
        attempted_model_calls = 0
        phase_a_latency_ms: int | None = None
        phase_b_latency_ms: int | None = None
        phase_a_usage = ModelUsage()
        phase_b_usage = ModelUsage()
        evidence_bundle: EvidenceBundle | None = None

        phase_a_settings = self.settings.model_copy(update={"wall_clock_deadline_seconds": 45})
        phase_b_settings = self.settings.model_copy(update={"wall_clock_deadline_seconds": 30})

        def append(event_type: str, details: dict[str, object]) -> None:
            events.append(
                ModelEvent(
                    sequence=len(events) + 1,
                    event_type=event_type,
                    observed_at=utc_now(),
                    details=sanitize_for_trace(details),
                )
            )

        def snapshot(status: str) -> ResearchTrajectory:
            return ResearchTrajectory(
                trajectory_id=trajectory_id,
                started_at=started_at,
                completed_at=utc_now(),
                status=status,
                provider="gemini",
                model=self.settings.model,
                thinking_level=self.settings.thinking_level,
                instruction_version=INSTRUCTION_VERSION,
                instruction_sha256=instruction_hash(),
                vehicle=vehicle,
                requested_field_ids=requested_field_ids,
                interaction_id=(
                    phase_b_execution.request_id
                    if phase_b_execution is not None
                    else phase_a_execution.request_id if phase_a_execution is not None else None
                ),
                last_provider_status=(
                    phase_b_execution.status
                    if phase_b_execution is not None
                    else phase_a_execution.status if phase_a_execution is not None else None
                ),
                elapsed_ms=self._sum_known(phase_a_latency_ms, phase_b_latency_ms),
                phase_a_latency_ms=phase_a_latency_ms,
                phase_b_latency_ms=phase_b_latency_ms,
                phase_a_usage=phase_a_usage,
                phase_b_usage=phase_b_usage,
                search_query_count=len(evidence_bundle.search_queries) if evidence_bundle else 0,
                grounded_source_count=len(evidence_bundle.sources) if evidence_bundle else 0,
                evidence_bundle=evidence_bundle,
                events=tuple(events),
                usage=self._combine_usage(phase_a_usage, phase_b_usage),
                model_call_count=attempted_model_calls,
                retry_count=0,
                failures=tuple(failures),
            )

        def finish(status: str, run_status: RunStatus) -> ResearchRunResult:
            return self._finish(snapshot(status), facts, warnings, configuration_notes, run_status, development_trace_root)

        append(
            "research_started",
            {
                "execution_mode": "synchronous_isolated_worker",
                "phase_a_parent_deadline_seconds": phase_a_settings.wall_clock_deadline_seconds,
                "phase_b_parent_deadline_seconds": phase_b_settings.wall_clock_deadline_seconds,
                "max_model_calls": self.settings.max_model_calls,
                "max_search_calls": self.settings.max_search_calls,
            },
        )
        append(
            "evidence_acquisition_started",
            {
                "model": self.settings.model,
                "google_search_enabled": True,
                "structured_output_enabled": False,
                "requested_field_ids": requested_field_ids,
            },
        )
        phase_a_request = StructuredModelRequest(
            model=self.settings.model,
            prompt=self._evidence_prompt(vehicle, requested_field_ids),
            timeout_seconds=phase_a_settings.request_timeout_seconds,
            thinking_level=None,
            system_instruction=None,
            response_schema=None,
            enable_google_search=True,
        )
        append(
            "evidence_acquisition_request",
            {
                "model": phase_a_request.model,
                "prompt": phase_a_request.prompt,
                "google_search_enabled": phase_a_request.enable_google_search,
                "timeout_seconds": phase_a_request.timeout_seconds,
            },
        )
        try:
            attempted_model_calls += 1
            phase_a_execution = self._provider_for(phase_a_settings).execute(phase_a_request)
            phase_a_latency_ms = phase_a_execution.latency_ms
            phase_a_usage = phase_a_execution.usage
        except WorkerDeadlineExceededError as error:
            failures.append("phase_a_deadline_exceeded")
            append("evidence_acquisition_failure", self._provider_error_details(error))
            return finish("failed", RunStatus.FAILED)
        except ModelProviderError as error:
            failures.append(str(error))
            append("evidence_acquisition_failure", self._provider_error_details(error))
            return finish("failed", RunStatus.FAILED)

        self._append_provider_events(events, phase_a_execution, phase="evidence_acquisition")
        append(
            "evidence_acquisition_completed",
            {
                "provider_status": phase_a_execution.status or "unknown",
                "provider_latency_ms": phase_a_execution.provider_latency_ms or phase_a_execution.latency_ms,
                "worker_latency_ms": phase_a_execution.latency_ms,
                "search_query_count": sum(event.event_type == "google_search_query" for event in phase_a_execution.events),
                "grounded_source_count": sum(event.event_type == "grounding_source" for event in phase_a_execution.events),
                "usage": phase_a_execution.usage.model_dump(mode="json"),
            },
        )
        evidence_bundle = self._build_evidence_bundle(vehicle, requested_field_ids, phase_a_execution)
        if evidence_bundle is None:
            failures.append("ungrounded_research_failure")
            append(
                "ungrounded_research_failure",
                {"reason": "provider exposed zero grounded sources", "model_written_urls_accepted": False},
            )
            return finish("ungrounded_research_failure", RunStatus.FAILED)
        append(
            "evidence_bundle_created",
            {
                "source_ids": [source.source_id for source in evidence_bundle.sources],
                "search_queries": evidence_bundle.search_queries,
                "grounded_source_count": len(evidence_bundle.sources),
            },
        )

        append(
            "synthesis_started",
            {
                "model": self.settings.model,
                "google_search_enabled": False,
                "structured_output_enabled": True,
                "source_ids_supplied": [source.source_id for source in evidence_bundle.sources],
            },
        )
        phase_b_request = StructuredModelRequest(
            model=self.settings.model,
            prompt=self._synthesis_prompt(vehicle, requested_field_ids, evidence_bundle),
            timeout_seconds=phase_b_settings.request_timeout_seconds,
            thinking_level=self.settings.thinking_level,
            system_instruction=system_instruction_text(),
            response_schema=ProviderResearchOutput.model_json_schema(),
            enable_google_search=False,
        )
        append(
            "synthesis_request",
            {
                "model": phase_b_request.model,
                "thinking_level": phase_b_request.thinking_level,
                "google_search_enabled": phase_b_request.enable_google_search,
                "response_schema_mode": "response_json_schema",
                "timeout_seconds": phase_b_request.timeout_seconds,
                "source_ids_supplied": [source.source_id for source in evidence_bundle.sources],
            },
        )
        try:
            attempted_model_calls += 1
            phase_b_execution = self._provider_for(phase_b_settings).execute(phase_b_request)
            phase_b_latency_ms = phase_b_execution.latency_ms
            phase_b_usage = phase_b_execution.usage
        except WorkerDeadlineExceededError as error:
            failures.append("phase_b_deadline_exceeded")
            append("synthesis_failure", self._provider_error_details(error))
            return finish("failed", RunStatus.FAILED)
        except ModelProviderError as error:
            failures.append(str(error))
            append("synthesis_failure", self._provider_error_details(error))
            return finish("failed", RunStatus.FAILED)

        self._append_provider_events(events, phase_b_execution, phase="synthesis")
        append(
            "synthesis_completed",
            {
                "provider_status": phase_b_execution.status or "unknown",
                "provider_latency_ms": phase_b_execution.provider_latency_ms or phase_b_execution.latency_ms,
                "worker_latency_ms": phase_b_execution.latency_ms,
                "usage": phase_b_execution.usage.model_dump(mode="json"),
            },
        )
        if (phase_b_execution.status or "completed").casefold() != "completed" or not phase_b_execution.output_text:
            failures.append("synthesis_missing_structured_output")
            append("synthesis_output_invalid", {"error": "missing structured output"})
            return finish("failed", RunStatus.FAILED)
        try:
            parsed = ProviderResearchOutput.model_validate_json(phase_b_execution.output_text)
            facts = self._provider_to_canonical(parsed, evidence_bundle, requested_field_ids)
            warnings = parsed.warnings
            configuration_notes = parsed.configuration_notes
            append("canonical_output_validated", {"fact_count": len(facts), "source_ids_resolved": True})
        except (ValidationError, ValueError) as error:
            failure = f"structured_output_invalid: {str(error).splitlines()[0]}"
            failures.append(failure)
            append("synthesis_output_invalid", {"error": failure})
            return finish("failed", RunStatus.FAILED)
        append("research_completed", {"fact_count": len(facts), "model_call_count": 2})
        return finish("succeeded", RunStatus.SUCCEEDED)

    def _provider_for(self, settings: GeminiSettings) -> ModelProvider:
        if self._uses_default_provider:
            return IsolatedGeminiWorkerProvider(settings)
        assert self.provider is not None
        return self.provider

    @staticmethod
    def _sum_known(*values: int | None) -> int | None:
        if not values:
            return None
        known = [value for value in values if value is not None]
        return sum(known) if known else None

    @staticmethod
    def _combine_usage(*usages: ModelUsage) -> ModelUsage:
        def total(field: str) -> int | None:
            values = [getattr(usage, field) for usage in usages]
            return sum(values) if all(value is not None for value in values) else None

        costs = [usage.estimated_cost_usd for usage in usages]
        estimated_cost = sum(costs) if all(cost is not None for cost in costs) else None
        return ModelUsage(
            input_tokens=total("input_tokens"),
            output_tokens=total("output_tokens"),
            thinking_tokens=total("thinking_tokens"),
            tool_use_tokens=total("tool_use_tokens"),
            total_tokens=total("total_tokens"),
            estimated_cost_usd=estimated_cost,
            pricing_note="Aggregated across evidence acquisition and synthesis phases."
            if estimated_cost is not None
            else None,
        )

    @staticmethod
    def _build_evidence_bundle(
        vehicle: VehicleContext,
        requested_field_ids: tuple[str, ...],
        execution: ModelExecution,
    ) -> EvidenceBundle | None:
        queries: list[str] = []
        query_seen: set[str] = set()
        source_records: dict[int, dict[str, object]] = {}
        support_records: dict[int, list[dict[str, object]]] = {}
        for event in execution.events:
            details = event.details
            if event.event_type == "google_search_query":
                query = details.get("query")
                if isinstance(query, str) and query and query not in query_seen:
                    query_seen.add(query)
                    queries.append(query)
            elif event.event_type == "grounding_source":
                index = details.get("index")
                url = details.get("url")
                if isinstance(index, int) and isinstance(url, str) and url:
                    source_records[index] = {
                        "url": url,
                        "title": details.get("title") if isinstance(details.get("title"), str) else None,
                    }
            elif event.event_type == "grounding_support":
                indices = details.get("grounding_chunk_indices")
                if isinstance(indices, list):
                    for index in indices:
                        if isinstance(index, int):
                            support_records.setdefault(index, []).append(dict(details))
        if not source_records:
            return None
        sources: list[GroundedSource] = []
        for source_index, record in source_records.items():
            support_details = tuple(support_records.get(source_index, ()))
            grounded_text = tuple(
                segment["text"]
                for detail in support_details
                if isinstance(detail.get("segment"), dict)
                for segment in (detail["segment"],)
                if isinstance(segment.get("text"), str) and segment["text"]
            )
            try:
                sources.append(
                    GroundedSource(
                        source_id=f"S{len(sources) + 1}",
                        title=record.get("title"),
                        url=record["url"],
                        grounded_text=grounded_text,
                        support_details=support_details,
                    )
                )
            except ValidationError:
                continue
        if not sources:
            return None
        return EvidenceBundle(
            vehicle=vehicle,
            requested_field_ids=requested_field_ids,
            research_summary=execution.output_text or "Grounding metadata returned without a summary.",
            sources=tuple(sources),
            search_queries=tuple(queries),
            usage=execution.usage,
            latency_ms=execution.latency_ms,
        )

    def _evidence_prompt(self, vehicle: VehicleContext, requested_field_ids: tuple[str, ...]) -> str:
        context = json.dumps(vehicle.model_dump(mode="json", exclude_none=True), sort_keys=True)
        fields = json.dumps(list(requested_field_ids))
        return (
            "Use Google Search to research the exact vehicle configuration below.\n"
            "Find external evidence for each requested fact. Do not rely only on model memory.\n"
            f"Vehicle context: {context}\nRequested facts: {fields}\n"
            "Return a concise research summary based on the web evidence."
        )

    @staticmethod
    def _synthesis_prompt(vehicle: VehicleContext, requested_field_ids: tuple[str, ...], evidence_bundle: EvidenceBundle) -> str:
        bundle = evidence_bundle.model_dump(mode="json", exclude={"usage", "latency_ms"})
        return (
            "Synthesize the requested facts using ONLY the supplied grounded EvidenceBundle. "
            "Do not use model memory for researched values, do not invent URLs, and reference evidence "
            "only with the provided source_ids. If evidence is insufficient, return state=unknown with "
            "a null value and no fabricated provenance.\n"
            f"Vehicle context: {json.dumps(vehicle.model_dump(mode='json', exclude_none=True), sort_keys=True)}\n"
            f"Requested facts: {json.dumps(list(requested_field_ids))}\n"
            f"EvidenceBundle: {json.dumps(bundle, sort_keys=True)}"
        )

    @staticmethod
    def _provider_to_canonical(
        output: ProviderResearchOutput,
        bundle: EvidenceBundle,
        requested_field_ids: tuple[str, ...],
    ) -> tuple[FactResult, ...]:
        source_by_id = {source.source_id: source for source in bundle.sources}
        output_ids = [fact.field_id for fact in output.facts]
        if len(output_ids) != len(set(output_ids)) or set(output_ids) != set(requested_field_ids):
            raise ValueError("model did not return exactly the requested field IDs")
        facts: list[FactResult] = []
        for provider_fact in output.facts:
            if set(provider_fact.source_ids) & set(provider_fact.conflict_source_ids):
                raise ValueError("a source ID cannot be both supporting and conflicting")
            for source_id in (*provider_fact.source_ids, *provider_fact.conflict_source_ids):
                if source_id not in source_by_id:
                    raise ValueError(f"provider returned unknown source ID: {source_id}")
            if provider_fact.state is FactState.KNOWN and not provider_fact.source_ids:
                raise ValueError("known facts require supporting source IDs")
            if provider_fact.state is FactState.CONFLICTED and not provider_fact.conflict_source_ids:
                raise ValueError("conflicted facts require conflicting source IDs")
            provenance = [
                ResearchAgent._provenance_for(
                    source_by_id[source_id],
                    provider_fact.confidence,
                    EvidenceRelationship.SUPPORTS if provider_fact.state is FactState.KNOWN else EvidenceRelationship.CONTEXT,
                )
                for source_id in provider_fact.source_ids
            ]
            provenance.extend(
                ResearchAgent._provenance_for(
                    source_by_id[source_id], provider_fact.confidence, EvidenceRelationship.CONFLICTS
                )
                for source_id in provider_fact.conflict_source_ids
            )
            facts.append(
                FactResult(
                    field_id=provider_fact.field_id,
                    value=provider_fact.value,
                    unit=provider_fact.unit,
                    state=provider_fact.state,
                    confidence=provider_fact.confidence,
                    provenance=tuple(provenance),
                    configuration_dependency_notes=provider_fact.configuration_dependency_notes,
                    conflict_information=provider_fact.conflict_information,
                    origin=OriginType.RESEARCHED,
                )
            )
        return tuple(facts)

    @staticmethod
    def _provenance_for(source: GroundedSource, confidence: Confidence | None, relationship: EvidenceRelationship) -> Provenance:
        notes = " ".join(source.grounded_text) if source.grounded_text else None
        return Provenance(
            source_url=source.url,
            publisher=source.title,
            source_type=SourceType.SECONDARY_SOURCE,
            configuration_match=ConfigurationMatch.UNKNOWN,
            origin=OriginType.RESEARCHED,
            confidence=confidence,
            notes=notes,
            relationship=relationship,
        )

    def _finish(
        self,
        trajectory: ResearchTrajectory,
        facts: tuple[FactResult, ...],
        warnings: tuple[str, ...],
        configuration_notes: tuple[str, ...],
        status: RunStatus,
        development_trace_root: Path | None,
    ) -> ResearchRunResult:
        # Keep the trajectory's phase-specific status (for example,
        # ``ungrounded_research_failure``) distinct from the canonical run
        # status used by AnalysisRunMetadata.
        completed = trajectory.model_copy(update={"completed_at": utc_now()})
        if development_trace_root is not None:
            write_development_trace(completed, development_trace_root)
        analysis = AnalysisRunMetadata(
            run_id=completed.trajectory_id,
            mode=RunMode.FULL_WEB,
            started_at=completed.started_at,
            completed_at=completed.completed_at,
            status=status,
            input_context=completed.vehicle,
            model_call_count=completed.model_call_count,
            tool_call_count=sum(1 for event in completed.events if event.event_type == "google_search_query"),
            web_search_count=completed.search_query_count,
            latency_ms=completed.elapsed_ms,
            estimated_cost_usd=completed.usage.estimated_cost_usd,
            unknown_count=sum(1 for fact in facts if fact.state is FactState.UNKNOWN),
            retry_count=0,
            failures=completed.failures,
            event_references=(f"trajectory://{completed.trajectory_id}",),
        )
        return ResearchRunResult(
            facts=facts,
            warnings=warnings,
            configuration_notes=configuration_notes,
            trajectory=completed,
            analysis=analysis,
        )

    @staticmethod
    def _validate_requested_fields(requested_field_ids: tuple[str, ...]) -> None:
        if not requested_field_ids or len(requested_field_ids) != len(set(requested_field_ids)):
            raise ValueError("requested_field_ids must be non-empty and unique")
        if any(any(term in field_id.casefold() for term in SUBJECTIVE_FIELD_TERMS) for field_id in requested_field_ids):
            raise ValueError("subjective field IDs are not valid research targets")

    @staticmethod
    def _append_provider_events(events: list[ModelEvent], execution: ModelExecution, *, phase: str) -> None:
        for provider_event in execution.events:
            details = dict(sanitize_for_trace(provider_event.details))
            details["phase"] = phase
            events.append(provider_event.model_copy(update={"sequence": len(events) + 1, "details": details}))

    @staticmethod
    def _provider_error_details(error: ModelProviderError) -> dict[str, object]:
        details: dict[str, object] = {"error": str(error)}
        if error.diagnostic is not None:
            details["provider_diagnostic"] = error.diagnostic.model_dump(mode="json")
        return details
