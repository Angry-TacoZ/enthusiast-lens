# Hackathon Core 24 Evaluation Specification

## Frozen status

`hackathon-core-24-ground-truth-v1` is the independently curated measuring
stick for `hackathon-core-24-v1`. It was frozen before any paid Core 24
Full-Web or Hybrid execution. The historical 92-field V1 corpus remains
unchanged under `evals/ground_truth/`; Core 24 lives separately under
`evals/ground_truth_core24_v1/` with its own schema, manifest, policy, lock,
audit, rules, and grader identity.

The corpus has 12 fixtures representing 11 vehicle families. The paired MINI
fixtures are two diagnostic cases for one family and are averaged into one
MINI family score before the 11-family headline macro.

The freeze contains 288 canonical field slots: 194 applicable scorable known
facts, 86 applicable unresolved facts excluded for insufficient exact evidence,
and 8 not-applicable facts. Required provenance coverage is 194/194.

## Frozen identities

- Task catalog: `hackathon-core-24-v1`
- Ground truth: `hackathon-core-24-ground-truth-v1`
- Schema: `hackathon-core-24-ground-truth-schema-v1`
- Comparison rules: `hackathon-core-24-comparison-rules-v1`
- Grader: `deterministic-core-24-grader-v1`
- Task catalog SHA-256: `59ae0015aae6592d006fd271a7e397b9778756dc0a9ba9918047f01c02eca6e7`
- Comparison rules SHA-256: `eeb27270df35546714cc634cdfd772b26668a83e41d2192c4105a22ea2f4e523`
- Grader source SHA-256: `a3311d5732c41dc91607681e7adc37dfca77a8ac14359a65fcfec63840280c37`
- Ground-truth lock SHA-256: `3b4bd15605c1ffd2e96ecdb247970fa5bbfcaf24f89855665d7cdebb0b87e750`

## Canonical output

The task definition is
[`hackathon_core_24_v1_field_catalog.json`](../evals/task_definition/hackathon_core_24_v1_field_catalog.json).
It has 24 canonical fields: 23 evidence-acquired fields plus deterministic
`engine_and_measured_performance.pounds_per_horsepower`.

Four fields are compound JSON values:

| Field | Required known shape |
|---|---|
| `brakes_wheels_and_tires.rotor_diameters_in` | `{ "front_diameter_in": number, "rear_diameter_in": number }` |
| `brakes_wheels_and_tires.default_tire` | `{ "brand_model": string, "front_size": string, "rear_size": string }` |
| `energy_storage.capacity` | `{ "fuel_tank_gal": number|null, "battery_kwh": number|null }` |
| `suspension_axles_and_chassis.suspension_layout` | `{ "front": string, "rear": string }` |

Square tire fitments repeat one size in both tire-size keys; staggered fitments
preserve both. ICE capacity uses fuel gallons, EV capacity uses gross/total
battery kWh, and PHEV capacity may contain both. Usable battery capacity is
not substituted for gross/total.

## Applicability and scoring

Every fixture represents all 24 field IDs exactly once:

- `known`: applicable, independently sourced, and scorable.
- `unresolved`: applicable but excluded from the denominator because exact
  defensible evidence was unavailable before freeze.
- `not_applicable`: excluded by frozen powertrain/transmission semantics; not
  converted to Unknown or error.

For known ground truth, a system output is `C` when its known value satisfies
the frozen comparison, `E` when a known value fails, and `U` when missing or
non-known. `C + E + U = N`. CEFC is `C/N`; attempted accuracy is `C/(C+E)`;
required error rate is `E/N`; Unknown rate is `U/N`. Correct researched facts
require provenance. Deterministic pounds/hp is provenance-exempt.

Headline CEFC is the unweighted macro-average across 11 family CEFC values.
The two MINI fixture CEFC values are averaged first, so MINI is not double
weighted.

## Frozen semantic decisions

- Audio power means manufacturer/system amplifier rated output in watts. Peak
  claims are not mixed with rated output.
- A subwoofer requires a dedicated low-frequency speaker; premium branding
  alone is insufficient.
- ACC means adaptive speed/following control, not ordinary cruise.
- Full stop-and-go requires braking to zero, holding/maintaining the stopped
  traffic state, and resume/continued low-speed following. Braking to zero and
  then cancelling does not qualify.
