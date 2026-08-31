# Enthusiast Lens

## Hackathon problem

Vehicle-marketplace listings expose generic specifications but often obscure the
exact configuration details that matter to enthusiasts: drivetrain, transmission,
brakes, tires, measured performance, driver assistance, and equipment.

## Hackathon solution

Enthusiast Lens produces an evidence-backed **Hackathon Core 24** vehicle
profile. It compares two acquisition paths against the same versioned task and
ground-truth contract:

```text
Full-Web: vehicle -> grounded web research -> evidence reconciliation -> Core 24 profile
Hybrid: VIN -> safe vPIC facts/context -> grounded web research for remaining facts -> same Core 24 profile
```

The experiment asks whether exact-VIN structured data reduces web-research work
while preserving factual quality, Unknown handling, and reviewable provenance.

Hybrid treats exact-VIN vPIC output at two levels: semantically complete values
may seed canonical facts, while trustworthy partial values are retained as
research context. The context can narrow the Web question without turning
generic or optional provider values into unsupported claims.

The Core 24 task fits one evidence-acquisition batch and one evidence
reconciliation batch. The historical 92-field catalog remains preserved as the
product-scale expansion, not as a discarded experiment.

## Interface and product direction

The hackathon interface is a standalone, reproducible demo. This avoids browser
extension installation and marketplace-DOM variability for judges while exposing
the same canonical pipeline and Full-Web/Hybrid comparison.

The intended longer-term product interface is a Chrome Manifest V3 extension:

```text
Supported marketplace listing -> identify exact vehicle/VIN -> retrieve or generate profile -> listing-page overlay
```

That future overlay is intentionally separate from the hackathon demo and is
not required to reproduce the evaluation.

## Judge result

The Core 24 benchmark was frozen before provider execution: 12 fixtures across
11 vehicle families, 288 canonical slots, 194 scorable known facts, 86
unresolved facts, and 8 not-applicable facts. Runtime systems never read frozen
ground-truth answers. Failed runs and trajectories remain preserved.

| Vehicle | Full-Web CEFC | Hybrid CEFC |
|---|---:|---:|
| Mazda MX-5 Miata | 78.95% | 57.89% |
| Toyota GR86 | 68.42% | failed at fixed 90-second Phase A deadline |
| Kia Soul Turbo | 73.68% | 78.95% |
| Subaru WRX | 64.71% | 82.35% |

Full-Web completed 4/4 with 71.44% four-family macro CEFC. Hybrid completed
3/4 with 73.07% macro CEFC across completed runs. Across the three matched
completed pairs, Full-Web measured 72.45% macro CEFC, $0.10734075, 80,631 ms,
29 searches, and 51,365 tokens; Hybrid measured 73.07%, $0.09655125, 67,693
ms, 33 searches, and 53,751 tokens. Hybrid supplied 18 complete vPIC seeds
across four attempted vehicles (4.5 per attempted vehicle).

The representative subset produced a mixed result. Hybrid did not show a universal advantage: it failed GR86 under the fixed envelope and used more searches/tokens across matched completions. Among the three completed pairs, Hybrid slightly improved macro CEFC and reduced cost/latency. Exact-VIN structured grounding may help on some configurations; benefit is vehicle-dependent, not uniformly superior.

This is recorded evidence, not a claim of statistical significance or a full
12-fixture benchmark result.

## Live product proof

The live standalone judge UI is separate from frozen evaluation artifacts. A
final live Hybrid Miata product run resolved 24/24 product fields, with 0
Unknown, 26 grounded references, 2 model calls, 45.8 seconds, and estimated
cost $0.037. This is product-run field resolution, not benchmark accuracy;
benchmark scores are reported separately above.

The historical 92-field version remains product-scale evidence: its V4 Miata
run used 8 model calls, 61,971 tokens, and approximately $0.1362. A normal
successful Core 24 run uses 2 model calls.

## Clean-clone reproduction

Requirements are Python `>=3.12,<3.13` (from `pyproject.toml`) and Node/npm
(the app package does not pin a Node version). From a clean clone:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
$env:GEMINI_API_KEY = "<set locally; never commit or print>"
.\.venv\Scripts\python.exe -m uvicorn enthusiast_lens.api:app --host 127.0.0.1 --port 8000
cd app
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

Open [http://127.0.0.1:5174/](http://127.0.0.1:5174/). Choose a vehicle and
Full-Web or Hybrid, then select **Review vehicle**. Product-run artifacts are
written under `artifacts/product_runs/`; the browser never receives the API
key. Provider cost and latency depend on live availability; the recorded runs
above are the only cost/runtime estimates claimed here.

Exact baseline/evaluation commands and safety boundaries are documented in
[`docs/FULL_WEB_BASELINE.md`](docs/FULL_WEB_BASELINE.md),
[`docs/HYBRID_VPIC_WEB.md`](docs/HYBRID_VPIC_WEB.md), and
[`docs/HACKATHON_CORE_24_EVALUATION_SPEC.md`](docs/HACKATHON_CORE_24_EVALUATION_SPEC.md).

## Evidence and project record

- [`CHANGELOG.md`](CHANGELOG.md): chronological decisions and execution results
- [`AGENTS.md`](AGENTS.md): repository operating and evaluation rules
- [`evals/ground_truth_core24_v1/`](evals/ground_truth_core24_v1/): frozen Core 24 benchmark
- [`artifacts/evals/core24_scores/`](artifacts/evals/core24_scores/): recorded scores
- [`artifacts/evals/full_web_core_24/`](artifacts/evals/full_web_core_24/): Full-Web results and trajectories
- [`artifacts/evals/hybrid_core_24/`](artifacts/evals/hybrid_core_24/): Hybrid results and trajectories
- [`artifacts/product_runs/`](artifacts/product_runs/): live judge product runs

Provider availability, deadlines, and configuration-specific evidence quality
are part of agent correctness. A structured source is useful only when it
actually reduces uncertainty; adding a source does not automatically improve
the final answer.
