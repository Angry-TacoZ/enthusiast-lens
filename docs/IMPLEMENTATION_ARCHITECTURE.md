# Enthusiast Lens V1 Implementation Architecture

## Purpose and status

This document freezes the V1 implementation boundaries, technology stack, persistence model, and data flow before application code is written. It preserves the Full-Web versus Hybrid experiment, frozen benchmark, and reproducible hackathon judging path.

The frozen benchmark under `evals/ground_truth/` and its manifest, lock, and scoring policy remain authoritative for evaluation. This architecture does not change schema semantics or benchmark methodology.

## 1. Product surfaces

Enthusiast Lens has two user-facing surfaces backed by the same core pipeline and canonical runtime result contract. Neither surface owns vehicle-analysis logic.

### A. Google Chrome browser extension

The Chrome extension is the primary real-world product experience.

V1 browser scope:

- Google Chrome is the official browser target.
- The extension uses Manifest V3.
- Hackathon judges load it as an unpacked extension.
- Chrome Web Store approval or publication is not required.
- CarGurus is the only officially supported V1 marketplace integration.
- Microsoft Edge may work because it is Chromium-based, but it is not an official target.
- Firefox and Safari are out of scope.

On a supported CarGurus vehicle-detail page, the extension should:

- extract the available listing context through the CarGurus adapter;
- submit that context to the shared Enthusiast Lens core pipeline;
- inject an Enthusiast Lens report panel into the listing page;
- display objective enthusiast facts and their provenance/confidence;
- display `Unknown` when evidence is insufficient;
- surface configuration-dependent warnings;
- surface conflicts, including marketplace equipment claims contradicted by stronger vehicle-specific evidence.

The extension is an input/output interface. It is not a separate intelligence architecture.

### B. Standalone demo application

The standalone application is the guaranteed hackathon reproduction path. It must remain usable without installing the extension and without depending on the current CarGurus DOM or continued availability of a live listing.

It should eventually allow a judge to:

- select included, reproducible benchmark or example vehicle contexts;
- enter a supported vehicle or listing context;
- select Full-Web or Hybrid mode where appropriate;
- view the canonical Enthusiast Lens report;
- inspect provenance and sources;
- inspect agent trajectory data;
- inspect basic runtime and resource metrics.

The standalone application and Chrome extension must invoke the same core pipeline and consume the same canonical Enthusiast Record. Vehicle-analysis logic must not be duplicated in either UI.

## 2. Frozen V1 technology stack

### Backend and core pipeline

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- httpx
- pytest

Python aligns with the benchmark and evaluation tooling, has a strong structured-data and AI ecosystem, and makes deterministic grader and runtime-pipeline work easy to share. FastAPI and Pydantic provide a typed, validated API boundary and natural canonical runtime contracts while remaining easy to reproduce locally.

### Persistence

- SQLite is the default local and hackathon runtime database.
- SQLAlchemy repositories form the data-access boundary.
- Database location and connection configuration are supplied through `DATABASE_URL`.
- The architecture remains PostgreSQL-compatible for a future production deployment.
- PostgreSQL is not required, verified, or deployed for hackathon V1.

SQLite provides a production-shaped persistence layer without requiring judges to operate external infrastructure. SQLAlchemy keeps future PostgreSQL migration practical without claiming untested portability.

### AI and model integration

- provider-neutral internal model adapter
- Gemini 3.7 Flash as the configured V1 research/reconciliation model
- paid Gemini Developer API tier for the hackathon
- medium thinking level as the initial default
- Google Search grounding where appropriate for web research
- one research/reconciliation agent for V1
- application-controlled, inspectable orchestration and trajectories
- per-run model, search, token, and resource measurement

Full-Web and Hybrid must use the same model, thinking configuration, and equivalent search capability for a fair comparison. Provider-specific calls remain behind the internal adapter so the core pipeline is not coupled directly to Gemini. V1 does not require an additional orchestration framework, and no Gemini SDK is introduced during the deterministic-utilities step.

### Frontend and browser extension

- React
- TypeScript
- Vite
- Tailwind CSS
- Chrome Manifest V3
- TypeScript/React extension UI where appropriate
- shared frontend/report components with the standalone demo where practical

