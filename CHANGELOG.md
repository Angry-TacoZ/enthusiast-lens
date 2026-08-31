# Enthusiast Lens — Improvement Changelog

This changelog records meaningful product, engineering, evaluation, and scope decisions for the Agentic Workflows Hackathon submission.

The goal is not to record every code edit. It is to preserve the reasoning behind important changes so the final system can be compared against earlier approaches and reproduced by another person.

---

## 2026-08-28 — Initial Design and Evaluation Decisions

### 1. Selected problem: enthusiast vehicle intelligence
**Decision:** Build an enthusiast-focused vehicle intelligence layer for online car shoppers.

**Why:** Mainstream car marketplaces expose broad consumer filters and simplified specification labels, but enthusiast-relevant mechanical and configuration details are often buried, missing, generic, or unfilterable.

**Current thesis:** Car-shopping sites treat specifications as product descriptions. Enthusiasts treat specifications as queryable data.

**Status:** Kept.


### 54. Added deterministic benchmark-grader candidate after preserving V4 evidence
**Decision:** Preserve the completed Full-Web V4 Miata result and trajectory first, then implement a local-only deterministic grader candidate. The grader is the only evaluation component that reads `evals/ground_truth/`; the Full-Web runner and research agent remain answer-key-free.

**Review correction:** Before any additional benchmark fixture was run, review found that the candidate exposed only the attempt-normalized error diagnostic `E / (C + E)` where the predeclared benchmark error rate is `E / N`. The candidate now exposes the required CEFC `C / N`, attempted accuracy `C / (C + E)`, error rate `E / N`, and Unknown rate `U / N`, while retaining the former value only as an explicitly secondary diagnostic. It enforces `C + E + U = N`, requires fixture-name identity between result and frozen ground truth, records frozen excluded-status counts, and writes system-level aggregate summaries. MINI remains one averaged family; null attempt/provenance ratios retain explicit denominator-zero state rather than becoming zero or an unexplained perfect score.

**Miata regrade:** The preserved V4 result remains 32 correct of 42 scorable facts with `C / E / U = 32 / 10 / 0`: CEFC `0.7619047619047619`; attempted accuracy `0.7619047619047619`; required error rate `0.23809523809523808`; Unknown rate `0.0`; provenance success `31 / 31`. No classification rule, runtime, catalog, input, provenance, or ground-truth change was made after observing the formal V4 result.

**Status:** Grader candidate pending PR review and merge.

### 55. Froze the deterministic grader and added the Hybrid vPIC + Web hypothesis
**Decision:** PR #7 merged before any additional benchmark run, freezing `deterministic-benchmark-grader-v1` and its reviewed comparison rules. The Hybrid runner then adds exact-VIN NHTSA vPIC structured seeds only for nonblank DisplacementCC, EngineHP, TransmissionSpeeds, and unambiguous DriveType values; all remaining catalog fields use the unchanged Full-Web ResearchAgent.

**Boundary:** Blank or ambiguous vPIC data is Unknown/not supplied, never equipment absence. Full-Web runtime, frozen benchmark, inputs, catalog, grader, and agent behavior remain unchanged. No Hybrid provider execution has occurred; its resource and quality benefit remains a benchmark hypothesis.

**Status:** Kept as unexecuted candidate implementation.


### 53. Completed the first structurally successful Full-Web V4 Miata run
**Execution:** After the explicitly authorized retry control was simplified, ran only `01_miata_gt_auto_ground_truth.json` with `--live --retry-failed` on Gemini 3.6 Flash. All four Phase A batches and all four matching Phase B batches completed in the frozen 24/24/24/19 shapes, with no automatic retry or other fixture execution.

**Result:** The run succeeded with 8 model calls, 22 observed Search queries, 60 grounded sources, 151,813 ms total worker latency, 61,971 total tokens, and estimated cost $0.13619625. Phase A used 83,719 ms and $0.0557865; Phase B used 68,094 ms and $0.08040975. All 91 researched field IDs validated exactly once, the deterministic power-to-weight fact was known, and the final canonical result contained 92 facts (80 known, 1 Unknown, 0 conflicted; 79 known facts with provenance). No grading or correctness score was run. The previous failed V4 result was archived, and V1/V2/V3 evidence remains preserved.

**Status:** Kept as formal ungraded benchmark evidence pending review.


### 2. Chose CarGurus as the V1 marketplace surface
**Decision:** Support one marketplace for the hackathon V1, with CarGurus as the primary browsing surface.

**Why:** Narrowing to one marketplace reduces integration complexity and allows the evaluation to focus on the quality of the agentic research workflow rather than cross-site DOM handling.

**Implementation note:** The marketplace parser should be isolated behind a CarGurus adapter so another marketplace can be added later.

**Status:** Kept.

---

### 3. Chose browser extension as interface, not core architecture
**Decision:** Use a browser extension overlay as the preferred user-facing interface, while keeping the research/evaluation pipeline independent from the extension.

**Why:** This makes the product visually useful during real browsing without making the core system dependent on brittle page parsing.

**Fallback:** A pasted-listing or standalone workflow may be retained so the complete system can still run if the marketplace DOM changes.

**Status:** Kept.

---

### 4. Chose one agent with deterministic supporting code
**Decision:** Use one research/reconciliation agent with tools rather than a multi-agent architecture.

**Agent responsibilities:**
- interpret exact vehicle configuration
- identify missing or inadequate enthusiast fields
- create targeted research questions
- research gaps
- reconcile conflicting evidence
- detect trim, package, transmission, drivetrain, model-year, and market dependencies
- return `Unknown` when evidence is insufficient

**Deterministic-code responsibilities:**
- API requests
- schema validation
- normalization
- unit conversion
- calculations
- caching
- filtering and sorting
- evaluation grading
- UI rendering

**Why:** Purposeful agent behavior is more important than agent count. One agent reduces orchestration overhead, trace complexity, and failure surface while keeping judgment tasks agentic.

**Status:** Kept.

---

### 5. Chose Car2DB as the primary structured data layer
**Decision:** Use Car2DB as the initial structured vehicle-specification source.

**Why:** It provides broad structured coverage while allowing the agent to spend web-research effort only where enthusiast-important fields are missing, weak, stale, or ambiguous.

**Observed limitation:** Car2DB can be incomplete, market-oriented differently, stale, or too generic for enthusiast hardware and exact configuration dependencies.

**Status:** Kept as a base source, not treated as authoritative ground truth.

---

### 6. Rejected a second structured vehicle API for V1
**Decision:** Do not add another structured API solely to fill Car2DB gaps.

**Why:** A second structured API would add integration and reconciliation complexity during a short hackathon. Targeted web research is more useful for testing the agent's ability to identify and close information gaps.

**Status:** Removed from V1.

---

### 7. Established Full-Web vs Hybrid comparison
**Decision:** Evaluate two workflows on the same vehicle cases.

**Full-Web:** Agent begins from the listing and researches enthusiast-relevant information from web sources.

**Hybrid:** Agent begins with Car2DB structured facts and researches only missing, ambiguous, or inadequate fields.

**Why:** This creates a measurable experiment rather than assuming that structured grounding improves the result.

**Status:** Kept.

---

### 8. Selected 11 fixed evaluation vehicles
**Decision:** Use 11 exact US-market vehicle configurations.

**Why:** The hackathon suggests 10+ cases where appropriate, and 11 cases provide enough diversity to test different failure modes while remaining manageable.

**Evaluation set:**
1. 2026 Mazda MX-5 Miata Grand Touring Automatic
2. 2024 MINI Cooper S 2-Door
3. 2022 Toyota GR86 Base
4. 2019 Ford Mustang EcoBoost Premium
5. 2024 Hyundai Elantra N Line
6. 2018 Cadillac ATS Base
7. 2026 Jeep Wrangler Rubicon 4xe
8. 2025 Dodge Charger Daytona
9. 2022 Kia Soul GT-Line Turbo
10. 2023 Tesla Model Y Long Range AWD
11. 2026 Subaru WRX Limited CVT

**Status:** Kept.

---

### 9. Deliberately selected vehicles for different failure modes
**Decision:** The evaluation set is not a random list of enthusiast cars. Each case should stress a distinct data-resolution problem.

Examples:
- transmission-dependent equipment
- ADAS mislabeling
- trim contamination
- performance-package dependency
- same engine family with different output
- wrong-spec inheritance
- PHEV and complex 4WD architecture
- EV trim/output ambiguity
- near-identical subtrim naming
- mid-year hardware changes
- transmission-dependent AWD architecture

**Why:** This provides a stronger evaluation of reasoning and configuration resolution than testing eleven similar vehicles.

**Status:** Kept.

---

### 10. Chose an objective-only scored schema
**Decision:** The scored core will contain only objective, verifiable enthusiast facts.

**Included examples:**
- horsepower
- torque
- curb weight
- transmission mechanism
- drivetrain architecture
- differential type
- suspension hardware
- brake hardware
- wheel/tire configuration
- measured 0–60
- measured skidpad
- ADAS capabilities
- package and configuration dependencies

