from pathlib import Path
from types import SimpleNamespace
from enthusiast_lens.evaluation.hybrid import HybridRunner, _research_context, _seeds
from enthusiast_lens.models import Confidence, ConfigurationMatch, EvidenceRelationship, OriginType, Provenance, SourceType
from enthusiast_lens.models.structured_seed import StructuredFactState

def _fact(field,value,state=StructuredFactState.REPORTED):
 return SimpleNamespace(provider_field=field,provider_value=None if value is None else str(value),normalized_value=value,state=state,provenance=Provenance(source_url="https://example.test/vpic",publisher="NHTSA",source_type=SourceType.GOVERNMENT_OR_REGULATORY,configuration_match=ConfigurationMatch.EXACT,origin=OriginType.STRUCTURED,confidence=Confidence.MEDIUM,relationship=EvidenceRelationship.SUPPORTS))

def test_vpic_seed_mapping_is_narrow_and_blank_or_ambiguous_is_not_seeded():
 seed=SimpleNamespace(facts=(_fact("DisplacementL",2.0),_fact("EngineHP",181),_fact("CurbWeightLB",2403),_fact("TransmissionSpeeds",6),_fact("DriveType","Rear-Wheel Drive")))
 facts=_seeds(seed)
 assert {x.field_id:x.value for x in facts} == {"engine_and_measured_performance.displacement_l":2.0,"engine_and_measured_performance.horsepower":181,"engine_and_measured_performance.curb_weight_lb":2403,"transmission.gear_count":6,"drivetrain_and_differentials.layout":"RWD"}
 assert all(x.origin is OriginType.STRUCTURED and x.provenance for x in facts)
 assert _seeds(SimpleNamespace(facts=(_fact("EngineHP",None,StructuredFactState.UNKNOWN),_fact("DriveType","all roads")))) == ()


def test_partial_context_is_not_promoted_to_a_false_canonical_answer():
 seed=SimpleNamespace(facts=(_fact("TransmissionStyle","Automatic"),_fact("TransmissionSpeeds",8),_fact("LaneKeepSystem",True)))
 facts=_seeds(seed)
 assert {fact.field_id for fact in facts} == {"transmission.gear_count"}


def test_explicit_turbo_and_mechanism_specific_transmission_can_seed():
 seed=SimpleNamespace(facts=(_fact("Turbo",True),_fact("TransmissionStyle","DCT"),_fact("AdaptiveCruiseControl",True),_fact("LaneCenteringAssistance",True)))
 facts=_seeds(seed)
 assert {fact.field_id:fact.value for fact in facts} == {
  "engine_and_measured_performance.aspiration":"turbocharged",
  "transmission.type":"DCT",
  "driver_assistance_and_highway_automation.adaptive_cruise_control":True,
  "driver_assistance_and_highway_automation.active_lane_centering":True,
 }


def test_context_filters_blank_values_and_preserves_optional_or_reported_values():
 context=(_fact("TransmissionStyle","Automatic"),)
 seed=SimpleNamespace(context_facts=context)
 assert _research_context(seed) == context
 assert _research_context(SimpleNamespace(context_facts=(_fact("Trim",None,StructuredFactState.UNKNOWN),))) == ()


def test_core_24_dry_run_reports_contribution_surface_not_per_vin_seed_promise():
 root = Path(__file__).parents[2]
 runner = HybridRunner(inputs_path=root / "evals" / "inputs" / "benchmark_inputs.json")
 report = runner.dry_run(runner.select("01_miata_gt_auto_ground_truth.json"))
 assert report.potential_vpic_contribution_field_count == 11
 assert report.maximum_research_field_count == 23
 assert report.max_model_calls == 2