React, TypeScript, and Vite fit both the extension and a polished judge interface. Shared components reduce duplicate UI logic and avoid unnecessary Next.js or server-rendering complexity. Injected CarGurus UI should use an isolation strategy such as Shadow DOM so host-page CSS cannot corrupt it.

### CI and development verification

GitHub Actions will eventually run the applicable repository verification:

- pytest;
- Python lint and type checks once configured;
- TypeScript and build checks once configured;
- the ground-truth audit;
- benchmark-lock verification.

No dependency, manifest, workflow, or implementation file is introduced by this architecture step.

## 3. API and trust boundary

```text
Chrome extension --------\
                         -> FastAPI -> shared core pipeline
Standalone React demo ---/
```

The extension and standalone demo consume validated canonical API responses. Gemini and Car2DB credentials remain server-side; browser-delivered code must not contain API keys. Detailed endpoint names remain deferred until implementation.

## 4. Conceptual data flow

```text
CarGurus listing or standalone vehicle context
        |
        v
Input adapter / vehicle context extraction
        |
        v
Canonical normalized vehicle identity/context
        |
        +-----------------------------+
        |                             |
        | Full-Web baseline           | Hybrid candidate
        |                             |
        v                             v
Research complete schema        Car2DB adapter
from web                         |
        |                        v
        |                  structured base facts
        |                        |
        |                        v
        |                  gap/quality analysis
        |                        |
        |                  targeted web research
        |                        |
        +------------+-----------+
                     |
                     v
         research/reconciliation agent
                     |
                     v
       canonical Enthusiast Lens record
                     |
                     v
       deterministic normalization /
       calculations / validation
                     |
                     +-------------------+
                     |                   |
                     v                   v
              product UI           evaluation output
```

This flow is conceptual, not a requirement for unnecessary internal stages. The single agent may plan, invoke research tools, and reconcile evidence iteratively. A simpler implementation is preferred when it preserves the same inputs, output contract, provenance, evaluation isolation, and Full-Web/Hybrid comparison.

## 5. One research/reconciliation agent

V1 uses one research/reconciliation agent with tools. Multi-agent orchestration is not part of the V1 design.

The agent owns judgment-heavy work:

- resolving the exact vehicle configuration;
- identifying missing, ambiguous, weak, stale, or configuration-sensitive facts;
- deciding what research is required;
- constructing focused research questions and queries;
- evaluating source and configuration relevance;
- reconciling conflicting evidence;
- recognizing trim, transmission, drivetrain, package, build-date, market, hardware-generation, and software-entitlement dependencies;
- returning `Unknown` when evidence is insufficient;
- producing structured provenance and confidence.

The agent does not own deterministic calculations, parsing, validation, scoring, or presentation formatting.

## 6. Deterministic application responsibilities

Normal code owns work that does not require model judgment:

- API transport and requests;
- configuration loading and environment variables;
- input allow-list validation;
- canonical schemas and models;
- JSON parsing and agent-output validation;
- exact configuration-key normalization;
- unit normalization and aliases;
- deterministic calculations, including horsepower-to-weight;
- accepted ranges and numeric tolerances;
- knowledge acceptance and persistence policy boundaries;
- database transaction boundaries;
- caching, filtering, and sorting;
- benchmark loading and benchmark-lock verification;
- evaluation scoring and MINI family aggregation;
- report generation and UI formatting;
- logging and telemetry formatting.

Client, third-party API, web-source, and agent outputs are trust boundaries. Listing data, Car2DB responses, web content, and agent output must be treated as untrusted input and validated before use. Provider secrets belong in environment configuration outside browser-delivered code.

## 7. Proposed repository and module boundaries

The following structure reflects the frozen V1 stack. It is a target, not a request to create implementation files during architecture freeze.

```text
src/
  enthusiast_lens/
    __init__.py

    api/
      routes/
      dependencies.py

    models/
      vehicle_context.py
      enthusiast_record.py
      provenance.py
      research.py
      trajectory.py

    adapters/
      cargurus.py
      car2db.py
      model.py

    pipeline/
      full_web.py
      hybrid.py
      common.py

    research/
      agent.py
      prompts.py
      tools.py
      reconciliation.py

    deterministic/
      normalization.py
      calculations.py
      validation.py
      aliases.py

    persistence/
      database.py
      models.py
      repositories.py
      knowledge_store.py
      cache.py

    observability/
      trajectories.py
      metrics.py
      logging.py

    config/
      settings.py

app/
  [React/Vite standalone demo]

extension/
  manifest.json
  [Chrome MV3 extension source]

frontend/
  [shared React/TypeScript report components if useful]

evals/
  ground_truth/          # FROZEN, READ ONLY
  results/
  trajectories/

scripts/

tests/
  unit/
  integration/
  evaluation/
```