- Active lane centering continuously steers toward lane center. Warning,
  departure prevention, and momentary lane-keep correction do not qualify.
- Drivetrain normalizes only to `FWD`, `RWD`, `AWD`, or `4WD`.
- LSD is axle-neutral. A documented mechanical LSD or true electronic
  torque-apportioning differential qualifies; brake traction control and
  selectable full lockers alone do not.
- Displacement is liters. Pure EV displacement and aspiration are N/A.
- ICE horsepower/torque use rated engine output; PHEV uses manufacturer
  combined-system output; EV uses manufacturer combined-system peak output
  only when published.
- Pounds/hp is only `curb_weight_lb / horsepower`, rounded to two decimals.
  Missing or nonpositive inputs make it unresolved; Gemini never researches it.
- Measured 0–60, skidpad, and 70–0 require an exact-configuration instrumented
  test. Manufacturer estimates and tests of another trim, transmission, tire,
  package, drivetrain, body, or model year are not silently substituted.
- Transmission type is mechanism-specific. Generic `Automatic` is not equal
  to DCT, CVT, IVT, or torque-converter automatic.
- Gear count means physical forward ratios. CVT simulated steps are N/A;
  single-speed EV reduction is one physical ratio.
- Manual shifting from selector applies to automatic ratio requests from the
  center selector. A conventional manual and a single-speed EV are N/A.
- Regeneration paddles are not transmission paddle shifters.

## Frozen tolerances

| Value | Absolute tolerance |
|---|---:|
| Amplifier power | 1 W |
| Each rotor diameter | 0.1 in |
| 70–0 braking | 1 ft |
| Displacement | 0.05 L |
| Horsepower | 1 hp |
| Torque | 1 lb-ft |
| Curb weight | 25 lb |
| Pounds/hp | 0.05 lb/hp |
| 0–60 | 0.1 s |
| Skidpad | 0.01 g |
| Fuel tank | 0.1 gal |
| Gross battery capacity | 0.5 kWh |

Compound fields receive one canonical outcome. Every required component must
match its own rule; a one-axle or one-component match is not a correct field.
The exact machine-readable rules and aliases are in
`evals/ground_truth_core24_v1/comparison_rules.json`.

## Curation and provenance boundary

Historical V1 was used only as a pointer to already located public sources.
Each new Core 24 value was checked against its new semantic shape and exact
configuration. vPIC is not answer-key provenance. Every scorable fact carries
one or more manufacturer, exact-listing, or reputable technical sources with
the fact it supports.

No exact-configuration Car and Driver instrumented test was available for the
three measured fields in these frozen configurations. The corpus therefore
records 0 exact C&D answers for 0–60, skidpad, and 70–0; nearby trims/model
years were deliberately excluded. This is a coverage limitation, not a failed
runtime output.

An automated URL reachability check returned success for 25 of 35 distinct
source URLs. Ten sources returned HTTP 403 to an automated client (not 404),
including manufacturer/dealer PDFs behind anti-bot controls. Retained local
MINI listing snapshots and the exact Charger OEM sticker are referenced where
available. HTTP reachability is reported as an archival risk and does not
replace the substantive source review.

## Leakage boundary

Full-Web and Hybrid receive only `evals/inputs/benchmark_inputs.json`, the
answer-key-independent Core 24 field catalog, and their normal permitted live
sources. Only `core24_grader.py`, offline audits, and tests may read
`evals/ground_truth_core24_v1/`. Runtime inputs reject answer-key-like fields,
and tests scan runtime/provider modules for answer-key path imports.

## Controlled comparison

Full-Web and Hybrid must use the same 12 inputs, catalog, Gemini model,
instructions, Search policy, canonical schema, frozen comparison rules, and
grader. Hybrid may use live exact-VIN vPIC as the candidate intervention. It
does not receive answer-key values or provenance.

With 23 researched targets, Full-Web fits one Phase A and one Phase B call.
Hybrid removes only safe complete seeds and supplies trustworthy partial vPIC
context for the remaining research. The first matched run happens only after
this freeze checkpoint is reviewed.

## Benchmark correction policy

Answers and tolerances may not change in response to Full-Web or Hybrid output.
A later correction requires independent evidence, an explicit changelog entry,
a new benchmark version/lock, and rerunning both systems on the corrected same
set when practical.
