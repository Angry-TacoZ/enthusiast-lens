# Full-Web benchmark baseline

Status: V1, V2, and V3 historical failures are preserved; V4 is implemented
offline and has not had a live execution.

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

### Full-Web V2 — historical evidence

`full-web-baseline-v2` retains the same model, task catalog, Search policy,
structured schema semantics, evidence-first architecture, source-ID provenance,
benchmark inputs, ground truth, and scoring contract. It changed the global
Phase B hard parent deadline to 60 seconds and omits redundant raw support
mappings only from the Phase B transport projection while preserving the full
EvidenceBundle in the trajectory. Because these materially change runtime
behavior, V2 has a distinct system identity. Its one formal Miata attempt
reached the 45-second Phase A parent deadline during the first Search-grounded
call; Phase B never began, and no correctness grading was performed.

### Full-Web V3 — historical evidence

`full-web-baseline-v3` retains the V2 model, thinking level, Search policy,
task catalog, structured schema, source-ID provenance, 92-field output
contract, scoring contract, ground truth, benchmark inputs, and 45-second
Phase A / 60-second Phase B parent deadlines. It changes only the deterministic
Phase A workload unit: one `ResearchAgent` preserves requested-field order and
splits the 91 research targets into four Search-grounded calls of 24, 24, 24,
and 19 fields, then performs one Phase B synthesis over the complete set. Its
formal Miata run completed all four Phase A batches (28 Search queries, 69
grounded sources, 111,219 ms measured Phase A latency, and $0.064875 measured
Phase A cost), but the single Phase B call exceeded its unchanged 60-second
deadline. No grading or retry was performed.

### Full-Web V4 — active benchmark candidate

`full-web-baseline-v4` preserves the V3 model, thinking level, Search policy,
task catalog, structured schema, provenance contract, and 45-second Phase A /
60-second Phase B parent deadlines. It changes only deterministic Phase B
workload containment: after the matching Phase A batches complete, one
ResearchAgent synthesizes 24, 24, 24, and 19 fields in four Search-disabled
calls. Each synthesis call receives only the corresponding Phase A
EvidenceBundle, and validated canonical facts are merged deterministically in
the original requested-field order. This is eight maximum model calls with no
retry, no extra agent, and no V4 provider execution yet.

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

The dry-run derives the maximum calls from the frozen 24-field Phase A and
Phase B batch sizes: a 91-field fixture has four evidence-acquisition calls and
four matching synthesis calls, for eight maximum model calls per fixture. It reports the configured Search
value as a declared planning budget. Gemini's Generate Content Google
Search tool does not expose an application-enforceable per-request query cap,
so this value is not called a ceiling and does not invalidate evidence when
the provider emits more queries. Formal results record the actual observed
`search_query_count`.

Each Phase A batch has the same 90-second hard parent deadline, while each
structured synthesis batch has the same 60-second hard parent deadline. These
are global `ResearchAgent` policies shared by Full-Web and Hybrid
execution; they are not adjusted by vehicle or fixture. Successful Phase A
batches merge deterministically: search queries and provider grounding support
metadata are retained, identical URLs share one stable source ID with the union
of distinct grounded text/support records, and the complete merged bundle stays
in the trajectory for auditability. Each Phase B batch receives only its
matching Phase A source-ID-preserving transport projection without duplicate raw
support mappings.

The rough cost estimate scales the Step 7 reference run (4 research fields, 2
calls, 3,957 tokens, $0.00745575) by field and fixture count; it is planning
guidance, not a linear cost promise. The earlier `$2.00` budget was a
conservative planning safeguard, not an execution ceiling. At this engineering
point Google billing reported approximately `$0.12` of project spend, but that
observation is not encoded as a runtime fact or limit. The runner reports
accumulated known measured cost and the count of unknown-cost matching attempts;
it never treats an unknown cost as zero. Cost data does not block a deliberately
authorized live execution or explicit `--retry-failed` retry. There are still
no automatic retries: `--live` and `--retry-failed` remain explicit controls,
and preserving every result/trajectory and prior attempt is the primary audit
mechanism.

No 12-fixture benchmark execution has been performed yet.