Boundary rules:

- `models/` defines runtime contracts shared across both pipelines and product surfaces.
- `adapters/` isolates marketplace and structured-provider formats from the core.
- `api/` owns validated transport shared by the extension and standalone application.
- `research/` contains the one agent's judgment and tool-facing behavior.
- `pipeline/` composes Full-Web, Hybrid, and shared stages without duplicating core logic.
- `deterministic/` contains reproducible transformations and validation.
- `persistence/` isolates SQLAlchemy data access, reusable knowledge, and raw cache concerns.
- `observability/` records inspectable execution evidence without changing product semantics.
- `extension/`, `app/`, and optional `frontend/` shared components are presentation/input surfaces only.
- Evaluation code may read `evals/ground_truth/`; normal runtime analysis modules may not.

No implementation files or directories described above are created by this architecture step.

## 8. Canonical runtime contracts

Pydantic v2 models define canonical backend/runtime contracts. TypeScript frontend types should correspond to the externally exposed API schema. Schema or code generation may reduce drift where useful, but V1 will not introduce tooling before a demonstrated need.

The runtime contracts are distinct from the frozen ground-truth answer-key JSON Schema. The runtime output must not reuse that schema merely because it already exists, and normal runtime code must not import it.

### Vehicle Context

The normalized exact identity and configuration supplied to either pipeline. It should be capable of representing:

- year, make, model, and trim;
- transmission and drivetrain;
- known packages and options;
- market;
- listing ID and URL;
- VIN when available;
- build-date, hardware-generation, or other configuration context when available.

### Enthusiast Record

The product-facing objective result contract. It must be emitted by both Full-Web and Hybrid and consumed consistently by:

- the standalone demo;
- the browser extension;
- deterministic validation and calculations;
- the evaluator.

The contract must represent supported values, `Unknown`, applicable configuration warnings, conflicts, provenance, confidence, and derived values without importing answer-key-only scoring data.

### Provenance

Each externally researched fact must be able to retain:

- source URL;
- publisher and source type where available;
- exact-configuration match quality;
- confidence or verification state;
- structured, researched, or derived origin;
- conflict information where applicable.

Normalization must not discard provenance.

### Agent trajectory

The trajectory contract must support inspection of:

- normalized input context;
- research questions and queries;
- tool calls and web/search requests;
- tool results and sources considered;
- selected evidence;
- conflict handling;
- retries and validation failures;
- final structured output;
- latency, model use, resource use, estimated cost, and cache usage where available.

## 9. Vehicle Knowledge Store

The `Vehicle Knowledge Store` is a scoped relational runtime persistence layer. It is neither the frozen benchmark nor merely a raw-response cache. Its purpose is to preserve normalized, researched vehicle knowledge so the production-shaped system does not rediscover identical verified facts on every analysis.

The V1 store is intentionally small.

### VehicleIdentity / VehicleConfiguration

Conceptually stores an internal ID; year, make, model, trim, and body style where relevant; transmission; drivetrain; market; VIN when available; package identifiers; build date or range; hardware generation where relevant; canonical configuration key; and created/updated timestamps.

Year, make, and model alone must never be assumed to identify a unique configuration.

### VehicleFact

Conceptually stores an ID; configuration ID; canonical field ID; normalized value and type/unit; origin (`structured`, `researched`, or `derived`); confidence or verification state; first-observed and last-verified timestamps; optional stale/refresh metadata; and optional conflict state.

Every fact remains configuration-bound.

### FactSource

Conceptually stores an ID; related fact ID; URL; publisher; source type; configuration-match quality; retrieval/observation time; evidence/support relationship; and relevant notes. The store preserves provenance rather than reducing a fact to only a value.

### AnalysisRun

Conceptually stores a run ID; Full-Web or Hybrid mode; input configuration; start/completion times; status; latency; web/tool and model-call counts; token/resource and estimated-cost data when available; cache/knowledge-store hit count; Unknown count; retry/failure metadata; structured-output reference; and trajectory reference.