**Excluded from scored output:**
- steering feel
- exhaust sound quality
- fun factor
- ride feel
- subjective handling
- interior quality
- reliability reputation
- tuning potential

**Why:** Objective fields can be supported by evidence and graded reproducibly.

**Status:** Kept.

---

### 11. Added objective exhaust hardware under Engine & Performance
**Decision:** Add exhaust-system fields to the Engine & Measured Performance category.

**Fields include:**
- standard vs factory performance exhaust
- active valves
- selectable exhaust modes
- outlet configuration
- option/package dependency
- trim/transmission dependency where applicable
- provenance/confidence

**Why:** Exhaust sound is subjective, but whether a vehicle has an active or factory performance exhaust is objective and enthusiast-relevant.

**Status:** Added.

---

### 12. Added detailed ADAS capability instead of yes/no labels
**Decision:** Model driver-assistance systems as individual capabilities rather than inferring a bundle from labels such as “adaptive cruise.”

**Fields include:**
- ACC type and operating range
- stop-and-go capability
- lane departure warning
- active lane keeping
- lane centering
- hands-on vs hands-free operation
- operating domain
- system name
- subscription requirement/cost
- hardware/software dependency
- trim/package dependency

**Why:** Marketplace ADAS labels can be misleading. Vehicles such as the 2024 MINI Cooper S and 2026 Wrangler 4xe demonstrate that one capability does not imply another.

**Status:** Kept.

---

### 13. Added configuration-dependency detection as a core capability
**Decision:** Treat configuration dependencies as a cross-category meta-layer rather than a normal isolated field.

**Why:** Exact transmission, drivetrain, trim, package, build date, or hardware generation can change multiple enthusiast-relevant facts at once.

**Canonical case:** 2026 MX-5 Miata Grand Touring automatic vs manual.

**Status:** Kept.

---

### 14. Ground truth must be independent from Car2DB
**Decision:** Do not use Car2DB to define the answer key.

**Why:** Car2DB is part of the Hybrid system being evaluated. Grading against Car2DB would partially evaluate the system against itself.

**Ground-truth hierarchy for factory equipment:**
1. manufacturer documentation
2. authoritative technical documentation
3. reputable automotive publication
4. lower-tier secondary source only when necessary

**Measured performance:** prioritize reputable instrumented tests.

**Status:** Kept.

---

### 15. Freeze ground truth before comparative runs
**Decision:** Build and verify `ground_truth.json` before scoring Full-Web or Hybrid outputs.

**Why:** This prevents the answer key from drifting after seeing agent results.

**Status:** Kept.

---

### 16. Use ranges for legitimate instrumented-test disagreement
**Decision:** When reputable instrumented tests produce different values, preserve an accepted range rather than averaging them into one artificial “true” number.

**Why:** An average may be a number that no source actually measured and creates false precision.

**Rule:**
- factory specification: exact value when configuration is known
- instrumented performance: accepted range of comparable reputable tests
- materially different test conditions or clear outliers: preserve separately rather than automatically widening the accepted range

**Status:** Kept.

---

### 17. `Unknown` is allowed and should not be treated as hallucination
**Decision:** The system may explicitly return `Unknown` when evidence is insufficient.

**Scoring behavior:**
- if ground truth is knowable and the agent returns `Unknown`, coverage decreases
- it is not counted as a fabricated factual error
- if the ground-truth field is genuinely unavailable or not applicable, exclude it from scoring as appropriate

**Why:** The system should be rewarded for avoiding unsupported claims while still being incentivized to find available information.

**Status:** Kept.

---

### 18. Primary metric: Correct Enthusiast Fact Coverage
**Decision:** Use Correct Enthusiast Fact Coverage as the primary evaluation metric.

**Definition:**

`correctly surfaced scorable facts / total scorable ground-truth facts`

**Why:** Accuracy alone can reward an agent that answers only easy fields. Correct coverage rewards finding useful information while still requiring correctness.

**Secondary metrics:**
- accuracy of attempted facts
- error rate
- unknown rate
- provenance/source success
- web calls/searches per vehicle
- latency per vehicle
- estimated cost per vehicle

**Status:** Kept.

---

## Current Baseline and Experiment Plan

### Baseline
A Full-Web research agent that starts from the vehicle/listing context and searches the web for the complete enthusiast schema.

### Candidate
A Hybrid agent that starts from Car2DB structured facts, identifies missing/weak fields, and performs targeted web research only where needed.

### Hypothesis
Structured grounding plus targeted gap research will improve correct enthusiast-fact coverage and/or reduce research cost, latency, and unnecessary searches compared with researching every field from the web.

This is a hypothesis, not a result. Final claims must be based on recorded evaluation evidence.

---

## Schema and Ground-Truth Foundation

### 19. Finalized and saved the V1 Enthusiast Lens schema
**Decision:** Freeze the V1 product/evaluation schema as a standalone specification rather than leaving it only in conversation context.

**Artifact:** `Enthusiast_Lens_V1_Schema_and_Eval_Spec.docx`

**Schema scope:**
- Engine & Measured Performance
- Transmission
- Drivetrain & Differentials
- Suspension, Axles & Chassis
- Brakes, Wheels & Tires
- Audio
- Driver Assistance & Highway Automation
- Configuration Dependencies
- Provenance & Confidence

**Objective-only rule:** Scored fields must be objectively verifiable. Subjective attributes such as steering feel, exhaust sound quality, ride feel, fun factor, and interior quality are excluded from the scored core.

**Additional refinement:** Objective exhaust-system hardware was added under Engine & Measured Performance, including standard/performance exhaust status, active valves, selectable modes, outlet configuration, and package/trim dependencies.

**Why:** The schema needed to be frozen before building answer keys so that research and scoring would not drift as individual vehicles were investigated.

**Status:** Kept and saved outside conversation context.

---

### 20. Defined the machine-readable ground-truth fixture format
**Decision:** Create a JSON Schema that defines how every evaluation vehicle's ground truth must be represented.

**Artifact:** `ground_truth.schema.json`

**Format includes:**
- exact vehicle identity and market
- trim, transmission, drivetrain, packages, build-date/hardware notes
- one structured record per ground-truth fact
- fact status: `known`, `not_available`, `not_applicable`, or `unresolved`
- exact values, accepted alternatives, accepted ranges, and numeric tolerances
- per-fact scoring eligibility
- verification status and confidence
- explicit configuration dependencies
- structured source evidence and configuration-match quality
- fixture lifecycle: `draft` → `verified` → `frozen`

**Source rule:** Car2DB cannot define ground truth because it is an input to the Hybrid system being evaluated.

**Measured-value rule:** When comparable reputable instrumented tests disagree, retain an accepted range rather than averaging them into a synthetic value.

**Architecture decision:** Maintain one ground-truth JSON file per vehicle/case rather than one large combined file. Python will load and validate all fixtures during evaluation.

**Why:** A formal schema makes the benchmark deterministic, reviewable, versionable, and reproducible.

**Status:** Kept.

---

### 21. Built the first real ground-truth fixture using the 2026 MX-5 Miata
**Decision:** Use the 2026 Mazda MX-5 Miata Grand Touring soft-top automatic as the first populated ground-truth case and as the pattern for subsequent fixtures.

**Artifact:** `01_miata_gt_auto_ground_truth.json`

**Initial result:**
- 50 facts captured
- 44 marked verified
- 46 initially scorable
- 6 left proposed/non-final rather than guessed
- JSON validated successfully against `ground_truth.schema.json`

**Important configuration finding:** Mazda's 2026 documentation shows meaningful hardware differences between Grand Touring manual and automatic configurations. The automatic must not inherit manual-only equipment such as the asymmetric limited-slip differential, Bilstein dampers, sport-tuned suspension, front shock-tower brace, DSC-Track, and induction sound enhancer.

**Conservative-ground-truth decision:** Exact-configuration 0–60, skidpad, exhaust-hardware absence, and detailed 2026 MRCC operating behavior were not forced into scored ground truth without sufficient direct evidence.

**Why:** The first fixture tested whether the proposed schema could represent exact values, dependencies, unknowns, evidence quality, and non-scorable gaps without manufacturing certainty.

**Learning:** A smaller verified answer key is preferable to a larger answer key containing plausible but weakly supported facts.

**Status:** Kept as the reference implementation for subsequent fixtures.

---

## Current Next Work

- resolve and freeze under-specified vehicle configurations
- preserve local evidence needed for reproducibility, especially listing/image evidence
- finish verification of remaining proposed ground-truth facts
- mark the completed fixtures `frozen` before comparative runs
- implement the Full-Web and Hybrid evaluation paths
- run identical benchmark cases through both systems
- export raw results and comparison metrics
- document failed/removed experiments as they occur

---

## 2026-08-28 — MINI ACC Benchmark Refinement

