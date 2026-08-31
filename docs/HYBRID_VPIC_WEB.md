# Hybrid vPIC + Web

Hybrid begins with one exact-VIN NHTSA vPIC decode, admits only semantically
safe structured facts, and sends every remaining V1 researched field to the
unchanged Web ResearchAgent. vPIC is structured source evidence, never ground
truth. Blank provider values mean not supplied; they never imply absent
equipment.

## Version boundary

`hybrid-vpic-web-v1` is preserved historical evidence with four admitted vPIC
seeds: displacement, horsepower, forward gear count, and unambiguous drivetrain
layout. `hybrid-vpic-web-v2` expands only the structured-seed admission rules
below. The model, prompts, Google Search behavior, phase batching, deadlines,
provenance semantics, frozen task catalog, benchmark inputs, and grader are
unchanged. No Gemini benchmark run has been made for V2.

## V2 admitted structured seeds

| vPIC field(s) | Canonical field | Admission rule |
| --- | --- | --- |
| `DisplacementCC` | `engine_and_measured_performance.displacement_cc` | Positive finite number; emitted in `cc`. |
| `EngineHP` | `engine_and_measured_performance.horsepower` | Positive finite number; emitted in `hp`. |
| `EngineConfiguration` + `EngineCylinders` | `engine_and_measured_performance.engine_configuration` | Both reported; recognized layout (`inline`, `V`, or `flat`) and a positive whole cylinder count. The deterministic value is, for example, `inline 4-cylinder`. |
| `CurbWeightLB` | `engine_and_measured_performance.curb_weight` | Positive finite number; emitted in `lb`. |
| `TransmissionSpeeds` | `transmission.gear_count` | Positive whole number only. |
| `DriveType` | `drivetrain_and_differentials.layout` | Explicit `FWD`, `RWD`, `AWD`, or `4WD` value/alias only. Broad values such as `2WD` are ambiguous and rejected. |

Every admitted fact retains exact-VIN vPIC provenance and
`OriginType.STRUCTURED`. The composed engine-configuration fact retains both
provider-field provenance records. A duplicated relevant provider field is a
hard validation error; a blank, malformed, unsupported, or ambiguous field is
simply not seeded and remains a normal Web-research target.

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