Exact relational columns, constraints, and indexes remain implementation decisions. V1 is not a full automotive data platform.

## 10. Four separate data domains

### A. Frozen Evaluation Ground Truth

Location: `evals/ground_truth/`

Purpose: immutable answer key used only by deterministic evaluation and grader code. It is never imported into normal runtime analysis, never used to seed the Vehicle Knowledge Store, and never exposed to the evaluated agent.

### B. Vehicle Knowledge Store

SQLite by default, behind a PostgreSQL-compatible SQLAlchemy repository boundary.

Purpose: normalized reusable facts, exact configuration identity, provenance, and research history.

### C. Raw/API Cache

Purpose: temporary or reusable raw Car2DB and other safe external responses, reduced repeated transport, and useful debugging evidence.

Raw cached responses are not equivalent to accepted normalized knowledge. The Vehicle Knowledge Store must not be described or treated as merely a cache.

### D. Evaluation Results and Trajectories

Locations may include `evals/results/` and `evals/trajectories/`.

Purpose: Full-Web/Hybrid experiment outputs, grader reports, and representative trajectories. These are experimental artifacts, not runtime vehicle knowledge.

## 11. Knowledge reuse and acceptance boundary

```text
vehicle/configuration request
        |
        v
identify exact configuration
        |
        v
query Vehicle Knowledge Store
        |
        +--> reusable current facts
        |
        +--> missing / stale / conflicting /
             configuration-sensitive facts
                          |
                          v
                structured data / research
                          |
                          v
                     reconcile
                          |
                          v
              validated new knowledge
                          |
                          v
               Vehicle Knowledge Store
                          |
                          v
                 Enthusiast Record
```

The architecture distinguishes three events:

1. A model proposes a fact with evidence.
2. The application accepts a fact into the current analysis after contract and evidence checks.
3. The application promotes an accepted fact into reusable knowledge under a persistence policy.

Acceptance into one analysis does not automatically authorize reusable persistence. V1 will not indiscriminately write back model assertions. The detailed acceptance workflow remains intentionally deferred, but this boundary is mandatory.

## 12. Contamination safeguard: the database is not an answer key

The runtime Vehicle Knowledge Store must never be populated from:

- `evals/ground_truth/*.json`;
- benchmark expected answers;
- grader results;
- hidden evaluation evidence.

Only the deterministic evaluation/grader path may read frozen ground truth. Runtime knowledge must come from the same legitimate sources available to the system being evaluated. A vehicle appearing in both the runtime domain and benchmark does not permit copying facts from the answer key.

## 13. Primary comparative evaluation isolation

Persistent runtime knowledge must not allow one system or run to advantage another in the headline Full-Web versus Hybrid comparison.

The default V1 rule is a **fresh isolated SQLite database per benchmark system run**:

```text
Full-Web evaluation -> its own clean runtime database
Hybrid evaluation   -> its own clean runtime database
```

An alternative identical allowed seed state may be supplied to both systems only when explicitly defined before the comparison. No facts discovered by Full-Web may become available to Hybrid, or vice versa.

Sequential benchmark execution must prevent earlier cases from leaking answer-relevant knowledge into later cases unless knowledge reuse is itself the separately declared experiment. The headline comparison measures architecture, not accumulated database memory.

## 14. Secondary knowledge-reuse experiment

Knowledge reuse may be demonstrated separately as a production-oriented experiment:

- first identical analysis: no prior verified knowledge, so research is required;
- second identical analysis: previously verified knowledge is available, reducing web/model calls, latency, or cost.

This is secondary evidence only. It must use declared conditions and metrics and must not change or contaminate the primary frozen Full-Web versus Hybrid methodology.

## 15. Evaluation isolation and scoring

The implementation must preserve the following logical separation during evaluation:

### Runtime input

Vehicle/listing context and provider or public-source evidence that Full-Web or Hybrid is authorized to see.

### Runtime output

The canonical Enthusiast Record, provenance, trajectory, and comparable resource metrics produced by the evaluated system.

### Frozen answer key

`evals/ground_truth/` contains the read-only benchmark, scoring policy, evidence, and grader expectations.