### 22. Replaced the generic MINI ACC case with paired true/false subcases
**Decision:** Replace the single generic MINI ACC benchmark with two frozen 2020 MINI Cooper S 2-Door subcases:

- **False positive:** CarGurus listing `443747910`, VIN `WMWXR5C02L2L92322`  
  CarGurus marks Adaptive Cruise Control as present, but the vehicle's steering-wheel controls do not show the ACC distance-control hardware.

- **True positive:** CarGurus listing `451744696`, VIN `WMWXR5C00L2M13510`  
  CarGurus marks Adaptive Cruise Control as present, and the vehicle's steering-wheel controls do show the ACC distance-control hardware.

**Why:** A single false-positive case could reward a system that simply learns to distrust MINI ACC data. The paired design requires the system to resolve the exact vehicle instead of applying a blanket rule.

**Ground-truth method:** Use the physical steering-wheel ACC controls as the decisive vehicle-specific evidence, while preserving the CarGurus feature claim, listing metadata, VIN, and supporting evidence locally.

**Reproducibility requirement:** The benchmark must not depend on the live listings remaining available. Freeze the relevant listing metadata and steering-wheel image evidence into the repository.

**Status:** Kept.


### 23. Locked the 2022 Toyota GR86 Base benchmark to the 6-speed automatic
**Decision:** Use the 2022 Toyota GR86 Base with the 6-speed automatic transmission for the frozen benchmark configuration.

**Why:** Toyota's 2022 GR86 Active Safety Suite, including Adaptive Cruise Control, is tied to the automatic-transmission configuration. The automatic also changes manufacturer-published 0–60 performance and other transmission-dependent specifications.

**Evaluation value:** This turns the GR86 into a clearer configuration-dependency case: the system must not transfer manual-transmission performance or equipment assumptions onto the automatic car.

**Status:** Kept.


### 24. Locked the 2019 Mustang EcoBoost Premium to Fastback + 10-speed automatic and investigated S vs L selector variants
**Decision:** Use the 2019 Ford Mustang EcoBoost Premium Fastback with the 10-speed SelectShift automatic.

**Investigation:** A possible S-versus-L selector variation was investigated before freezing the transmission detail. Ford's 2019 US Mustang owner manual documents the automatic selector as `P-R-N-D-S`, with `S` providing Sport behavior and permanent SelectShift manual control through the steering-wheel paddles. Ford's 2019 order guide also lists paddle shifters with the 10-speed automatic.

**Finding:** No Ford primary-source evidence was found for a `P-R-N-D-L` / Low-selector version of the 2019 US Mustang 10-speed. `L`-selector behavior is documented on later Mustang configurations without the same paddle/SelectShift setup.

**Evaluation decision:** The 2019 benchmark will expect the `S` selector unless VIN-specific primary evidence later establishes otherwise. Do not create a second 2019 transmission variant based only on later-model evidence.

**Still unresolved:** EcoBoost Performance Package, Active Valve Performance Exhaust, and Safe & Smart/ACC equipment status.

**Status:** Kept.


### 25. Revised the Mustang benchmark from 2019 to 2020 to use the 2.3L High Performance Package + ACC
**Decision:** Change the Mustang benchmark to a **2020 Ford Mustang EcoBoost Premium Fastback, 10-speed SelectShift automatic, equipped with the 2.3L High Performance Package (67E) and Ford Safe & Smart Package (77S) with Adaptive Cruise Control**.

**Why the model year changed:** Ford introduced the 2.3L High Performance Package for model year 2020. It was not available on the 2019 Mustang. The earlier 2019 EcoBoost Performance Package used the standard-output EcoBoost engine.

**Ground-truth implications:**
- 2.3L High Performance EcoBoost: **330 hp / 350 lb-ft**
- 10-speed SelectShift automatic
- Active Valve Performance Exhaust included with the High Performance Package
- GT-derived larger front brakes / 4-piston fixed calipers and additional chassis/cooling hardware
- Ford Safe & Smart Package explicitly included for the benchmark
- Adaptive Cruise Control = **true**

**Evaluation value:** This case now tests whether the system distinguishes the 330-hp High Performance Package from the standard 310-hp EcoBoost, correctly resolves performance-package hardware, and independently recognizes the optional Safe & Smart/ACC package.

**Status:** Kept.


### 26. Added Premium Plus digital cluster and B&O audio to the 2020 Mustang benchmark
**Decision:** Further specify the 2020 Mustang EcoBoost Premium benchmark with **Equipment Group 201A / Premium Plus**, the **12-inch configurable digital instrument cluster**, and the **12-speaker B&O premium audio system with subwoofer**.

**Clarification:** Shaker Pro was used on earlier Mustang model years. For the 2020 benchmark, the premium-audio target is B&O.

**Why:** This adds another independent package-resolution layer. The agent must distinguish:
- Premium trim from Premium Plus / 201A
- analog vs 12-inch digital instrumentation
- standard audio vs B&O premium audio
- the separate High Performance Package
- the separate Safe & Smart / ACC package

**Evaluation value:** The case now tests whether the system can reconstruct a configuration made from several overlapping option groups rather than assuming that one trim badge implies all premium or performance equipment.

**Status:** Kept.


### 27. Locked the 2024 Elantra N Line as ACC-absent but active lane-assist capable
**Decision:** Keep the 2024 Hyundai Elantra N Line as an ADAS-separation benchmark with **Smart Cruise Control with Stop & Go = false**, while **Lane Keeping Assist = true** and **Lane Following Assist = true**.

**Clarification:** Hyundai's Lane Following Assist provides active steering assistance to help center the car in its lane. This means the N Line can have active lateral assistance even though Smart Cruise Control is omitted.

**Why:** This is a valuable failure mode because a simplistic system may incorrectly assume that active lane assistance and adaptive cruise are bundled together.

**Evaluation value:** The agent must independently resolve longitudinal and lateral driver-assistance capabilities rather than inferring one from the other.

**Status:** Kept.


### 28. Locked the 2018 Cadillac ATS Base benchmark to the sedan body style
**Decision:** Use the **2018 Cadillac ATS Base sedan** for the benchmark.

**Why:** Fixing the body style removes one unnecessary source of ambiguity while preserving the more useful drivetrain, transmission, and option-package questions.

**Still unresolved:** RWD vs AWD, transmission choice, and package-dependent equipment/ADAS.

**Status:** Kept.


### 29. Locked the 2018 Cadillac ATS Base sedan to RWD + 6-speed manual
**Decision:** Use the **2018 Cadillac ATS Base sedan with rear-wheel drive and the 6-speed manual transmission**.

**Why:** This deliberately gives the benchmark an enthusiast-oriented manual configuration and removes the RWD/AWD and manual/automatic ambiguity that existed in the draft fixture.

**Evaluation value:** The system must not inherit AWD or 8-speed automatic specifications simply because those configurations were also available within the ATS model line.

**Still unresolved:** Only package-dependent equipment/ADAS fields that are useful enough to score.

**Status:** Kept.


### 30. Corrected the Wrangler 4xe benchmark to MY2025 and refined the ADAS taxonomy
**Decision:** Change the benchmark from a proposed **2026 Jeep Wrangler Rubicon 4xe** to the **2025 Jeep Wrangler Rubicon 4xe**, the final completed Wrangler 4xe model year.

**Why the model year changed:** Jeep has since discontinued Wrangler 4xe production. Preliminary 2026 fleet material had listed a 4xe, but the production program ended after model year 2025. The benchmark therefore uses the last real production model year rather than a canceled configuration.

**ADAS refinement:** The benchmark now distinguishes the lateral and longitudinal systems explicitly:
- Adaptive Cruise Control = **true**
- ACC can brake the automatic-transmission vehicle to a full stop
- minimum ACC set speed = **20 mph**
- Lane Keeping Assist = **false**
- continuous Lane Centering / Lane Following = **false**
- Hands-Free Highway Assist = **false**

**Important correction to reasoning:** The project will not claim as ground truth that the solid front axle caused Jeep to omit lane-keeping/lane-centering. Wrangler steering architecture and highway precision may make such systems harder to implement, but no Jeep primary source was found establishing that causal explanation.

**Evaluation value:** This case tests whether the agent can recognize that a vehicle may have capable adaptive longitudinal control without assuming any active lateral-control system.

**Status:** Kept.


### 31. Locked the 2025 Dodge Charger Daytona benchmark to Scat Pack
**Decision:** Use the **2025 Dodge Charger Daytona Scat Pack** rather than the R/T.

**Why:** The Scat Pack creates a denser enthusiast-data benchmark and makes the separate Track Package dependency meaningful.

**Ground-truth implications:**
- maximum output = **670 hp**
- maximum torque = **627 lb-ft**
- manufacturer 0–60 = **3.3 seconds**
- dual-motor AWD EV architecture remains unchanged
- Track Package is still treated as a separate option rather than assumed from the Scat Pack trim

