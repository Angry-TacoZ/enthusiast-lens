# Full-Web V1 benchmark baseline

Status: Implemented, not yet benchmark-executed.

The Full-Web baseline is the simple, reproducible comparison path:

```text
answer-key-free runtime vehicle input
  -> fixed objective V1 field catalog
  -> Gemini 3.6 Flash evidence-first ResearchAgent
  -> canonical FactResults + unified trajectory/resource evidence
```

The baseline receives no vPIC facts, structured seeds, knowledge-store facts,
previous outputs, Hybrid gap analysis, or ground-truth data. Runtime loading
reads only `evals/inputs/benchmark_inputs.json`; the runner never passes a
ground-truth path into execution. Public web evidence is acquired by Phase A
of `ResearchAgent`, and Phase B synthesizes only from the grounded evidence
bundle and deterministic source IDs. This is a reasonable baseline because it
researches the complete objective task directly from the web using the same
model, policy, canonical contracts, and provenance rules that Hybrid will use;
it is not intentionally weakened with fewer fields or a different output
contract.

## Fixed task definition

The machine-readable catalog is
[`evals/task_definition/v1_objective_field_catalog.json`](../evals/task_definition/v1_objective_field_catalog.json).
It was derived from sections 3.1-3.8 of the human-readable V1 Schema and
Evaluation Specification and contains objective identifiers and descriptions
only. It is independent of `evals/ground_truth/` and contains no expected
values.

- Catalog version: `v1-objective-fields-2026-08-30`
- Fields: 69
- Categories: engine/performance, transmission, drivetrain/differentials,
  suspension/axles/chassis, brakes/wheels/tires, audio, driver assistance,
  and configuration dependencies
- SHA-256: `875879e7ef3e12b63ea5a75dd0d5ef6a344bd2fd3bd5d7362a3a2497d07c7ed9`
- Subjective fields such as steering feel, fun, sound quality, ride quality,
  reliability opinions, and tuning potential are excluded.

The catalog hash is recorded in every persisted baseline result and is not
part of the frozen 24-file benchmark lock.

## Runner and artifacts

Use the safe dry-run by default:

```text
python -m enthusiast_lens.evaluation.full_web --dry-run
```

Explicit selection and paid execution require deliberate flags:

```text
python -m enthusiast_lens.evaluation.full_web --fixture <fixture-id> --live
python -m enthusiast_lens.evaluation.full_web --all --live
```

Formal results are stored under `artifacts/evals/full_web/<fixture-id>/` with
the answer-key-free result and a separate trajectory directory. Each fixture
gets a fresh `ResearchAgent`; no facts or answer-bearing cache is reused.
Completed results are skipped only when system version, model, instruction
hash, and catalog version/hash all match. Failed results are retained and are
not rerun unless `--retry-failed` is explicit. `--continue-on-failure` is also
explicit; there is no automatic paid retry.

The dry-run uses two maximum model calls per fixture and the configured Search
ceiling. Its rough estimate scales the Step 7 reference run (4 fields, 2
calls, 3,957 tokens, $0.00745575) by field and fixture count; it is planning
guidance, not a linear cost promise. The default hard accumulated-cost ceiling
for a formal Full-Web run is `$2.00`, and the runner stops before another
fixture when the ceiling would be exceeded.

No 12-fixture benchmark execution has been performed yet.