Normal runtime analysis must not import or read ground-truth answers, scoring values, or hidden benchmark evidence. Only evaluation and grader code may access the frozen answer key. Module imports and runtime entry points should make this boundary enforceable rather than relying only on prompt instructions.

The frozen evaluation contains 12 benchmark fixtures representing 11 vehicle families. Coverage is calculated per fixture; the paired MINI true-positive and false-positive fixture scores are averaged into one MINI family score; headline Correct Enthusiast Fact Coverage is then macro-averaged across the original 11 vehicle families. Full-Web and Hybrid must use this same aggregation policy.

## 16. Full-Web baseline

```text
normalized vehicle context
    -> research/reconciliation agent
    -> web research for the complete enthusiast schema
    -> canonical Enthusiast Record
```

The Full-Web baseline starts from equivalent normalized vehicle context and researches the objective enthusiast schema using web sources. It must not receive Car2DB facts as privileged structured grounding. It uses the same runtime output contract, deterministic validation, grader, and measurement rules as Hybrid.

## 17. Hybrid candidate

```text
normalized vehicle context
    -> Car2DB
    -> normalized structured facts
    -> gap/quality/configuration analysis
    -> targeted web research only where needed
    -> reconciliation
    -> canonical Enthusiast Record
```

Hybrid uses Car2DB as structured starting evidence, then identifies missing, weak, stale, ambiguous, or configuration-sensitive fields for targeted research and reconciliation.

The hypothesis is that structured grounding plus targeted research may improve Correct Enthusiast Fact Coverage and/or reduce research cost, latency, and unnecessary searches. This remains unproven until both systems are run on the same fixed cases and scored under the same policy.

## 18. Car2DB boundary

Car2DB is the only structured vehicle-data provider required for V1. Its adapter should eventually:

- isolate vendor-specific requests and response formats;
- preserve raw responses for debugging and reproducibility where permitted;
- normalize supported facts into runtime structures;
- retain provenance;
- tolerate missing or partial data;
- cache where appropriate;
- never treat Car2DB as ground truth;
- never silently fill unsupported fields.

No second structured vehicle database is included in V1 unless a later measured experiment justifies revisiting this decision.

## 19. UI architecture

Both product surfaces render the same canonical Enthusiast Record. The judge-facing report may organize objective results into:

- Engine & Measured Performance;
- Transmission;
- Drivetrain & Differentials;
- Suspension / Axles / Chassis;
- Brakes / Wheels / Tires;
- Audio;
- Driver Assistance / Highway Automation;
- Configuration Dependencies.

The UI should support clear states or badges such as:

- Structured data;
- Web verified;
- Derived;
- Unknown;
- Conflict / marketplace discrepancy.

Sources and configuration warnings must be inspectable so the report is not opaque AI output. Detailed visual styling is deferred.

## 20. Hackathon reproducibility path

### Fastest and lowest-risk judge path

1. Clone the repository.
2. Configure the documented environment.
3. Start the core backend and standalone demo application.
4. Select a provided reproducible example or fixture context.
5. Run an analysis.
6. Inspect the report, sources, and trajectory.

### Optional product-experience path

1. Use Google Chrome.
2. Open `chrome://extensions`.
3. Enable Developer Mode.
4. Select **Load unpacked**.
5. Select `extension/`.
6. Open a supported CarGurus vehicle-detail page.
7. Activate or use Enthusiast Lens.

The standalone path must remain functional if a live listing disappears or the CarGurus page structure changes.

## 21. Failure philosophy

The architecture must support explicit, graceful degradation:

- Car2DB unavailable: report the provider failure and use only an explicitly supported fallback path; do not pretend structured facts were retrieved.
- Research source unavailable: continue with other evidence where possible and retain `Unknown` for unresolved fields.
- Unsupported listing: return a clear unsupported-input error.
- Ambiguous exact configuration: return `Unknown` and a configuration warning rather than importing nearby-spec facts.
- Malformed agent output: reject or repair through deterministic validation; never silently trust it.
- Individual unresolved field: preserve the partial report rather than failing the whole result unnecessarily.

## 22. Observability and comparable metrics

Observability must support like-for-like Full-Web and Hybrid comparison. Record, where available:

- web searches and tool calls;
- model calls;
- latency;
- token or other resource use;
- estimated cost;
- cache hits;
- `Unknown` count;
- failures and retries.

