# Hybrid vPIC + Web

# Hybrid vPIC + Web (Hackathon Core 24)

## Hypothesis

Exact-VIN NHTSA vPIC data can reduce Web research without lowering factual
standards. Hybrid now uses structured data in two ways:

1. **Canonical structured seeds** safely populate a complete Core 24 field when
   the provider semantics are sufficient.
2. **Trusted research context** carries useful exact-VIN values that constrain
   Web research even when they cannot finish a canonical field.

For example, `TransmissionStyle=Automatic` and `TransmissionSpeeds=8` provide
useful context. The Web agent still determines whether the mechanism is a
torque-converter automatic, DCT, CVT/IVT, or another supported type. Generic
`Automatic` is never silently upgraded to one of those mechanisms.

## Current safe canonical mappings

- `DisplacementL`, or `DisplacementCC` converted deterministically to liters,
  -> `engine_and_measured_performance.displacement_l`
- valid `EngineHP` -> horsepower
- valid `CurbWeightLB` -> curb weight
- positive integer `TransmissionSpeeds` -> gear count
- explicit FWD/RWD/AWD/4WD `DriveType` -> drivetrain layout
- explicit positive `Turbo` -> `aspiration=turbocharged`
- explicit positive `AdaptiveCruiseControl` -> ACC
- actual `LaneCenteringAssistance` positive -> active lane centering
- mechanism-specific `TransmissionStyle` values such as CVT, DCT, or Manual
  -> transmission type

Blank, optional, unavailable, malformed, broad, or ambiguous values do not
become canonical answers. A vPIC `LaneKeepSystem` value is not lane centering.
Turbo blank/ambiguous is not naturally aspirated. A generic transmission style
is context, not a mechanism-specific seed.

## Research context

The adapter preserves exact-VIN context for identity and useful constraints,
including model year, make, model, trim, series, engine identity, displacement,
horsepower, fuel/electrification, transmission style/speeds, drivetrain, curb
weight, Turbo, ACC, lane centering, battery-energy fields, and wheel size when
vPIC returns them. Each context item retains NHTSA provenance and its original
provider state. Blank values are omitted from the research prompt; Optional and
Not Available remain non-assertive states.

The ResearchAgent receives this context explicitly and is told that it is
trusted exact-VIN NHTSA data, that blanks are unknown, and that it should not
spend searches re-establishing a safe value unless stronger evidence reveals a
real conflict. The context is persisted in the trajectory and Core 24 result.

## Partial compound fields

Partial structured knowledge is represented as context until reconciliation,
not as a falsely complete final fact. This matters for:

- `transmission.type`: generic Automatic may be known while mechanism remains
  unknown;
- `energy_storage.capacity`: battery range or battery side may be known while
  fuel-tank capacity remains a Web target for a PHEV.

The final Core 24 output still uses ordinary `FactState` rules and preserves
structured subfields and provenance boundaries. A compound fact assembled from
vPIC and Web evidence must not be attributed wholly to either source.

## Audit boundary

`scripts/audit_hybrid_core_24_vpic.py` performs only vPIC calls against the
answer-key-free runtime inputs. It reports per fixture:

- nonblank provider fields;
- complete canonical seeds;
- partial canonical contributions;
- context-only fields;
- fields still requiring Web research.

The audit is not a Gemini benchmark, does not read ground truth, does not grade
outputs, and cannot change the Core 24 answer key. Its generated report is
`artifacts/audits/hybrid_core_24_vpic_audit.json`.

## Version boundary

The runtime identity is `hybrid-vpic-web-core-24-v1`. This is a pre-benchmark
mapping revision. No paid Core 24 Gemini run has occurred, and no Hybrid quality
claim is made until the independently curated Core 24 ground truth and grader
are frozen.
