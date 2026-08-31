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
- A Core 24 ground-truth corpus must be independently curated, audited, and
  locked before any paid Core 24 Full-Web or Hybrid benchmark execution.

No runtime system reads ground-truth answer keys.
