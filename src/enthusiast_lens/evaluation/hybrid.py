"""Minimal vPIC-first Hybrid benchmark runner; provider work requires --live."""
from __future__ import annotations
import argparse, json
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable
from pydantic import BaseModel, ConfigDict
from enthusiast_lens.adapters import VPICClient
from enthusiast_lens.deterministic import canonicalize_string
from enthusiast_lens.model import GeminiSettings, ModelProvider
from enthusiast_lens.models import FactResult, FactState, OriginType, RunMode, RunStatus
from enthusiast_lens.models.benchmark_input import BenchmarkInput
from enthusiast_lens.models.structured_seed import StructuredFactState, StructuredVehicleSeed
from enthusiast_lens.research import ResearchAgent
from enthusiast_lens.research.agent import PHASE_A_MAX_FIELDS_PER_BATCH, PHASE_B_MAX_FIELDS_PER_BATCH
from .field_catalog import DEFAULT_FIELD_CATALOG_PATH, field_catalog_hash, load_field_catalog
from .full_web import BaselineResult, DEFAULT_INPUTS_PATH, FullWebBaselineRunner, _load_inputs_only

SYSTEM_VERSION="hybrid-vpic-web-v1"; DEFAULT_OUTPUT_ROOT=Path("artifacts/evals/hybrid")
VPIC_MAP={"DisplacementCC":("engine_and_measured_performance.displacement_cc",None),"EngineHP":("engine_and_measured_performance.horsepower","hp"),"TransmissionSpeeds":("transmission.gear_count",None),"DriveType":("drivetrain_and_differentials.layout",None)}
DRIVE={"rwd":"RWD","rear-wheel drive":"RWD","fwd":"FWD","front-wheel drive":"FWD","awd":"AWD","all-wheel drive":"AWD","4wd":"4WD","four-wheel drive":"4WD"}
class HybridDryRun(BaseModel):
 model_config=ConfigDict(frozen=True); fixture_id:str; total_canonical_fields:int; potential_vpic_seed_field_count:int; maximum_research_field_count:int; max_model_calls:int; vpic_seed_count_note:str
def _seeds(seed: StructuredVehicleSeed):
 out=[]
 for fact in seed.facts:
  target=VPIC_MAP.get(fact.provider_field)
  if not target or fact.state is not StructuredFactState.REPORTED or fact.normalized_value is None: continue
  field_id,unit=target; value=fact.normalized_value
  if fact.provider_field in {"DisplacementCC","EngineHP","TransmissionSpeeds"}:
   if isinstance(value,bool) or not isinstance(value,(int,float)) or value<=0: continue
   if fact.provider_field=="TransmissionSpeeds" and (not float(value).is_integer()): continue
   value=int(value) if fact.provider_field=="TransmissionSpeeds" else value
  if fact.provider_field=="DriveType":
   value=DRIVE.get(canonicalize_string(str(value)) or "")
   if value is None: continue
  out.append(FactResult(field_id=field_id,value=value,unit=unit,state=FactState.KNOWN,provenance=(fact.provenance,),origin=OriginType.STRUCTURED))
 if len({x.field_id for x in out})!=len(out): raise ValueError("duplicate vPIC canonical seed")
 return tuple(out)
