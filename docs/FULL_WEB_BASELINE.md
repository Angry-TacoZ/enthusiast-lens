# Full-Web benchmark baseline

Status: V1 historical failure preserved; V2 implemented and not yet live-executed.

The Full-Web baseline is the simple, reproducible comparison path:

```text
answer-key-free runtime vehicle input
  -> fixed canonical V1 scoring-field catalog
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

## Runtime identities

### Full-Web V1 — historical evidence

`full-web-baseline-v1` identifies the first formal Miata attempt. It used the
45-second Phase A parent deadline, the original 30-second Phase B parent
deadline, and serialized full raw grounding support mappings into Phase B.
Phase A completed with 8 Search queries and 28 grounded sources, but Phase B
exceeded its parent deadline. Provider cost was unavailable and no correctness
grading was performed. Its result and trajectory remain immutable historical
engineering/evaluation evidence.

### Full-Web V2 — active benchmark candidate

`full-web-baseline-v2` retains the same model, task catalog, Search policy,
structured schema semantics, evidence-first architecture, source-ID provenance,
benchmark inputs, ground truth, and scoring contract. It changes the global
Phase B hard parent deadline to 60 seconds and omits redundant raw support
mappings only from the Phase B transport projection while preserving the full
EvidenceBundle in the trajectory. Because these materially change runtime
behavior, V2 has a distinct system identity and has not yet had a live formal
execution.

## Fixed task definition

The machine-readable catalog is
[`evals/task_definition/v1_objective_field_catalog.json`](../evals/task_definition/v1_objective_field_catalog.json).
It was structurally reconciled before the first formal benchmark execution
against sections 3.1-3.8 of the human-readable V1 Schema and Evaluation
Specification and the frozen scorable field-ID contract. It contains objective
identifiers, categories, descriptions, and acquisition classification only;
it contains no expected values.

- Catalog version: `v1-objective-fields-2026-08-30-structural-alignment`
- Canonical scored fields: 92
- Agent-research targets: 91
- Deterministic derived fields: 1
  (`engine_and_measured_performance.power_to_weight_hp_per_us_ton`, calculated
  from canonical horsepower and curb weight)
- SHA-256: `439d5fc674c25f040da52efb8a391d6a28366a4b1822b3bd96c057e933501b43`
- Subjective fields such as steering feel, fun, sound quality, ride quality,
  reliability opinions, and tuning potential are excluded.

The structural audit is preserved at
[`artifacts/audits/v1_field_alignment_audit.json`](../artifacts/audits/v1_field_alignment_audit.json).
It extracts only field IDs, categories, labels, and `scorable` metadata from
the frozen fixtures. The catalog hash is recorded in every persisted baseline
result and is not part of the frozen 24-file benchmark lock.

## Runner and artifacts

Use the safe all-fixture dry-run by default:

```text
python -m enthusiast_lens.evaluation.full_web
python -m enthusiast_lens.evaluation.full_web --dry-run
```

Explicit selection and paid execution require deliberate flags:

```text
python -m enthusiast_lens.evaluation.full_web --fixture <fixture-id> --live
python -m enthusiast_lens.evaluation.full_web --all --live
```

`--live` without either `--fixture` or `--all` is rejected before the runner
or provider is constructed.

Formal results are stored under `artifacts/evals/full_web/<fixture-id>/` with
the answer-key-free result and a separate trajectory directory. Each fixture
gets a fresh `ResearchAgent` with the 91 research targets; the runner then
adds the one explicitly classified deterministic canonical fact. No facts or
answer-bearing cache is reused.
Completed results are skipped only when system version, model, instruction
hash, and catalog version/hash all match. Every current `result.json` is moved
unchanged to a named `attempt-*.json` artifact before a genuine new attempt
replaces it, including failed-to-successful retries and identity changes.
Failed results are not rerun unless `--retry-failed` is explicit.
`--continue-on-failure` is also explicit; there is no automatic paid retry.

The dry-run uses two maximum model calls per fixture and reports the configured
Search value as a declared planning budget. Gemini's Generate Content Google
Search tool does not expose an application-enforceable per-request query cap,
so this value is not called a ceiling and does not invalidate evidence when
the provider emits more queries. Formal results record the actual observed
`search_query_count`.

Evidence acquisition has a 45-second hard parent deadline and structured
synthesis has a 60-second hard parent deadline. These are global `ResearchAgent`
policies shared by Full-Web and future Hybrid execution; they are not adjusted
by vehicle or fixture. The persisted EvidenceBundle retains full provider
grounding support metadata, while Phase B receives a deterministic transport
projection with the same source IDs, URLs, titles, and grounded text but without
duplicating raw support mappings already represented by that text.

The rough cost estimate scales the Step 7 reference run (4 research fields, 2
calls, 3,957 tokens, $0.00745575) by field and fixture count; it is planning
guidance, not a linear cost promise. The default hard accumulated-cost ceiling
for a formal Full-Web benchmark is `$2.00`. Resumed runs include measured cost
from each matching current and archived fixture attempt within the active
system/model/instruction/catalog identity before another provider call. An
unknown cost in any matching V2 attempt stops further paid V2 execution because
the remaining V2 budget cannot be established safely. Byte-identical duplicated
artifacts are not double-counted, while distinct matching archived attempts
remain part of measured V2 spend. The V1 failed attempt remains an unknown
project/provider cost; it is neither treated as zero nor charged against V2's
identity-scoped `$2.00` benchmark ceiling. Complete project/provider spend is
therefore at least measured V2 spend plus the unknown V1 amount. The current
all-fixture dry run projects `$2.03541975`, so the default guard will stop before
an additional V2 call would exceed `$2.00`.

No 12-fixture benchmark execution has been performed yet.