Metrics and trajectories must be machine-readable and attributable to the pipeline mode and input case. The core product result must not depend on hackathon-only display code.

## 23. V1 non-goals

- Firefox support;
- Safari support;
- Chrome Web Store publication;
- multiple marketplace integrations;
- mobile browser extension;
- autonomous vehicle purchasing or contacting sellers;
- subjective vehicle reviews;
- reliability prediction;
- aftermarket modification recommendations;
- a second structured vehicle API;
- multi-agent orchestration;
- managed cloud database deployment;
- production PostgreSQL deployment;
- large-scale vehicle-data ingestion or bulk prepopulation;
- user accounts, saved-user garages, or billing;
- distributed cache infrastructure or a Redis requirement;
- Elasticsearch or vector database requirements;
- database-driven benchmark-answer storage;
- automatic trust of model-generated facts;
- a broad consumer marketplace platform.

## 24. Database portability and migration direction

Application code depends on repositories or services rather than SQLite-specific SQL. SQLAlchemy is the persistence abstraction, and the default `DATABASE_URL` will eventually point to SQLite. A future production deployment can use PostgreSQL without intentionally rewriting core agent/pipeline logic.

This is a **PostgreSQL-compatible architecture**, not a claim that PostgreSQL behavior has been verified. PostgreSQL deployment is out of scope for hackathon V1.

Relational schema changes should become migration-controlled when the initial persistence schema is implemented. Alembic is the preferred future tool, but it is not installed and no migrations are created during architecture freeze.

## 25. Deferred implementation choices

The accepted stack and boundaries above are frozen. These implementation details remain deliberately undecided:

- exact FastAPI endpoint names and request grouping;
- exact relational columns, constraints, indexes, and transaction policy;
- knowledge acceptance, conflict, freshness, and refresh thresholds;
- raw-cache retention and invalidation details;
- whether TypeScript API types are generated or checked through a lighter shared-schema process;
- local process startup and future hosting details;
- detailed visual design.

Any later choice must preserve the shared pipeline, canonical contracts, evaluation isolation, deterministic boundaries, and official reproduction paths defined here.

## 26. Architecture decisions

| Decision | Status |
| --- | --- |
| Python 3.12 backend | Accepted |
| FastAPI | Accepted |
| Pydantic v2 runtime contracts | Accepted |
| SQLAlchemy 2.x persistence abstraction | Accepted |
| SQLite default V1 database | Accepted |
| `DATABASE_URL` configuration boundary | Accepted |
| PostgreSQL-compatible future architecture | Accepted; not verified or deployed in V1 |
| Vehicle Knowledge Store | Accepted; scoped V1 |
| Raw/API cache separate from reusable knowledge | Accepted |
| Evaluation results separate from runtime knowledge | Accepted |
| Provider-neutral internal model adapter | Accepted |
| Gemini 3.7 Flash | Accepted as configured V1 model |
| Paid Gemini Developer API tier | Accepted for hackathon V1 |
| Medium thinking level | Accepted as initial default |
| Google Search grounding | Accepted where appropriate |
| Additional orchestration framework | Not required for V1 |
| Single research/reconciliation agent | Accepted |
| Application-controlled orchestration | Accepted |
| Full-Web baseline | Accepted |
| Hybrid candidate | Accepted; hypothesis unproven |
| Car2DB structured source | Accepted for V1 |
| React + TypeScript + Vite | Accepted |
| Tailwind CSS | Accepted |
| Chrome Manifest V3 extension | Accepted |
| Shadow DOM-style injected UI isolation | Accepted |
| Shared UI components | Accepted where practical |
| Chrome unpacked installation for judging | Accepted |
| Standalone demo as guaranteed reproduction path | Accepted |
| CarGurus-only marketplace adapter | Accepted |
| Fresh isolated database per primary comparative evaluation | Accepted |
| Knowledge-reuse demonstration | Secondary experiment only |
| Alembic migration direction | Deferred until schema implementation |
| Managed production database | Out of scope |
| Firefox and Safari support | Rejected for V1 |
| Chrome Web Store publishing | Deferred / out of scope |
| Shared core pipeline for extension and standalone | Accepted |
| Frozen benchmark isolated from runtime | Accepted |

These decisions are frozen for V1 implementation. Revisions require an explicit decision, evidence where applicable, and a meaningful changelog entry.
