# Hackathon Core 24 Evaluation Specification

## Status

`hackathon-core-24-v1` defines the active hackathon task shape. Its answer-key
corpus is **not yet frozen**. No paid Core 24 Full-Web or Hybrid result may be
graded or presented as a benchmark result until independent curation completes
the new corpus, provenance audit, leakage scan, and lock.

The historical 92-field V1 corpus remains unchanged at
`evals/ground_truth/` and must continue to be used only for historical V1
artifacts.

## Canonical output

The task definition is
[`hackathon_core_24_v1_field_catalog.json`](../evals/task_definition/hackathon_core_24_v1_field_catalog.json).
It has 24 canonical fields: 23 evidence-acquired fields plus deterministic
`engine_and_measured_performance.pounds_per_horsepower`.

The following fields are JSON objects and must retain their subfields in the
canonical result:

| Field | Required object shape when known |
|---|---|
| `brakes_wheels_and_tires.rotor_diameters_in` | `{ "front_diameter_in": number|null, "rear_diameter_in": number|null }` |
| `brakes_wheels_and_tires.default_tire` | `{ "brand_model": string|null, "size": string|null }` |
| `energy_storage.capacity` | `{ "fuel_tank_gal": number|null, "battery_kwh": number|null }` |
| `suspension_axles_and_chassis.suspension_layout` | `{ "front": string|null, "rear": string|null }` |

For energy storage: ICE configurations use `fuel_tank_gal`; EV configurations
use `battery_kwh`; PHEVs may have both. Units are never combined into one
number.

## Deterministic field

`pounds_per_horsepower` is calculated only when canonical horsepower and curb
weight are known:

```text
curb_weight_lb / horsepower
```

It is rounded to two decimal places, has unit `lb/hp`, and is never requested
from Gemini or vPIC as an independent fact.

## Ground-truth curation rules

The new corpus must use new versioned directories and locks; it must not modify
the V1 corpus or `benchmark_lock.json`.

1. Preserve exact vehicle, trim, drivetrain, transmission, package, market,
   and VIN identity where Hybrid needs a VIN.
2. Reuse V1 evidence only when it independently supports the exact new field
   semantics. A renamed field or a combined object needs fresh verification.
3. Prefer manufacturer documentation for configuration facts. Use Car and
   Driver for matching-configuration 0–60, skidpad, and 70–0 results when
   available; document another instrumented source when not.
4. Do not use vPIC as the sole ground truth for a Hybrid-seeded field. That
   would make the system grade itself against its own input source.
5. Store one or more supporting sources for every scorable fact. Mark missing
   or unresolvable facts explicitly; never manufacture a value.
6. Freeze value aliases, numeric tolerances, and measured-test acceptance
   ranges before either model is run.

## Comparison policy to freeze with the corpus

- Boolean and enum facts: normalized exact match plus explicitly listed aliases.
- Numeric manufacturer specifications: explicit field-level tolerance, if any.
- Instrumented 0–60, skidpad, and 70–0 results: source/test-method-specific
  accepted range fixed before execution, never widened after observing output.
- Rotor and suspension objects: compare front and rear independently; a match
  on only one side is not a whole-object match.
- Default tire objects: compare brand/model and size independently using
  explicitly frozen aliases; an unspecified brand is not evidence of a match.
- Energy objects: compare each non-null component in its own unit. A fuel-tank
  result cannot satisfy a battery-capacity expectation, or vice versa.

The deterministic grader will retain C/E/U, CEFC, attempted accuracy, error
rate, Unknown rate, provenance success, and paired-MINI family aggregation if
the new corpus includes the same family structure.

## Controlled comparison

Full-Web and Hybrid must use the same Core 24 catalog, benchmark input, model,
research instruction, Search policy, output schema, and frozen grader. Hybrid
may remove facts that an exact-VIN vPIC decode safely seeds and may pass other
trustworthy exact-VIN values as research context. Complete-seed candidates
include displacement, horsepower, curb weight, gear count, explicit turbo,
positive ACC/lane-centering, mechanism-specific transmission, and an
unambiguous drivetrain layout. Generic transmission style, ambiguous
aspiration, optional equipment, and broad drive labels remain Web-research
targets (or non-assertive context).

With 23 researched targets, Full-Web plans one Phase A and one Phase B call.
Hybrid can remove safe seed fields and supply trusted exact-VIN context for
additional fields, but is still bounded by at most one batch in each phase.
The vPIC contribution surface is an 11-field upper bound, not a per-VIN
guarantee. Its benefits must therefore be measured through evidence quality,
Web target count, tokens, latency, cost, and failure behavior—not presumed from
the architecture.
