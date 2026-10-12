# Hybrid vPIC + Web

Hybrid begins with one exact-VIN NHTSA vPIC decode, admits only semantically
safe structured facts, and sends every remaining V1 researched field to the
unchanged Web ResearchAgent. vPIC is structured source evidence, never ground
truth. Blank provider values mean not supplied; they never imply absent
equipment.

## Version boundary

`hybrid-vpic-web-v1` is preserved historical evidence with four admitted vPIC
seeds: displacement, horsepower, forward gear count, and unambiguous drivetrain
layout. The initial `hybrid-vpic-web-v2` candidate added curb weight and a
composed engine-configuration label. The current `hybrid-vpic-web-v3` keeps
curb weight and returns engine configuration to Web research to preserve the
frozen benchmark comparison contract. The model, prompts, Google Search
behavior, phase batching, deadlines, provenance semantics, frozen task catalog,
benchmark inputs, and grader are unchanged. No Gemini benchmark run has been
made for V2 or V3.

## V3 admitted structured seeds

| vPIC field(s) | Canonical field | Admission rule |
| --- | --- | --- |
| `DisplacementCC` | `engine_and_measured_performance.displacement_cc` | Positive finite number; emitted in `cc`. |
| `EngineHP` | `engine_and_measured_performance.horsepower` | Positive finite number; emitted in `hp`. |
| `CurbWeightLB` | `engine_and_measured_performance.curb_weight` | Positive finite number; emitted in `lb`. |
| `TransmissionSpeeds` | `transmission.gear_count` | Positive whole number only. |
| `DriveType` | `drivetrain_and_differentials.layout` | Explicit `FWD`, `RWD`, `AWD`, or `4WD` value/alias only. Broad values such as `2WD` are ambiguous and rejected. |

Every admitted fact retains exact-VIN vPIC provenance and
`OriginType.STRUCTURED`. A duplicated relevant provider field is a hard
validation error; a blank, malformed, unsupported, or ambiguous field is simply
not seeded and remains a normal Web-research target.

Engine layout and cylinder count remain Web-researched. The composed label
`inline 4-cylinder` does not satisfy the frozen benchmark's accepted
engine-configuration values, so treating it as known would bypass the existing
comparison contract while omitting more specific configuration details.

The saved `hybrid_vpic_seed_audit_v2.json` records the initial V2 mapping audit,
including its now-removed engine-configuration seed. Its counts describe that
initial candidate and must not be read as current V3 seed coverage. The audit
script now follows the V3 admission rules; refreshing the vPIC-only audit
requires a new explicit NHTSA request. The two curb-weight results that differed
from frozen references remain unresolved as factual discrepancies and are not
claimed as benchmark-compatible by this mapping decision.

## Intentional exclusions

`TransmissionStyle` is not mapped. A value such as `Automatic` does not prove
the canonical exact mechanism (`torque-converter`, `DCT`, `CVT`, and so on), and
it is not a clean match for the catalog's control-type field. It therefore stays
with Web research.

`AdaptiveCruiseControl`, `LaneDepartureWarning`, `LaneKeepSystem`, `Turbo`,
`BrakeSystemType`, axle count, and other equipment/ADAS fields also remain Web
research targets. vPIC may describe availability or a broad configuration rather
than exact equipped hardware; no absence is inferred from a blank response.

## Workload and isolation

The catalog remains 92 canonical facts: 91 are researchable and one
power-to-weight fact is deterministic. Structured seed IDs are removed from the
91 ResearchAgent targets before batching, and the runner rejects any
seeded/researched duplicate. Phase A and Phase B use the existing maximum of 24
targets per batch, so the maximum call count becomes twice the batch count for
the remaining targets. Neither the runtime nor this mapping reads
`evals/ground_truth/`.