**Evaluation value:** The agent must distinguish Scat Pack from R/T output while also avoiding the opposite mistake of assuming that every Scat Pack automatically has Track Package brakes, wheels/tires, and adaptive-damper hardware.

**Status:** Kept.


### 32. Explicitly excluded the Track Package from the Charger Daytona Scat Pack benchmark
**Decision:** The **2025 Dodge Charger Daytona Scat Pack benchmark will not include the Track Package**.

**Why:** Track Package hardware is optional and should not be inferred simply because the vehicle is a Scat Pack.

**Evaluation value:** The system must correctly identify Scat Pack output while avoiding false inheritance of Track Package-specific equipment such as its upgraded brake, wheel/tire, and adaptive-damper hardware.

**Ground-truth rule:** `Track Package equipped = false`.

**Status:** Kept.


### 33. Locked the 2023 Model Y benchmark to HW4 / AI4 while separating hardware capability from FSD entitlement
**Decision:** Use a **2023 Tesla Model Y Long Range AWD equipped with HW4 / AI4**.

**Why:** The 2023 Model Y is a useful transition-year case because both HW3 and HW4 vehicles exist. The benchmark intentionally selects the newer HW4 configuration so the system must resolve the exact hardware generation rather than assuming all 2023 Model Ys are identical.

**Important terminology correction:** HW4 is not required merely to run any version of FSD (Supervised). Tesla currently allows FSD subscription eligibility on FSD Computer 3.0 or newer, and HW3 vehicles can receive an HW3-specific/lite FSD branch. The benchmark uses HW4 because it represents the newer/full hardware path, not because HW3 has zero FSD capability.

**Ground-truth separation:**
- Hardware generation = **HW4 / AI4**
- FSD hardware capability = **HW4/AI4-capable**
- Current FSD purchase/subscription entitlement = **separate and not inferred from hardware**

**Evaluation value:** The agent must distinguish model year, hardware generation, and software entitlement instead of collapsing them into a single “FSD capable” label.

**Status:** Kept.


### 34. Completed the first full ground-truth freeze-readiness pass
**Decision:** Run a systematic pass over every benchmark fixture before implementing the comparative agents.

**Result:** The benchmark now contains **11 vehicle families and 12 fixture files** because the MINI family intentionally contributes paired ACC true-positive and false-positive cases.

**Frozen:** **10 fixtures** now have no unresolved/proposed scored facts and validate against `ground_truth.schema.json`.

**Remaining blocker:** Only the two MINI ACC fixtures remain draft. Their CarGurus structured claims are frozen locally, but the steering-wheel image evidence still needs to be saved into the repository before the vehicle-specific ACC true/false facts are marked verified.

**Conservative cleanup decisions:**
- Removed weak exact-2026 Miata MRCC-detail and exhaust-absence claims from scoring rather than inferring them.
- Removed stale 2019 Mustang draft-package facts after the benchmark moved to the 2020 High Performance Package configuration.
- Resolved the ATS Base manual benchmark with `ACC=false` and the manual-specific limited-slip differential.
- Verified the Wrangler 4xe solid-axle facts against 2025 documentation.
- Removed Tesla EPA range from scoring because wheel configuration is not fixed, and kept mutable FSD software entitlement non-scorable.
- Upgraded the Kia Soul Turbo FWD fact to official Kia-source verification.

**Reproducibility rule reinforced:** A fixture is not frozen merely because a fact seems obvious; unsupported or configuration-dependent claims are either independently evidenced or excluded from scoring.

**Status:** Kept.


### 35. Replaced the MINI ACC false-positive case with a stronger CarGurus example
**Decision:** Replace the earlier MINI false-positive listing with **2021 MINI Cooper S 2-Door CarGurus listing `435848455`, VIN `WMWXR5C02M2N13321`**.

**Why:** CarGurus explicitly lists **Adaptive Cruise Control** in the structured `safetyFeatures` data for this vehicle. The listing also shows a Driver Assistance Package, while the vehicle-specific steering-wheel controls were visually checked and do **not** show the ACC distance-control controls.

**Evaluation value:** This creates a cleaner false-positive benchmark because the incorrect ACC claim is present in the marketplace's structured feature data itself, not merely buried in free-text dealer copy.

**Reproducibility requirement:** Save the steering-wheel image locally before freezing `ACC=false`.

**Status:** Kept.


### 36. Captured the MINI false-positive steering-wheel evidence and froze that fixture
**Decision:** Preserve the steering-wheel photo for the 2021 MINI Cooper S false-positive case directly in the benchmark repository.

**Evidence:** `evidence/02_mini/false_positive_steering_wheel.jpg`

**Observation:** The steering-wheel cruise cluster contains RES/CNCL, SET, +/- and the standard cruise-control button. The smooth area immediately to the right does not contain the additional ACC following-distance controls, while CarGurus explicitly reports `Adaptive Cruise Control` in structured `safetyFeatures`.

**Result:** The false-positive MINI fixture is now marked `verified` and `frozen`.

**Remaining MINI blocker:** The true-positive steering-wheel image still needs to be saved locally before that fixture can be frozen.

**Status:** Kept.


### 37. Captured the MINI true-positive steering-wheel evidence and completed benchmark freeze
**Decision:** Preserve the steering-wheel photo for the 2020 MINI Cooper S true-positive case directly in the benchmark repository.

**Evidence:** `evidence/02_mini/true_positive_steering_wheel.jpg`

**Observation:** The steering wheel shows the ACC following-distance controls to the right of the main cruise-control cluster, confirming that Adaptive Cruise Control is actually equipped.

**Result:** The true-positive MINI fixture is now marked `verified` and `frozen`. With both MINI evidence images now saved locally, the full benchmark is complete.

**Benchmark status:** All **12 benchmark fixtures** are now frozen across **11 vehicle families**.

**Status:** Kept.


### 38. Performed an independent pre-evaluation audit and corrected benchmark weaknesses
**Decision:** Re-audit the entire frozen benchmark before implementing or running the Full-Web and Hybrid systems.

**Corrections made:**
- Fixed the stale freeze-readiness report after the MINI fixtures were frozen.
- Corrected the 2021 MINI false-positive evidence semantics and switched its control-reference documentation to the 2021 MINI owner manual.
- Clarified that the Mustang B&O 12-speaker system is **separate option 583**, not automatically included by 201A, and added it explicitly to the benchmark configuration.
- Replaced migrated/dead Ford historical PDF URLs with a surviving mirror of the original Ford Division 2020 order guide while retaining primary Ford HPP evidence.
- Grounded the 2023 Model Y HW4 benchmark to exact VIN **7SAYGDEE3PF885285** rather than leaving HW4 as an unsupported stipulated attribute.
- Added an explicit scoring policy: calculate coverage per fixture, average MINI's two subcases into one MINI family score, then macro-average the original **11 vehicle families**. This prevents unequal fact counts and the paired MINI design from biasing the headline metric.
- Added `audit_ground_truth.py` for repeatable structural validation.

**Audit result:** All **12 fixtures** pass JSON Schema validation, are frozen, have no duplicate field IDs, contain no scorable unresolved/unverified facts, and every scorable fact has at least one source marked as supporting its value.

**Status:** Kept.

---

## 2026-08-29 — V1 Implementation Architecture

### 39. Defined the official product surfaces and shared-core reproduction path
**Decision:** Use a **Google Chrome Manifest V3 browser extension** as the primary real-world interface. Hackathon judges will load it as an unpacked extension, so Chrome Web Store approval or publication is not required. **CarGurus** is the only marketplace integration officially targeted for V1. Microsoft Edge compatibility may occur because it is Chromium-based, but Edge is not an official target; Firefox and Safari are out of scope for V1.

**Reproduction path:** Maintain a standalone demo application as the guaranteed hackathon reproduction path. The standalone application and Chrome extension use the same core pipeline and canonical result schema, so judges can reproduce the system without extension installation, a surviving live listing, or dependence on the current CarGurus DOM.

**Why:** Preserve a convincing real-world product experience while preventing browser-store approval and live-site fragility from becoming evaluation blockers.

**Status:** Kept.


### 40. Froze the V1 technology stack and scoped Vehicle Knowledge Store
**Technology stack:** Use **Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, httpx, and pytest** for the backend and core pipeline; **SQLite** as the default runtime database, configured through `DATABASE_URL`, with a PostgreSQL-compatible future direction; the **OpenAI Responses API** behind a thin internal adapter; **React, TypeScript, Vite, and Tailwind CSS** for the shared frontend and standalone demo; and **Chrome Manifest V3** for the extension. The OpenAI Agents SDK is not required for V1.

**Persistence decision:** Add a scoped **Vehicle Knowledge Store** that preserves exact vehicle/configuration identity, normalized accepted vehicle facts, provenance/source relationships, and analysis-run metadata. Raw API cache, reusable runtime knowledge, evaluation results/trajectories, and the frozen evaluation answer key remain distinct data domains. Only validated and accepted facts may be promoted into reusable knowledge.

