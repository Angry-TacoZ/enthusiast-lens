from types import SimpleNamespace
from enthusiast_lens.evaluation.hybrid import _seeds
from enthusiast_lens.models import Confidence, ConfigurationMatch, EvidenceRelationship, OriginType, Provenance, SourceType
from enthusiast_lens.models.structured_seed import StructuredFactState

def _fact(field,value,state=StructuredFactState.REPORTED):
 return SimpleNamespace(provider_field=field,normalized_value=value,state=state,provenance=Provenance(source_url="https://example.test/vpic",publisher="NHTSA",source_type=SourceType.GOVERNMENT_OR_REGULATORY,configuration_match=ConfigurationMatch.EXACT,origin=OriginType.STRUCTURED,confidence=Confidence.MEDIUM,relationship=EvidenceRelationship.SUPPORTS))

def test_vpic_seed_mapping_is_narrow_and_blank_or_ambiguous_is_not_seeded():
 seed=SimpleNamespace(facts=(_fact("DisplacementL",2.0),_fact("EngineHP",181),_fact("CurbWeightLB",2403),_fact("TransmissionSpeeds",6),_fact("DriveType","Rear-Wheel Drive")))
 facts=_seeds(seed)
 assert {x.field_id:x.value for x in facts} == {"engine_and_measured_performance.displacement_l":2.0,"engine_and_measured_performance.horsepower":181,"engine_and_measured_performance.curb_weight_lb":2403,"transmission.gear_count":6,"drivetrain_and_differentials.layout":"RWD"}
 assert all(x.origin is OriginType.STRUCTURED and x.provenance for x in facts)
 assert _seeds(SimpleNamespace(facts=(_fact("EngineHP",None,StructuredFactState.UNKNOWN),_fact("DriveType","all roads")))) == ()
