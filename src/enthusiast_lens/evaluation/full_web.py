"""Reproducible Full-Web benchmark baseline runner.

The runner intentionally has no ground-truth, vPIC, structured-seed, or
knowledge-store dependency. Dry-run is the safe default; paid execution
requires ``--live``.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Callable
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from enthusiast_lens.model import GeminiSettings, ModelProvider
from enthusiast_lens.models import FactResult, RunMode, RunStatus, VehicleContext
from enthusiast_lens.models.benchmark_input import BenchmarkInput, BenchmarkInputCorpus
from enthusiast_lens.research import ResearchAgent
from enthusiast_lens.research.instructions import INSTRUCTION_VERSION, instruction_hash

from .field_catalog import DEFAULT_FIELD_CATALOG_PATH, FieldCatalog, field_catalog_hash, load_field_catalog


SYSTEM_VERSION = "full-web-baseline-v1"
REFERENCE_COST_USD = 0.00745575
REFERENCE_FIELD_COUNT = 4
DEFAULT_MAX_TOTAL_COST_USD = 2.00
DEFAULT_INPUTS_PATH = Path("evals/inputs/benchmark_inputs.json")
DEFAULT_OUTPUT_ROOT = Path("artifacts/evals/full_web")


class BaselineResult(BaseModel):
    """Formal answer-key-free output persisted for one baseline fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    system_version: str
    fixture_id: str
    vehicle_family_id: str
    vehicle: VehicleContext
    run_mode: RunMode
    model: str
    instruction_version: str
    instruction_sha256: str
    field_catalog_version: str
    field_catalog_sha256: str
    started_at: datetime
    completed_at: datetime | None = None
    status: RunStatus
    requested_field_ids: tuple[str, ...]
    facts: tuple[FactResult, ...] = Field(default_factory=tuple)
    warnings: tuple[str, ...] = Field(default_factory=tuple)
    configuration_notes: tuple[str, ...] = Field(default_factory=tuple)
    model_call_count: int = Field(default=0, ge=0)
    search_query_count: int = Field(default=0, ge=0)
    grounded_source_count: int = Field(default=0, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    thinking_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    latency_ms: int | None = Field(default=None, ge=0)
    retry_count: int = Field(default=0, ge=0)
    failures: tuple[str, ...] = Field(default_factory=tuple)
    trajectory_path: str | None = None


class BaselineDryRun(BaseModel):
    """Deterministic cost and execution plan shown before paid runs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_count: int = Field(ge=0)
    fixture_ids: tuple[str, ...]
    requested_field_count: int = Field(ge=0)
    max_model_calls_per_fixture: int = 2
    maximum_total_model_calls: int = Field(ge=0)
    configured_search_call_ceiling: int | None = Field(default=None, ge=0)
    rough_projected_cost_usd: float = Field(ge=0)
    rough_cost_basis: str
    maximum_total_cost_usd: float = Field(ge=0)


ProviderFactory = Callable[[BenchmarkInput], ModelProvider | None]


def _load_inputs_only(path: Path) -> BenchmarkInputCorpus:
    """Load only the answer-key-free runtime input corpus."""

    resolved = path.resolve()
    if "ground_truth" in {part.casefold() for part in resolved.parts}:
        raise ValueError("Full-Web baseline cannot load a ground-truth path")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"benchmark inputs could not be loaded: {error}") from error
    return BenchmarkInputCorpus.model_validate(raw)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class FullWebBaselineRunner:
    """Execute fresh Full-Web cases using only runtime inputs and the field catalog."""

    def __init__(
        self,
        *,
        inputs_path: Path = DEFAULT_INPUTS_PATH,
        field_catalog_path: Path = DEFAULT_FIELD_CATALOG_PATH,
        output_root: Path = DEFAULT_OUTPUT_ROOT,
        settings: GeminiSettings | None = None,
        max_total_cost_usd: float = DEFAULT_MAX_TOTAL_COST_USD,
        provider_factory: ProviderFactory | None = None,
    ) -> None:
        self.inputs_path = inputs_path
        self.catalog_path = field_catalog_path
        self.output_root = output_root
        self.settings = settings or GeminiSettings.from_environment()
        if max_total_cost_usd < 0:
            raise ValueError("max_total_cost_usd must be non-negative")
        self.max_total_cost_usd = max_total_cost_usd
        self.provider_factory = provider_factory
        self.corpus = _load_inputs_only(inputs_path)
        if any(not item.runtime_ready for item in self.corpus.inputs):
            raise ValueError("Full-Web baseline requires all selected runtime inputs to be ready")
        self.catalog = load_field_catalog(field_catalog_path)
        self.catalog_hash = field_catalog_hash(field_catalog_path)

    def select(self, *, fixture_ids: tuple[str, ...] = (), all_fixtures: bool = False) -> tuple[BenchmarkInput, ...]:
        if all_fixtures and fixture_ids:
            raise ValueError("choose --all or explicit fixtures, not both")
        if all_fixtures or not fixture_ids:
            return self.corpus.inputs
        by_id = {item.fixture_id: item for item in self.corpus.inputs}
        missing = [fixture_id for fixture_id in fixture_ids if fixture_id not in by_id]
        if missing:
            raise ValueError(f"unknown benchmark fixture(s): {missing}")
        return tuple(by_id[fixture_id] for fixture_id in fixture_ids)

    def dry_run(self, fixtures: tuple[BenchmarkInput, ...]) -> BaselineDryRun:
        field_count = len(self.catalog.field_ids)
        count = len(fixtures)
        projected = round(REFERENCE_COST_USD * (field_count / REFERENCE_FIELD_COUNT) * count, 8)
        return BaselineDryRun(
            fixture_count=count,
            fixture_ids=tuple(item.fixture_id for item in fixtures),
            requested_field_count=field_count,
            maximum_total_model_calls=count * 2,
            configured_search_call_ceiling=self.settings.max_search_calls,
            rough_projected_cost_usd=projected,
            rough_cost_basis=(
                f"Approximate only: Step 7 reference was {REFERENCE_FIELD_COUNT} fields, "
                f"2 calls, 3,957 tokens, and ${REFERENCE_COST_USD:.8f}; scaled by field count "
                "and fixture count, without assuming linear provider behavior."
            ),
            maximum_total_cost_usd=self.max_total_cost_usd,
        )

    def run(
        self,
        fixtures: tuple[BenchmarkInput, ...],
        *,
        live: bool = False,
        continue_on_failure: bool = False,
        retry_failed: bool = False,
    ) -> tuple[BaselineResult | None, ...]:
        if not live:
            raise ValueError("paid execution requires live=True")
        results: list[BaselineResult | None] = []
        accumulated_cost = 0.0
        rough_per_fixture = self.dry_run((fixtures[0],)).rough_projected_cost_usd if fixtures else 0.0
        for item in fixtures:
            existing = self._existing_result(item)
            if existing is not None and existing.status is RunStatus.SUCCEEDED:
                results.append(None)
                continue
            if existing is not None and not retry_failed:
                results.append(existing)
                if not continue_on_failure:
                    break
                continue
            if accumulated_cost + rough_per_fixture > self.max_total_cost_usd:
                raise RuntimeError(
                    "Full-Web cost ceiling would be exceeded before another provider call: "
                    f"measured=${accumulated_cost:.8f}, rough_next=${rough_per_fixture:.8f}, "
                    f"ceiling=${self.max_total_cost_usd:.8f}"
                )
            result = self.run_fixture(item)
            results.append(result)
            if result.estimated_cost_usd is not None:
                accumulated_cost += result.estimated_cost_usd
            if result.status is not RunStatus.SUCCEEDED and not continue_on_failure:
                break
            if accumulated_cost > self.max_total_cost_usd:
                raise RuntimeError("measured Full-Web cost exceeded the configured ceiling")
        return tuple(results)

    def run_fixture(self, item: BenchmarkInput) -> BaselineResult:
        started_at = _utc_now()
        fixture_dir = self.output_root / item.fixture_id
        fixture_dir.mkdir(parents=True, exist_ok=True)
        provider = self.provider_factory(item) if self.provider_factory else None
        agent = ResearchAgent(settings=self.settings, provider=provider)
        research = agent.run(
            item.vehicle,
            self.catalog.field_ids,
            development_trace_root=fixture_dir / "trajectory",
        )
        completed_at = research.trajectory.completed_at or _utc_now()
        trajectory_path = fixture_dir / "trajectory" / f"{research.trajectory.trajectory_id}.json"
        result = BaselineResult(
            system_version=SYSTEM_VERSION,
            fixture_id=item.fixture_id,
            vehicle_family_id=item.vehicle_family_id,
            vehicle=item.vehicle,
            run_mode=RunMode.FULL_WEB,
            model=research.trajectory.model,
            instruction_version=research.trajectory.instruction_version,
            instruction_sha256=research.trajectory.instruction_sha256,
            field_catalog_version=self.catalog.catalog_version,
            field_catalog_sha256=self.catalog_hash,
            started_at=started_at,
            completed_at=completed_at,
            status=research.analysis.status,
            requested_field_ids=research.trajectory.requested_field_ids,
            facts=research.facts,
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
            trajectory_path=str(trajectory_path),
        )
        self._persist_result(item, result)
        return result

    def _result_path(self, item: BenchmarkInput) -> Path:
        return self.output_root / item.fixture_id / "result.json"

    def _existing_result(self, item: BenchmarkInput) -> BaselineResult | None:
        path = self._result_path(item)
        if not path.is_file():
            return None
        try:
            result = BaselineResult.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ValueError(f"existing baseline result is invalid: {path}: {error}") from error
        if not self._identity_matches(result):
            return None
        return result

    def _identity_matches(self, result: BaselineResult) -> bool:
        return (
            result.system_version == SYSTEM_VERSION
            and result.model == self.settings.model
            and result.instruction_version == INSTRUCTION_VERSION
            and result.instruction_sha256 == instruction_hash()
            and result.field_catalog_version == self.catalog.catalog_version
            and result.field_catalog_sha256 == self.catalog_hash
        )

    def _persist_result(self, item: BenchmarkInput, result: BaselineResult) -> Path:
        path = self._result_path(item)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and result.status is not RunStatus.SUCCEEDED:
            archive = path.with_name(f"failed-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}.json")
            path.replace(archive)
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return path


def _print_json(value: BaseModel) -> None:
    print(value.model_dump_json(indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="append", dest="fixtures", help="Fixture ID; repeat for multiple fixtures")
    parser.add_argument("--all", action="store_true", help="Select all 12 runtime fixtures")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without provider calls (default safety mode)")
    parser.add_argument("--live", action="store_true", help="Authorize paid provider execution")
    parser.add_argument("--continue-on-failure", action="store_true")
    parser.add_argument("--retry-failed", action="store_true", help="Explicitly rerun a previously failed fixture")
    parser.add_argument("--max-total-cost-usd", type=float, default=DEFAULT_MAX_TOTAL_COST_USD)
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS_PATH)
    parser.add_argument("--field-catalog", type=Path, default=DEFAULT_FIELD_CATALOG_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args(argv)
    try:
        runner = FullWebBaselineRunner(
            inputs_path=args.inputs,
            field_catalog_path=args.field_catalog,
            output_root=args.output_root,
            max_total_cost_usd=args.max_total_cost_usd,
        )
        fixtures = runner.select(fixture_ids=tuple(args.fixtures or ()), all_fixtures=args.all)
        if args.dry_run or not args.live:
            _print_json(runner.dry_run(fixtures))
            return 0
        results = runner.run(
            fixtures,
            live=True,
            continue_on_failure=args.continue_on_failure,
            retry_failed=args.retry_failed,
        )
        print(json.dumps([result.model_dump(mode="json") if result else {"status": "skipped_complete"} for result in results], indent=2))
        return 0 if all(result is None or result.status is RunStatus.SUCCEEDED for result in results) else 1
    except (ValueError, RuntimeError) as error:
        parser.error(str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