**Evaluation safeguard:** Primary Full-Web versus Hybrid benchmark runs use fresh, isolated runtime databases by default so persistent knowledge cannot contaminate the comparison. Frozen answers, grader results, and hidden evaluation evidence may never seed runtime knowledge.

**Why:** This gives V1 a production-shaped persistence boundary and a path to reuse already researched knowledge without requiring judges to operate PostgreSQL or other external infrastructure.

**Status:** Kept.


### 41. Hackathon alignment checkpoint and transition to implementation
**Decision:** Architecture planning is considered complete after Step 3.5. Development priority now shifts to a working Full-Web baseline, a working Hybrid candidate, deterministic evaluation, and measured evidence. The primary implementation goal is measurable end-to-end improvement rather than additional architecture expansion.

**Scope discipline:** The Vehicle Knowledge Store remains intentionally limited and must not become the main project. The full engineering `CHANGELOG.md` will be preserved, while the final submission should also include a shorter evidence-driven Improvement Changelog focused on baseline -> experiments -> final result.

**Experiment requirement:** Preserve and document at least one genuine implementation experiment that is tested and later removed or rejected.

**Submission requirements:** The README/final submission must disclose what existed before the hackathon and what was added during it. Before submission, check licenses and service terms for Car2DB, CarGurus, OpenAI, and all shipped dependencies.

**Status:** Kept.


### 42. Selected Gemini 3.7 Flash behind a provider-neutral model adapter
**Decision:** Use **Gemini 3.7 Flash** as the V1 research/reconciliation model through the paid Gemini Developer API tier, with **medium** thinking as the initial default and Google Search grounding as the intended web-research capability where appropriate.

**Evaluation safeguard:** Full-Web and Hybrid will use equivalent model, thinking, and search settings. Model, search, token, resource usage, and estimated cost will be captured per run as evaluation metrics.

**Architecture boundary:** Provider-specific implementation remains behind a provider-neutral internal model adapter, removing OpenAI-specific coupling from the V1 architecture. No unnecessary orchestration framework or Gemini SDK is introduced in this step.

**Why:** Gemini 3.7 Flash provides the selected agentic/search capability with expected hackathon-scale spend comfortably within a small budget while retaining future provider portability.

**Status:** Kept.


### 43. Replaced Car2DB with NHTSA vPIC as the V1 structured data source
**Decision:** Car2DB was rejected for V1 after confirming its free trial exposes only a limited demo database and full benchmark coverage would require paid access. Weekend/time constraints made obtaining temporary access impractical. NHTSA vPIC is now the V1 structured vehicle-data provider.

**Provider boundary:** vPIC requires no API key and provides manufacturer-reported VIN decoding data for US-market vehicles. Hybrid will use vPIC as structured seed data, then research only missing, ambiguous, and configuration-sensitive enthusiast facts. Missing vPIC values are interpreted as `Unknown` / not supplied by NHTSA, never automatically as feature absence. vPIC is **not** ground truth.

**Evaluation safeguard:** Full-Web remains the baseline without vPIC structured grounding.

**Status:** Kept.


### 44. Froze the reproducible benchmark runtime-input corpus
**Decision:** Create `evals/inputs/benchmark_inputs.json` as the sole benchmark runtime-input corpus, separate from the immutable answer key in `evals/ground_truth/`. Evaluated systems receive vehicle identity, exact VIN/listing context, advertised packages/options, and input-only source metadata; they do not receive expected enthusiast facts, tolerances, grader fields, or answer-key provenance.

**Resolution result:** Eight of the nine previously missing exact VINs were resolved through public vehicle listings or dealer window stickers and verified with live NHTSA vPIC decoding. Together with the three existing exact-VIN inputs, **11 of 12 fixtures** are runtime-ready across the original **11 vehicle families**.

**Unresolved case:** The 2025 Dodge Charger Daytona Scat Pack remains blocked. Public listings confirmed nearby Scat Pack/AWD vehicles, but no source found reliably proved an exact VIN was configured **without the Track Package**. No close match was forced into the corpus.

**Input integrity:** Added deterministic validation for plausible and unique VINs, unique fixture IDs, exact manifest mapping, required identity/readiness state, source-snapshot references, and recursive rejection of answer-key fields. Volatile listing identity metadata is preserved under `evals/inputs/evidence/` without enthusiast conclusions.

**Evaluation boundary:** Benchmark inputs, frozen ground truth, scored results, and trajectories are explicit separate domains. Runtime/evaluated code consumes `evals/inputs/`; only deterministic grading and audit code may read `evals/ground_truth/`.

**Status:** Kept.


### 45. Corrected the 2025 Charger Daytona benchmark to the production Track Package configuration
**Decision:** Correct the 2025 Dodge Charger Daytona Scat Pack AWD benchmark from the original explicitly non-Track configuration to the production Track Package configuration.

**Why:** During runtime-input VIN research, 15 real MY2025 Scat Pack VINs were checked against OEM window stickers and every one carried the Track Package. Additional production evidence showed that the earlier non-Track assumption came from pre-production package documentation and did not support a real production configuration. The original fixture therefore represented an unsupported non-production configuration.

**Correction:** Because no Full-Web or Hybrid evaluation had run, the benchmark was corrected rather than preserving a known-invalid configuration. The Charger fixture is now tied to public VIN `2C3CDBDK2SR559586` with preserved OEM Track Package evidence. Track Package-dependent ground-truth facts were revalidated, and the runtime input exposes only legitimate VIN/identity/package evidence while the mechanical consequences remain in ground truth.

**Lesson:** Pre-production package documentation can disagree with actual production configuration availability; exact model-year/VIN evidence wins.

**Status:** Kept.


### 46. Moved implementation to GitHub PR-based development
**Decision:** Published the local implementation history through the corrected frozen benchmark to a private GitHub remote before agent implementation began, preserving existing history rather than squashing or rewriting it.

**Workflow:** Future meaningful implementation work will normally occur on `feature/...`, `fix/...`, or `docs/...` branches and enter `main` through pull requests. Expected branch names include `feature/gemini-research-agent`, `feature/full-web-baseline`, `feature/hybrid-pipeline`, `feature/vehicle-knowledge-store`, `feature/judge-demo`, and `feature/chrome-extension`. Pull requests provide reviewable checkpoints for implementation changes, experiments, verification results, and benchmark-integrity checks.

**Publication state:** The repository remains private while development, reproduction documentation, service-term review, and publication checks are still underway. It will be made accessible to judges during final submission preparation.

**Why:** This improves auditability, rollback, review, and the evidence trail for the hackathon.

**Status:** Kept.


### 47. Implemented the Gemini research/reconciliation agent with trace capture
**Decision:** Implement the V1 research boundary with the official `google-genai` SDK, Gemini 3.7 Flash, medium thinking, Google Search, Pydantic structured output, and a provider-neutral adapter. The implementation uses the current Gemini Interactions API and its dedicated `system_instruction` field for the versioned research policy.

**Trace and safety result:** Each research run records sanitized externally observable provider/search/citation events, validation and repair outcomes, model configuration, usage, and an estimated cost only when measured token components permit it. API keys and hidden reasoning are excluded. Failed calls and malformed model output produce a reviewable failed trace rather than an `EnthusiastRecord`.

**Verification result:** Offline contract tests cover valid, malformed, unknown, conflicted, provenance, retry, configuration, missing-key, trace-sanitization, and no-answer-key-import behavior. One controlled non-benchmark live request was dispatched after `GEMINI_API_KEY` was configured, but the SDK invocation remained nonresponsive beyond the configured 45-second request timeout and produced no result or trace before its exact smoke-test process was terminated. No model result was accepted and no retry was performed.

**Status:** Blocked pending an explicitly authorized replacement live validation after timeout behavior is resolved.


### 48. Replaced blocking Gemini execution after live timeout failure
**Experiment:** The first real non-benchmark Gemini smoke test used a synchronous/blocking execution path with an intended 45-second timeout. The request remained nonresponsive past that boundary, produced no usable final result or trajectory, and the exact smoke-test processes were terminated. No retry was made.

**Learning:** A network/request timeout is not a reliable lifecycle boundary for agentic web research. The blocking execution approach was rejected.

**Replacement:** Gemini background execution now creates an interaction, captures its ID immediately, polls with bounded retrieval requests, and applies an application-level wall-clock deadline with an official cancellation attempt. This is preserved as a genuine failed/removed implementation experiment for the hackathon Improvement Changelog.

**Status:** Removed / Replaced.


### 49. Isolated and corrected the background-client lifecycle failure
**Official-contract correction:** Reconciled the adapter with the May 2026 Gemini Interactions API contract. Structured output now uses one `response_format` object containing `type`, `mime_type`, and `schema`; plain-text diagnostic requests omit `response_format`. Background creation, retrieval, cancellation, Google Search, medium thinking, and the `steps` response structure match the current official syntax. Thinking tokens are included in cost estimates at the output-token rate when provider usage is available.

