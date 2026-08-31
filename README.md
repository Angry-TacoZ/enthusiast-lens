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

## Reproducibility boundary

- `evals/ground_truth/` is the immutable historical V1 benchmark.
- `evals/task_definition/v1_objective_field_catalog.json` is the preserved
  92-field product-scale catalog.
- `evals/task_definition/hackathon_core_24_v1_field_catalog.json` is the new,
  answer-key-independent Core 24 task definition.
- `evals/ground_truth_core24_v1/` is the independently curated and frozen Core
  24 measuring stick: 12 fixtures, 11 families, its own schema, comparison
  rules, manifest, lock, audit, and grader identity.

The Core 24 freeze contains 288 canonical field slots. It currently has 194
applicable scorable facts with provenance, 86 applicable facts frozen as
unresolved because exact evidence was insufficient, and 8 not-applicable
facts. Neither evaluated system has seen a paid Core 24 benchmark execution.
The next checkpoint is a matched Full-Web versus Hybrid run against this exact
lock; answers and tolerances may not be tuned afterward.

No runtime system reads ground-truth answer keys.

## Standalone judge UI

The judge UI is a local Vite app backed by a localhost-only Core 24 API. From
the repository root, install the Python package and start both processes:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn enthusiast_lens.api:app --host 127.0.0.1 --port 8000
cd app
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

Open `http://127.0.0.1:5174/`, choose any of the 11 Core 24 vehicle families,
select Full-Web or Hybrid, and click **Review vehicle**. The API maps the UI
selection to the answer-key-free runtime input and invokes the existing runner;
the report then displays the returned 24-field canonical result and provenance.
Live runs require `GEMINI_API_KEY` in the local server environment. The key is
never sent to the browser. Product-run artifacts are written under
`artifacts/product_runs/`, separate from evaluation artifacts.