class HybridRunner:
 def __init__(self,*,inputs_path:Path=DEFAULT_INPUTS_PATH,field_catalog_path:Path=DEFAULT_FIELD_CATALOG_PATH,output_root:Path=DEFAULT_OUTPUT_ROOT,settings:GeminiSettings|None=None,vpic_client:VPICClient|None=None,provider_factory:Callable[[BenchmarkInput],ModelProvider|None]|None=None):
  self.corpus=_load_inputs_only(inputs_path); self.catalog=load_field_catalog(field_catalog_path); self.catalog_hash=field_catalog_hash(field_catalog_path); self.output_root=output_root; self.settings=settings or GeminiSettings.from_environment(); self.vpic=vpic_client or VPICClient(); self.provider_factory=provider_factory
 def select(self,fixture_id:str)->BenchmarkInput:
  return next(x for x in self.corpus.inputs if x.fixture_id==fixture_id)
 def dry_run(self,item:BenchmarkInput)->HybridDryRun:
  n=len(self.catalog.agent_research_field_ids); calls=(n+23)//24+(n+23)//24
  return HybridDryRun(fixture_id=item.fixture_id,total_canonical_fields=len(self.catalog.field_ids),potential_vpic_seed_field_count=4,maximum_research_field_count=n,max_model_calls=calls,vpic_seed_count_note="Potential only; exact seeds require a live vPIC decode.")
 def targets(self,seed:StructuredVehicleSeed)->tuple[str,...]:
  seeded={x.field_id for x in _seeds(seed)}; return tuple(x for x in self.catalog.agent_research_field_ids if x not in seeded)
 def _result_path(self,item): return self.output_root/item.fixture_id/"result.json"
 def run(self,item:BenchmarkInput,*,live:bool=False,retry_failed:bool=False):
  if not live: raise ValueError("paid execution requires live=True")
  path=self._result_path(item)
  if path.is_file():
   existing=BaselineResult.model_validate_json(path.read_text(encoding="utf-8"))
   if existing.status is RunStatus.SUCCEEDED: return None
   if not retry_failed: return existing
   path.replace(FullWebBaselineRunner._archive_path(path))
  return self.run_fixture(item)
 def run_fixture(self,item:BenchmarkInput)->BaselineResult:
  if not item.vehicle.vin: raise ValueError("Hybrid requires exact VIN")
  started=datetime.now(UTC); fixture_dir=self.output_root/item.fixture_id; seed=self.vpic.decode_vin(item.vehicle.vin,item.vehicle.year); seeded=_seeds(seed); targets=self.targets(seed); agent=ResearchAgent(settings=self.settings,provider=self.provider_factory(item) if self.provider_factory else None); research=agent.run(item.vehicle,targets,development_trace_root=fixture_dir/"trajectory")
  researched={x.field_id:x for x in research.facts}; seeded_ids={x.field_id for x in seeded}
  if research.analysis.status is not RunStatus.SUCCEEDED:
   result=BaselineResult(system_version=SYSTEM_VERSION,fixture_id=item.fixture_id,vehicle_family_id=item.vehicle_family_id,vehicle=item.vehicle,run_mode=RunMode.HYBRID,model=research.trajectory.model,instruction_version=research.trajectory.instruction_version,instruction_sha256=research.trajectory.instruction_sha256,field_catalog_version=self.catalog.catalog_version,field_catalog_sha256=self.catalog_hash,started_at=started,completed_at=research.trajectory.completed_at,status=research.analysis.status,requested_field_ids=targets,canonical_field_ids=self.catalog.field_ids,facts=tuple(seeded)+research.facts,warnings=research.warnings,configuration_notes=research.configuration_notes,model_call_count=research.trajectory.model_call_count,search_query_count=research.trajectory.search_query_count,grounded_source_count=research.trajectory.grounded_source_count,input_tokens=research.trajectory.usage.input_tokens,output_tokens=research.trajectory.usage.output_tokens,thinking_tokens=research.trajectory.usage.thinking_tokens,total_tokens=research.trajectory.usage.total_tokens,estimated_cost_usd=research.trajectory.usage.estimated_cost_usd,latency_ms=research.trajectory.elapsed_ms,retry_count=research.trajectory.retry_count,failures=research.trajectory.failures,trajectory_path=str(fixture_dir/"trajectory"/f"{research.trajectory.trajectory_id}.json")); path=fixture_dir/"result.json";path.parent.mkdir(parents=True,exist_ok=True);path.write_text(result.model_dump_json(indent=2),encoding="utf-8");return result
  if seeded_ids & set(researched): raise ValueError("duplicate seeded and researched canonical field")
  if set(researched)!=set(targets): raise ValueError("researched facts missing or outside requested targets")
  ordered=tuple((next((x for x in seeded if x.field_id==fid),None) or researched[fid]) for fid in self.catalog.agent_research_field_ids)
  derived=FullWebBaselineRunner._append_deterministic_facts(self,ordered)
  if len(ordered)!=len(self.catalog.agent_research_field_ids) or len(derived)!=len(self.catalog.field_ids): raise ValueError("successful Hybrid canonical field invariant failed")
  result=BaselineResult(system_version=SYSTEM_VERSION,fixture_id=item.fixture_id,vehicle_family_id=item.vehicle_family_id,vehicle=item.vehicle,run_mode=RunMode.HYBRID,model=research.trajectory.model,instruction_version=research.trajectory.instruction_version,instruction_sha256=research.trajectory.instruction_sha256,field_catalog_version=self.catalog.catalog_version,field_catalog_sha256=self.catalog_hash,started_at=started,completed_at=research.trajectory.completed_at,status=research.analysis.status,requested_field_ids=targets,canonical_field_ids=self.catalog.field_ids,facts=derived,warnings=research.warnings,configuration_notes=research.configuration_notes,model_call_count=research.trajectory.model_call_count,search_query_count=research.trajectory.search_query_count,grounded_source_count=research.trajectory.grounded_source_count,input_tokens=research.trajectory.usage.input_tokens,output_tokens=research.trajectory.usage.output_tokens,thinking_tokens=research.trajectory.usage.thinking_tokens,total_tokens=research.trajectory.usage.total_tokens,estimated_cost_usd=research.trajectory.usage.estimated_cost_usd,latency_ms=research.trajectory.elapsed_ms,retry_count=research.trajectory.retry_count,failures=research.trajectory.failures,trajectory_path=str(fixture_dir/"trajectory"/f"{research.trajectory.trajectory_id}.json"))
  path=fixture_dir/"result.json"; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(result.model_dump_json(indent=2),encoding="utf-8"); return result
def main(argv:list[str]|None=None)->int:
 p=argparse.ArgumentParser();p.add_argument("--fixture",required=True);p.add_argument("--live",action="store_true");p.add_argument("--retry-failed",action="store_true");args=p.parse_args(argv); r=HybridRunner(); item=r.select(args.fixture)
 if not args.live: print(r.dry_run(item).model_dump_json(indent=2));return 0
 r.run(item,live=True,retry_failed=args.retry_failed);return 0
if __name__=="__main__": raise SystemExit(main())