**Diagnostic result:** The authorized three-probe ladder stopped after Probe A. The plain-text background creation failed before an interaction ID was issued because the lazily created SDK client was not retained and its interaction service observed a closed client. Search and structured output were therefore not exercised, and no retry or additional live interaction was performed.

**Correction:** Retain the lazily created `google-genai` client for the lifetime of the adapter. Provider failures now preserve sanitized stage, exception class, HTTP/provider fields when available, response body, elapsed time, and whether an interaction ID was issued. Offline coverage includes the lifecycle regression and diagnostic redaction paths.

**Status:** Kept; live validation remains blocked until a separately authorized fresh ladder run.


### 50. Replaced Gemini background retrieval with a process-isolated synchronous boundary
**Background finding:** The retained SDK client was verified live: background creation returned a real interaction ID with status `in_progress`. Polling then failed with HTTP 400. Inspection of `google-genai` 2.20.0 confirmed that public `interactions.get()` forces `stream=false`; however, a direct documented REST retrieval without that parameter and with the required API revision returned the same HTTP 400. The SDK query issue exists but cannot be assigned sole causality for this integration failure.

**Decision:** Remove background execution from the V1 research path. Gemini Interactions remain the API boundary, but V1 now performs one synchronous interaction in an isolated worker process. The parent process owns the hard wall-clock deadline and terminates/kills the worker if necessary, so an SDK or network call cannot indefinitely retain application control. No automatic retry occurs.

**Diagnostic update:** A minimal non-benchmark synchronous control request (78 serialized provider-request bytes, no tools, schema, system instruction, or thinking configuration) was given a 30-second worker SDK timeout and 40-second parent deadline. The SDK timeout did not fire; the parent terminated the worker at approximately 40.018 seconds, with no interaction ID or result. This environment therefore has no demonstrated synchronous completion within 40 seconds for even the minimal control.

**Generate Content update:** After the transport pivot, the first minimal Generate Content control used the isolated worker with a 20-second parent deadline and failed after approximately 2.8 seconds with provider HTTP 503 `UNAVAILABLE` (“currently experiencing high demand”). One explicitly authorized controlled retry used the unchanged model/request after a bounded 5-second delay and returned the same HTTP 503 `UNAVAILABLE` after 747 ms; no retry metadata, result, or usage was present, and the worker was not terminated. Search and structured probes were not attempted. This records the repeated observed capacity response without generalizing it to Gemini overall.

**Model comparison update:** One authorized `gemini-3.6-flash` Generate Content comparison used the same isolated-worker request shape but stopped in local worker validation because `GeminiSettings` currently allows only `gemini-3.7-flash`. The provider was not reached, so no provider latency, output, usage, or cost was available; the outer diagnostic completed in under one second. No additional model call was made.

**Model-selection correction and result:** The settings model allowlist now explicitly accepts `gemini-3.7-flash` and `gemini-3.6-flash` while retaining 3.7 as the default; arbitrary model IDs remain rejected. The single live 3.6 comparison then completed successfully through Generate Content in the isolated worker (provider latency 3,798 ms; parent worker latency 4,282 ms; 448 total tokens; estimated cost $0.001635). The model returned a non-benchmark response asking for vehicle context rather than identifying the supplied vehicle, so this verifies transport/model availability only. `gemini-3.6-flash` is the provisional V1 research-model candidate pending Search and structured-output validation; those probes were not run.

**Search and structured validation:** Probe B then succeeded on `gemini-3.6-flash` with Generate Content plus Google Search (one query, one grounding source, two support/citation events, provider latency 17,248 ms, parent worker latency 17,719 ms, 862 total tokens, estimated cost $0.0023565). The returned 34 MPG combined claim matched the exposed grounding-support segment. Probe C used the real structured research-agent path but stopped at provider validation with HTTP 400 `INVALID_ARGUMENT` after 253 ms: the generated response schema included unsupported `additional_properties` fields. No retry or schema repair was attempted; Step 7 remains incomplete pending an offline schema-compatibility correction and a separately authorized future C run.

**Schema compatibility correction and replacement C:** Offline inspection of `google-genai` 2.20.0 showed Pydantic's canonical `additionalProperties` was rewritten to `additional_properties` by the legacy `response_schema` transformer. The adapter now sends the canonical JSON Schema through `response_json_schema`, preserving raw JSON Schema keywords while retaining local Pydantic validation. Regression coverage confirms the raw wire shape and Search-tool coexistence. The single replacement C completed on `gemini-3.6-flash` (provider latency 16,147 ms; parent worker latency 16,609 ms; 3,157 total tokens; estimated cost $0.00910575) and locally validated four researched facts with canonical provenance. However, the provider exposed no Search query, grounding source, or citation events for C (`search_call_count=0`, `citation_count=0`); the returned provenance URLs are model output, not independently provider-grounded evidence. Step 7 therefore remains pending acceptance of the Search-evidence gap; no model-default switch or completion commit was made.

**Evidence-first architecture and final validation:** Probe C established that Search availability does not guarantee Search invocation, and model-written URLs are not grounding evidence. V1 therefore uses one two-phase research agent: Phase A acquires a grounded `EvidenceBundle` from Generate Content plus Google Search, and Phase B performs raw-JSON-Schema structured synthesis with Search disabled using only deterministic source IDs. Offline coverage verifies grounding admission, source-ID resolution, ungrounded failure, canonical validation, no retries, and secret-safe unified traces. The authorized final non-benchmark run used the 2024 Toyota GR Corolla Circuit Edition and completed successfully with two isolated Generate Content calls: Phase A latency 8,813 ms, 2 Search queries, 5 grounded sources, 941 tokens, estimated cost $0.00261075; Phase B latency 5,203 ms, structured validation passed, 3,016 tokens, estimated cost $0.004845. Totals were 2 model calls, 2 Search queries, 3,957 tokens, 14,016 ms, and estimated cost $0.00745575. Four known facts resolved only through Phase-A source IDs S1-S5. Following the two observed 3.7 high-demand responses, the live 3.6 evidence supports selecting `gemini-3.6-flash` as the reproducible V1 default while retaining both IDs in the validated allowlist.

**Correction:** Resource accounting now counts attempted provider calls, including provider, SDK-timeout, parent-deadline, and malformed-result failures; unavailable usage remains unknown. Active documentation and configuration now describe the Generate Content two-phase path, fixed 45-second/30-second parent deadlines, and no polling knob. Historical Interactions experiments and traces remain unchanged.

**Status:** Kept; evidence-first two-phase research validation completed.


### 51. Implemented the reproducible Full-Web benchmark baseline
**Decision:** Added a dry-run-safe Full-Web runner that loads only the frozen answer-key-free runtime input corpus, supplies a fixed objective catalog, invokes the existing evidence-first Gemini 3.6 Flash agent, and persists per-fixture canonical results plus trajectories and resource metrics. The baseline deliberately uses no vPIC, structured seeds, knowledge-store facts, Hybrid gap detection, prior outputs, or ground truth. Paid execution requires an explicit fixture or `--all`; every superseded formal result is retained unchanged; and the default $2.00 cost guard includes matching current results across resumed execution, stopping further paid work when prior cost is unknown. Gemini's Generate Content Search query count is not application-enforceable, so the configured value is treated as a declared planning budget while formal artifacts record actual observed queries.

**Pre-execution structural correction:** The initial 69-field catalog (SHA-256 `875879e7ef3e12b63ea5a75dd0d5ef6a344bd2fd3bd5d7362a3a2497d07c7ed9`) was implemented before the structural field-ID audit. With zero formal results, the metadata-only audit found that it intersected only 15 of 92 frozen scorable canonical IDs because category namespaces and field names had drifted. The catalog was reconciled to all 92 canonical scoring IDs before evaluation: 91 are agent-researched and `engine_and_measured_performance.power_to_weight_hp_per_us_ton` is deterministically derived from canonical horsepower and curb weight. The corrected catalog SHA-256 is `439d5fc674c25f040da52efb8a391d6a28366a4b1822b3bd96c057e933501b43`. No expected values were used, and frozen ground truth and benchmark inputs remained unchanged.

**Full-Web V1 first formal execution:** Ran only `01_miata_gt_auto_ground_truth.json` on Gemini 3.6 Flash under system identity `full-web-baseline-v1`. Phase A completed with 8 observed Google Search queries and 28 provider-grounded sources. Phase B exceeded the original 30-second hard parent deadline after 2 attempted model calls and 42.906 seconds total elapsed time. Token usage and estimated cost were not exposed by the provider. The 91-field task did not complete structurally (one fallback `Unknown` fact was persisted); no grading or score was run. The result and trajectory remain failed historical engineering/evaluation evidence. Frozen ground truth, the 24/24 benchmark lock, and the 12/12 runtime-input corpus remained unchanged.

