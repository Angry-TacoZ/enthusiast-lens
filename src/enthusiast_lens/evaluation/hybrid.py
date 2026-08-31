"""vPIC-first Hybrid benchmark runner; Gemini execution requires ``--live``."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from enthusiast_lens.adapters import VPICClient
from enthusiast_lens.deterministic import canonicalize_string, parse_numeric
from enthusiast_lens.model import GeminiSettings, ModelProvider
from enthusiast_lens.models import FactResult, FactState, OriginType, RunMode, RunStatus
from enthusiast_lens.models.benchmark_input import BenchmarkInput
from enthusiast_lens.models.structured_seed import (
    StructuredFactState,
    StructuredSeedFact,
    StructuredVehicleSeed,
)
from enthusiast_lens.research import ResearchAgent
from enthusiast_lens.research.agent import (
    PHASE_A_MAX_FIELDS_PER_BATCH,
    PHASE_B_MAX_FIELDS_PER_BATCH,
)

from .field_catalog import DEFAULT_FIELD_CATALOG_PATH, field_catalog_hash, load_field_catalog
from .full_web import (
    DEFAULT_INPUTS_PATH,
    BaselineResult,
    FullWebBaselineRunner,
    _load_inputs_only,
)


SYSTEM_VERSION = "hybrid-vpic-web-v2"
DEFAULT_OUTPUT_ROOT = Path("artifacts/evals/hybrid")

DRIVETRAIN_LAYOUTS = {
    "rwd": "RWD",
    "rear-wheel drive": "RWD",
    "rear-wheel drive (rwd)": "RWD",
    "fwd": "FWD",
    "front-wheel drive": "FWD",
    "front-wheel drive (fwd)": "FWD",
    "awd": "AWD",
    "all-wheel drive": "AWD",
    "all-wheel drive (awd)": "AWD",
    "4wd": "4WD",
    "four-wheel drive": "4WD",
    "four-wheel drive (4wd)": "4WD",
    "4x4": "4WD",
}
ENGINE_LAYOUTS = {
    "in-line": "inline",
    "inline": "inline",
    "straight": "inline",
    "v-shaped": "V",
    "v": "V",
    "horizontal": "flat",
    "flat": "flat",
}


@dataclass(frozen=True)
class VPICSeedMapping:
    """One deterministic, exact-VIN vPIC-to-canonical seed rule."""

    field_id: str
    provider_fields: tuple[str, ...]
    unit: str | None
    normalize: Callable[[Mapping[str, StructuredSeedFact]], object | None]


def _positive_number(value: object) -> int | float | None:
    try:
        parsed = parse_numeric(value)
    except (TypeError, ValueError):
        return None
    if parsed is None or parsed <= 0:
        return None
    return int(parsed) if parsed == parsed.to_integral_value() else float(parsed)


def _positive_integer(value: object) -> int | None:
    numeric = _positive_number(value)
    if numeric is None or isinstance(numeric, float):
        return None
    return numeric


def _engine_configuration(facts: Mapping[str, StructuredSeedFact]) -> str | None:
    layout = ENGINE_LAYOUTS.get(
        canonicalize_string(str(facts["EngineConfiguration"].normalized_value)) or ""
    )
    cylinders = _positive_integer(facts["EngineCylinders"].normalized_value)
    if layout is None or cylinders is None:
        return None
    return f"{layout} {cylinders}-cylinder"


def _drivetrain_layout(facts: Mapping[str, StructuredSeedFact]) -> str | None:
    return DRIVETRAIN_LAYOUTS.get(
        canonicalize_string(str(facts["DriveType"].normalized_value)) or ""
    )


VPIC_SEED_MAPPINGS: tuple[VPICSeedMapping, ...] = (
    VPICSeedMapping(
        "engine_and_measured_performance.displacement_cc",
        ("DisplacementCC",),
        "cc",
        lambda facts: _positive_number(facts["DisplacementCC"].normalized_value),
    ),
    VPICSeedMapping(
        "engine_and_measured_performance.horsepower",
        ("EngineHP",),
        "hp",
        lambda facts: _positive_number(facts["EngineHP"].normalized_value),
    ),
    VPICSeedMapping(
        "engine_and_measured_performance.engine_configuration",
        ("EngineConfiguration", "EngineCylinders"),
        None,
        _engine_configuration,
    ),
    VPICSeedMapping(
        "engine_and_measured_performance.curb_weight",
        ("CurbWeightLB",),
        "lb",
        lambda facts: _positive_number(facts["CurbWeightLB"].normalized_value),
    ),
    VPICSeedMapping(
        "transmission.gear_count",
        ("TransmissionSpeeds",),
        None,
        lambda facts: _positive_integer(facts["TransmissionSpeeds"].normalized_value),
    ),
    VPICSeedMapping(
        "drivetrain_and_differentials.layout",
        ("DriveType",),
        None,
        _drivetrain_layout,
    ),
)


def _reported_provider_facts(seed: StructuredVehicleSeed) -> dict[str, StructuredSeedFact]:
    relevant = {
        field for mapping in VPIC_SEED_MAPPINGS for field in mapping.provider_fields
    }
    facts: dict[str, StructuredSeedFact] = {}
    for fact in seed.facts:
        if fact.provider_field not in relevant:
            continue
        if fact.provider_field in facts:
            raise ValueError(f"duplicate vPIC provider field: {fact.provider_field}")
        facts[fact.provider_field] = fact
    return facts


class HybridDryRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    fixture_id: str
    total_canonical_fields: int
    potential_vpic_seed_field_count: int
    maximum_research_field_count: int
    max_model_calls: int
    vpic_seed_count_note: str


def _seeds(seed: StructuredVehicleSeed) -> tuple[FactResult, ...]:
    provider_facts = _reported_provider_facts(seed)
    seeds: list[FactResult] = []
    for mapping in VPIC_SEED_MAPPINGS:
        selected = {
            field: provider_facts.get(field) for field in mapping.provider_fields
        }
        if any(
            fact is None
            or fact.state is not StructuredFactState.REPORTED
            or fact.normalized_value is None
            for fact in selected.values()
        ):
            continue
        value = mapping.normalize(selected)  # type: ignore[arg-type]
        if value is None:
            continue
        seeds.append(
            FactResult(
                field_id=mapping.field_id,
                value=value,
                unit=mapping.unit,
                state=FactState.KNOWN,
                provenance=tuple(fact.provenance for fact in selected.values()),
                origin=OriginType.STRUCTURED,
            )
        )
    if len({fact.field_id for fact in seeds}) != len(seeds):
        raise ValueError("duplicate vPIC canonical seed")
    return tuple(seeds)


class HybridRunner:
    def __init__(
        self,
        *,
        inputs_path: Path = DEFAULT_INPUTS_PATH,
        field_catalog_path: Path = DEFAULT_FIELD_CATALOG_PATH,
        output_root: Path = DEFAULT_OUTPUT_ROOT,
        settings: GeminiSettings | None = None,
        vpic_client: VPICClient | None = None,
        provider_factory: Callable[[BenchmarkInput], ModelProvider | None] | None = None,
    ):
        self.corpus = _load_inputs_only(inputs_path)
        self.catalog = load_field_catalog(field_catalog_path)
        self.catalog_hash = field_catalog_hash(field_catalog_path)
        self.output_root = output_root
        self.settings = settings or GeminiSettings.from_environment()
        self.vpic = vpic_client or VPICClient()
        self.provider_factory = provider_factory

    def select(self, fixture_id: str) -> BenchmarkInput:
        return next(item for item in self.corpus.inputs if item.fixture_id == fixture_id)

    def dry_run(self, item: BenchmarkInput) -> HybridDryRun:
        target_count = len(self.catalog.agent_research_field_ids)
        batch_count = (target_count + PHASE_A_MAX_FIELDS_PER_BATCH - 1) // PHASE_A_MAX_FIELDS_PER_BATCH
        return HybridDryRun(
            fixture_id=item.fixture_id,
            total_canonical_fields=len(self.catalog.field_ids),
            potential_vpic_seed_field_count=len(VPIC_SEED_MAPPINGS),
            maximum_research_field_count=target_count,
            max_model_calls=batch_count * 2,
            vpic_seed_count_note="Potential only; exact seeds require a live vPIC decode.",
        )

    def targets(self, seed: StructuredVehicleSeed) -> tuple[str, ...]:
        seeded_ids = {fact.field_id for fact in _seeds(seed)}
        return tuple(
            field_id
            for field_id in self.catalog.agent_research_field_ids
            if field_id not in seeded_ids
        )

    def _result_path(self, item: BenchmarkInput) -> Path:
        return self.output_root / item.fixture_id / "result.json"

    def run(
        self,
        item: BenchmarkInput,
        *,
        live: bool = False,
        retry_failed: bool = False,
    ) -> BaselineResult | None:
        if not live:
            raise ValueError("paid execution requires live=True")
        path = self._result_path(item)
        if path.is_file():
            existing = BaselineResult.model_validate_json(path.read_text(encoding="utf-8"))
            if existing.status is RunStatus.SUCCEEDED:
                return None
            if not retry_failed:
                return existing
            path.replace(FullWebBaselineRunner._archive_path(path))
        return self.run_fixture(item)

    def run_fixture(self, item: BenchmarkInput) -> BaselineResult:
        if not item.vehicle.vin:
            raise ValueError("Hybrid requires exact VIN")
        started = datetime.now(UTC)
        fixture_dir = self.output_root / item.fixture_id
        seed = self.vpic.decode_vin(item.vehicle.vin, item.vehicle.year)
        seeded = _seeds(seed)
        targets = self.targets(seed)
        agent = ResearchAgent(
            settings=self.settings,
            provider=self.provider_factory(item) if self.provider_factory else None,
        )
        research = agent.run(
            item.vehicle,
            targets,
            development_trace_root=fixture_dir / "trajectory",
        )
        researched = {fact.field_id: fact for fact in research.facts}
        seeded_ids = {fact.field_id for fact in seeded}
        if research.analysis.status is not RunStatus.SUCCEEDED:
            result = BaselineResult(
                system_version=SYSTEM_VERSION,
                fixture_id=item.fixture_id,
                vehicle_family_id=item.vehicle_family_id,
                vehicle=item.vehicle,
                run_mode=RunMode.HYBRID,
                model=research.trajectory.model,
                instruction_version=research.trajectory.instruction_version,
                instruction_sha256=research.trajectory.instruction_sha256,
                field_catalog_version=self.catalog.catalog_version,
                field_catalog_sha256=self.catalog_hash,
                started_at=started,
                completed_at=research.trajectory.completed_at,
                status=research.analysis.status,
                requested_field_ids=targets,
                canonical_field_ids=self.catalog.field_ids,
                facts=tuple(seeded) + research.facts,
                warnings=research.warnings,
                configuration_notes=research.configuration_notes,
                model_call_count=research.trajectory.model_call_count,
                search_query_count=research.trajectory.search_query_count,
                grounded_source_count=research.trajectory.grounded_source_count,
                input_tokens=research.trajectory.usage.input_tokens,
                output_tokens=research.trajectory.usage.output_tokens,
                thinking_tokens=research.trajectory.usage.thinking_tokens,
                total_tokens=research.trajectory.usage.total_tokens,
                estimated_cost_usd=research.trajectory.usage.estimated_cost_usd,
                latency_ms=research.trajectory.elapsed_ms,
                retry_count=research.trajectory.retry_count,
                failures=research.trajectory.failures,
                trajectory_path=str(
                    fixture_dir / "trajectory" / f"{research.trajectory.trajectory_id}.json"
                ),
            )
            path = fixture_dir / "result.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
            return result

        if seeded_ids & set(researched):
            raise ValueError("duplicate seeded and researched canonical field")
        if set(researched) != set(targets):
            raise ValueError("researched facts missing or outside requested targets")
        ordered = tuple(
            next((fact for fact in seeded if fact.field_id == field_id), None)
            or researched[field_id]
            for field_id in self.catalog.agent_research_field_ids
        )
        derived = FullWebBaselineRunner._append_deterministic_facts(self, ordered)
        if len(ordered) != len(self.catalog.agent_research_field_ids) or len(derived) != len(
            self.catalog.field_ids
        ):
            raise ValueError("successful Hybrid canonical field invariant failed")
        result = BaselineResult(
            system_version=SYSTEM_VERSION,
            fixture_id=item.fixture_id,
            vehicle_family_id=item.vehicle_family_id,
            vehicle=item.vehicle,
            run_mode=RunMode.HYBRID,
            model=research.trajectory.model,
            instruction_version=research.trajectory.instruction_version,
            instruction_sha256=research.trajectory.instruction_sha256,
            field_catalog_version=self.catalog.catalog_version,
            field_catalog_sha256=self.catalog_hash,
            started_at=started,
            completed_at=research.trajectory.completed_at,
            status=research.analysis.status,
            requested_field_ids=targets,
            canonical_field_ids=self.catalog.field_ids,
            facts=derived,
            warnings=research.warnings,
            configuration_notes=research.configuration_notes,
            model_call_count=research.trajectory.model_call_count,
            search_query_count=research.trajectory.search_query_count,
            grounded_source_count=research.trajectory.grounded_source_count,
            input_tokens=research.trajectory.usage.input_tokens,
            output_tokens=research.trajectory.usage.output_tokens,
            thinking_tokens=research.trajectory.usage.thinking_tokens,
            total_tokens=research.trajectory.usage.total_tokens,
            estimated_cost_usd=research.trajectory.usage.estimated_cost_usd,
            latency_ms=research.trajectory.elapsed_ms,
            retry_count=research.trajectory.retry_count,
            failures=research.trajectory.failures,
            trajectory_path=str(
                fixture_dir / "trajectory" / f"{research.trajectory.trajectory_id}.json"
            ),
        )
        path = fixture_dir / "result.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args(argv)
    runner = HybridRunner()
    item = runner.select(args.fixture)
    if not args.live:
        print(runner.dry_run(item).model_dump_json(indent=2))
        return 0
    runner.run(item, live=True, retry_failed=args.retry_failed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
