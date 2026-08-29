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

---

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