**Full-Web V2 pre-benchmark engineering correction:** Offline replay of the preserved V1 Phase B request found a 57,434-byte worker payload for the 91-field synthesis, including redundant provider support mappings whose segment text was already supplied as source-grounded text. The complete EvidenceBundle remains preserved in the trajectory, but the corrected runtime sends Phase B a deterministic source-ID-preserving projection without those duplicate support mappings. The original 30-second Phase B ceiling had been validated only on a 4-fact development workload; the corrected runtime globally uses 60 seconds for Phase B while keeping Phase A at 45 seconds. Because deadline and transport behavior materially changed, the corrected runtime is identified as `full-web-baseline-v2`. The task definition, model, Search policy, schema, scoring, source-ID provenance system, ground truth, and benchmark inputs remain unchanged. No V2 live benchmark execution had occurred at this correction.

**Removed pre-use control approach:** An explicit unknown-prior-cost retry override was implemented while V1 and the corrected runtime still shared one identity, then removed before any use. Versioning the materially changed runtime is the cleaner reproducibility boundary: V1's unknown cost remains unknown historical project spend, while the then-planned V2 `$2.00` ledger would count only matching current and archived V2 attempts, count byte-identical artifacts once, and remain fail-closed if any matching V2 cost was unknown.

**Full-Web V2 first formal execution:** Ran only `01_miata_gt_auto_ground_truth.json` on Gemini 3.6 Flash under the fixed 45-second Phase A / 60-second Phase B runtime policy. Phase A reached its 45-second hard parent deadline during the first model call, before a completed Google Search response or Phase B. The formal artifact records one model call, zero observed Search queries, zero grounded sources, and `phase_a_deadline_exceeded`; persisted Phase A, Phase B, and aggregate latency fields, token usage, and provider cost are unavailable, while the trajectory timestamps span approximately 45.008 seconds. The 91 requested researched fields were not returned, so the only persisted fact is the deterministic power-to-weight field as `Unknown`; no correctness grading was performed. Persistence archived the V1 result byte-for-byte and left its original trajectory unchanged.

**Full-Web V3 pre-benchmark engineering correction:** V2 showed that one Google-Search-grounded Phase A call for all 91 research targets is not a reliable workload unit. V3 retains one ResearchAgent, Gemini 3.6 Flash, medium thinking, the 92-field task/scoring contract, Search policy, source-ID provenance, catalog hash, ground truth, benchmark inputs, and the 45-second Phase A / 60-second Phase B deadlines. It deterministically batches Phase A in original requested-field order into at most 24 fields per call (24/24/24/19 for the Full-Web workload), merges successful grounded evidence with globally stable source IDs and URL-level deterministic deduplication, and performs one unchanged Phase B synthesis only after all batches succeed. A failing or ungrounded batch stops without later batches, synthesis, or retry. This materially changes runtime behavior, so the active identity is `full-web-baseline-v3`; no V3 provider execution has occurred.

**Full-Web V3 first formal execution:** Ran only `01_miata_gt_auto_ground_truth.json` on Gemini 3.6 Flash with Phase A batches of 24/24/24/19 fields. All four Search-grounded batches completed in 111,219 ms aggregate worker latency with 28 observed Search queries and 69 grounded sources; their measured Phase A usage was 8,745 input tokens, 4,527 output tokens, 11,024 thinking tokens, 24,296 total tokens, and estimated cost $0.064875. The fifth call, unchanged Phase B structured synthesis, exceeded its 60-second hard parent deadline (worker diagnostic 60,016 ms) and returned no usage. The formal result therefore failed with `phase_b_deadline_exceeded` after five model calls; aggregate token/cost fields remain unknown, no researched facts were structurally returned, and the deterministic power-to-weight fact remained `Unknown`. No grading or retry was performed. Persistence archived the V2 result byte-for-byte and left V1/V2 trajectories unchanged.

**Full-Web V4 offline correction:** V3 demonstrated that Phase A batching contained evidence-acquisition workload but left one 91-field Phase B synthesis call beyond the unchanged 60-second deadline. V4 keeps the same model, thinking, Search policy, catalog/hash, schemas, provenance semantics, benchmark inputs, ground truth, and Phase A/Phase B deadlines. It deterministically partitions Phase B in the same original field order (24/24/24/19), supplies each Search-disabled synthesis call only its matching Phase A EvidenceBundle, independently validates each response, and deterministically merges canonical facts only after all four batches succeed. One ResearchAgent now has eight maximum calls, with no retry or V4 provider execution yet.

**Full-Web V4 first formal execution:** Ran only `01_miata_gt_auto_ground_truth.json` on Gemini 3.6 Flash. The first 24-field Phase A batch stopped with sanitized `Gemini worker provider_error` before a completed provider response, so the run failed with `phase_a_batch_1_provider_error` after one attempted model call. No later Phase A or Phase B batch ran; observed Search queries and grounded sources were both zero; latency, token usage, and cost were unavailable; and no researched facts were structurally returned. The persisted result contains only the deterministic power-to-weight fact as `Unknown`. No retry, grading, timeout/model/prompt change, or other fixture execution occurred. V1, V2, and V3 artifacts were preserved byte-for-byte; V3 became an archive before V4 replaced the current result.

**Status:** V1, V2, V3, and V4 formal Miata failures preserved; no rerun performed.


### 52. Simplified Full-Web benchmark cost controls
**Decision:** Keep provider usage and known cost as observable benchmark evidence, but remove the `$2.00` hard execution ceiling and the unknown-cost retry blocker. Google billing showed approximately `$0.12` of total project spend at this point, making the earlier conservative control more operationally complex than useful.

**Controls retained:** Live execution still requires `--live`; failed cases still require explicit `--retry-failed`; there are no automatic retries; every attempt is persisted and any superseded result is archived. Matching historical results continue to provide accumulated known cost and explicit unknown-cost counts without treating unknown as zero.

**Diagnostic correction:** Missing `GEMINI_API_KEY` failures now return a sanitized configuration diagnostic with request stage, exception class, non-secret message, elapsed time, and `interaction_id_issued=false`. This does not change Full-Web V4 model behavior, batching, prompts, deadlines, catalog, evidence semantics, or scoring.

**Status:** Kept.


### 53. Narrowed the hackathon evaluation to an evidence-backed Core 24 profile
**Decision:** Preserve the original V1 92-field catalog and all of its benchmark, artifact, and engineering history as the product-scale expansion path. Create the separate versioned task definition `hackathon-core-24-v1` for the weekend hackathon rather than rewriting the historical benchmark.

**Evidence:** The product-scale task has 91 agent-researched facts plus one deterministic derived fact. Its V4 execution shape is four Phase A grounded-research batches and four Phase B reconciliation batches, for up to eight model calls per vehicle. The prior formal Miata attempts demonstrated the associated deadline, latency, token, cost, grading, and demo-surface burden. The Core 24 has 23 researched facts plus deterministic pounds-per-horsepower, which fits one Phase A batch and one Phase B batch.

**Product scope:** Core 24 preserves the enthusiast-shopping value proposition—audio, brakes/tires, driver assistance, drivetrain/differential, power/performance, energy storage, transmission, and suspension—while defining combined rotor, tire, energy-storage, and suspension objects explicitly. Exact-VIN vPIC remains a conservative structured source for semantically compatible facts only; ambiguous provider values remain Web-research targets.

**Interface direction:** The standalone demo is the reproducible hackathon interface. A Chrome Manifest V3 marketplace overlay remains the future commercial interface, not a prerequisite for judge reproduction.

**Freeze boundary:** No paid Core 24 Full-Web or Hybrid benchmark execution is valid until the new independent ground-truth corpus, comparison rules, provenance audit, leakage scan, and benchmark lock are completed. The historical V1 ground truth and its lock remain untouched.

**Status:** Kept as an evidence-driven scope reduction; Core 24 answer-key curation is pending.


### 54. Expanded Hybrid Core 24 from seeds-only to structured research context
**Decision:** Exact-VIN vPIC data now contributes at two levels: canonical seeds when provider semantics fully support a Core 24 field, and provenance-bearing research context when a trustworthy sub-fact narrows the Web question without completing it.

**Example:** `TransmissionStyle=Automatic` plus `TransmissionSpeeds=8` is passed to the ResearchAgent as trusted vPIC context. The Web phase still resolves the mechanism (torque-converter automatic, DCT, CVT/IVT, or another supported taxonomy) and cannot silently promote generic `Automatic` to a mechanism-specific answer.

**Safety:** Blank, Optional, Not Available, malformed, broad, or ambiguous provider values remain non-assertive. Turbo only seeds aspiration for explicit positive semantics; lane centering uses only the actual `LaneCenteringAssistance` variable; battery energy preserves range/context rather than inventing one exact capacity; and compound final facts retain their normal reconciliation/provenance boundary.

**Audit result:** The authorized vPIC-only audit covered all 12 answer-key-free VIN inputs with no Gemini calls. Actual Core 24 contribution ranged from 1 to 6 fields (average 3.75), with an average of 3.0 complete canonical seeds and 0.75 additional partial contributions. Manufacturer/provider variation is material, so the potential 11-field list is not a guaranteed per-VIN seed count. The raw machine-readable report is `artifacts/audits/hybrid_core_24_vpic_audit.json`.

**Status:** Kept as a pre-benchmark mapping/context revision; no paid Core 24 Gemini execution or grading occurred.


### 56. Clarified Core 24 vPIC contribution reporting
**Correction:** The Hybrid dry-run contract now reports an 11-field upper-bound
vPIC contribution surface (complete seeds, deterministic composition, and
trusted context constraints), rather than an outdated five-seed count. The
per-VIN audit remains the source of actual contribution counts; no runtime
provider behavior, benchmark artifact, or ground-truth data changed.

**Verification:** 179 offline tests, the canonical verifier, and the historical
V1 ground-truth audit pass. The committed frozen benchmark lock verifies 24/24,
and the answer-key-free vPIC audit remains 12/12 decoded with no Gemini calls.

**Status:** Kept; Core 24 ground-truth curation and paid comparison remain pending.


### 57. Independently curated and froze the Hackathon Core 24 measuring stick
**Decision:** Create `hackathon-core-24-ground-truth-v1` as a separate 12-fixture, 11-family answer-key corpus before either Full-Web or Hybrid receives a paid Core 24 execution. The historical 92-field V1 ground truth, inputs, lock, artifacts, grader evidence, and failed experiments remain unchanged.

**Evidence contract:** Every fixture represents all 24 Core fields exactly once. The freeze contains 194 applicable scorable known facts, all 194 with non-vPIC provenance; 86 applicable fields are explicitly unresolved and non-scorable because exact-configuration evidence was insufficient; 8 fields are not applicable under frozen EV/CVT/manual semantics. Exact-trim instrumented Car and Driver results were unavailable across the frozen set, so 0–60, skidpad, and 70–0 facts remain unresolved rather than borrowing nearby trims, transmissions, packages, tires, or model years.

**Scoring contract:** Added `deterministic-core-24-grader-v1`, machine-readable numeric tolerances/aliases, compound-field all-components matching, Known/Unknown/N/A separation, deterministic pounds-per-horsepower, provenance scoring, `C + E + U = N`, and paired-MINI family aggregation before the 11-family headline macro.

**Evaluation safeguard:** The Core 24 catalog, ground truth, comparison rules, schema, manifest, lock, provenance audit, and grader have distinct version/hash identities. Runtime/provider modules cannot import the answer-key path, runtime inputs remain answer-key-free, and vPIC is never answer-key provenance. This freeze order prevents changing answers or tolerances in response to later Full-Web/Hybrid results.

**Status:** Kept; no paid Core 24 Gemini call occurred. The next step is one matched Full-Web and Hybrid execution against the frozen lock.


### 58. Documented Core 24 product coverage versus scoreable coverage before execution
**Clarification:** Core 24 defines a 24-field user-facing product surface, while `hackathon-core-24-ground-truth-v1` scores only facts for which defensible exact-configuration ground truth was independently established. Its 288 canonical slots contain 194 known scorable facts, 86 unresolved applicable facts, and 8 not-applicable facts. The 86 unresolved applicable facts are approximately 29.9% of all canonical slots.

**Instrumented coverage:** Exact-configuration frozen coverage is zero known scorable facts for 0–60 mph, skidpad, and 70–0 mph braking. Available instrumented tests differed in trim, transmission, tires, packages, model year, or another performance-affecting configuration detail. We preferred an unresolved benchmark fact over a falsely precise answer derived from a mismatched test vehicle.

**Product interpretation:** These fields may still appear in the user-facing product or demo when live evidence supports them even when they are not included in a fixture's formal factual-accuracy score. This distinction was documented before the first evaluated Core 24 provider run; the frozen answer key was not changed to increase coverage.

**First matched execution:** The first Core 24 Miata pair used the frozen catalog, Gemini 3.6 Flash, and unchanged one-batch-per-phase behavior. Full-Web requested 23 researched fields and stopped after its first attempted model call with `phase_a_batch_1_deadline_exceeded`. Hybrid successfully decoded the exact VIN through vPIC, seeded displacement (2.0 L), horsepower (181 hp), gear count (6), and curb weight (2,513 lb), reduced the Web target set to 19 fields, and then stopped after its first attempted model call with the same `phase_a_batch_1_deadline_exceeded`. Neither system reached Phase B or returned researched facts; Search/source/token/cost measurements were unavailable, and neither incomplete result was graded. No retry occurred and no system behavior changed between the matched runs.

**Pre-retry execution-envelope correction:** The first matched Core 24 execution revealed that the inherited 45-second Phase A parent deadline was shorter than Gemini's observed grounded-search response time for both Full-Web and Hybrid. Full-Web had 23 research targets; Hybrid had 19 after four vPIC seeds. Both terminated at the Phase A deadline, neither reached Phase B, and neither produced a gradeable accuracy result. Because this was an execution-envelope failure rather than a scoring or model-quality result, the shared Phase A parent deadline was increased equally from 45 seconds to 90 seconds for both systems before one documented explicit retry. Phase B remains 60 seconds. The failed 45-second results and trajectories are preserved. No benchmark, grader, mapping, prompt, model, batching, retry-policy, or runtime-input change was made, and there are no automatic retries.

**One explicit matched retry:** Full-Web completed Phase A in 89,235 ms with 11 observed Search queries and 26 grounded sources, then reached the unchanged 60-second Phase B deadline. Its two-call result remained failed and ungradeable; token usage and measured cost were unavailable. Hybrid again seeded four vPIC facts and researched the remaining 19 fields. It completed both phases, returned all 24 canonical facts, and recorded two model calls, 14 Search queries, 24 grounded sources, 19,538 total tokens, 101,437 ms aggregate model latency, and $0.0349425 measured cost. The frozen grader scored Hybrid at N=19, C=11, E=8, U=0, CEFC=0.5789473684, attempted accuracy=0.5789473684, error rate=0.4210526316, Unknown rate=0, and provenance success=11/11. Because Full-Web did not produce a gradeable result, this retry demonstrates a completion/reliability difference for this sample but does not establish a matched accuracy improvement. Exactly one explicit retry per system was performed; neither system was rerun again.

**Status:** Kept; measuring-stick coverage was made explicit before execution, and both first formal Miata attempts remain preserved as matched reliability evidence rather than accuracy evidence.


### 59. Extended the shared Phase B execution envelope before the final benchmark retry
**Decision:** The first controlled retry showed that the 90-second Phase A envelope was sufficient for both acquisition paths: Full-Web completed grounded research in 89.235 seconds, while Hybrid completed it in 52.344 seconds after vPIC resolved four facts first. Full-Web then exceeded the unchanged 60-second Phase B synthesis deadline, while Hybrid completed synthesis in 49.093 seconds. Because Full-Web had successfully completed evidence acquisition and failed only against the inherited synthesis execution envelope, the Phase B parent deadline was increased equally from 60 to 90 seconds for both modes before one final Full-Web retry. Hybrid was not rerun because its existing Phase B response completed within 49.093 seconds and is therefore already valid under the new 90-second maximum.

**Boundary:** This is an execution-envelope correction, not a prompt, model, Search, benchmark, mapping, batching, or scoring correction. Phase A remains 90 seconds. No benchmark, grader, comparison-rule, tolerance, catalog, runtime-input, vPIC-mapping, research-target, or retry-policy value changed. There are no automatic retries, Hybrid will not be rerun, and this is the final benchmark retry before integration and submission work.

**Final Full-Web retry:** The one authorized final retry completed under the shared 90/90 envelope. Full-Web returned all 24 canonical facts after two model calls: Phase A completed in 36,000 ms, Phase B in 50,032 ms, and aggregate model latency was 86,032 ms. It recorded 10 Search queries, 19 grounded sources, 17,802 total tokens, and $0.0393045 measured cost. The frozen grader scored N=19, C=15, E=4, U=0, CEFC=0.7894736842, attempted accuracy=0.7894736842, error rate=0.2105263158, Unknown rate=0, and provenance success=14/14.

**Matched result:** The preserved Hybrid result scored C=11, E=8, U=0, and CEFC=0.5789473684 with 19,538 tokens, 101,437 ms latency, and $0.0349425 measured cost. On this one matched fixture, Full-Web CEFC was 0.2105263158 higher, its error rate was 0.2105263158 lower, it used 1,736 fewer tokens, 4 fewer Search queries, 5 fewer grounded sources, and 15,405 ms less aggregate model latency; Hybrid cost $0.004362 less. Both used two model calls and both had 100% provenance success for their correct known facts. This sample does not support an accuracy, latency, query, source, or token advantage for Hybrid. It does show that the frozen comparison is runnable and that vPIC contributed four exact-VIN seeds, but the observed structured head start did not translate into a better final score on Miata.

**Status:** Kept as the final Core 24 Miata benchmark result. No Hybrid rerun or additional provider retry occurred; benchmarking stops here before integration and submission work.
