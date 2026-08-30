# Deterministic benchmark grader

`enthusiast_lens.evaluation.grader` is the only evaluation component that reads
the frozen answer key under `evals/ground_truth/`. The Full-Web runner and the
research agent remain answer-key-free.

It receives a completed canonical result and its matching frozen fixture, then
applies only the fixture's stored comparison metadata:

- exact values after case/whitespace string normalization;
- explicit fixture aliases;
- inclusive accepted ranges and numeric tolerances; and
- recursive exact comparison for lists and objects.

For each scorable fact, `C` is correct known output, `K` is all known output,
`E` is incorrect known output, and `U` is missing or non-known output. The
metrics are CEFC `C / N`, attempted accuracy `C / K`, attempted error rate
`E / K`, and Unknown rate `U / N`. Any zero-denominator rate is `null`, never
silently treated as zero.

Correct known non-derived facts also require at least one provenance record for
the provenance-success metric. A correct deterministic-derived fact still
counts toward CEFC but is provenance-exempt.

Fixture scores are grouped by `vehicle_family_id`; the paired MINI fixtures are
averaged within MINI before the headline unweighted family-macro CEFC is
calculated. The scorer writes a per-fixture `score.json` plus JSON and Markdown
summary files. Each artifact records the grader version, SHA-256 of the frozen
`benchmark_lock.json`, and SHA-256 of the comparison-rule declaration.

Example local-only command:

```powershell
python -m enthusiast_lens.evaluation.grader `
  --result artifacts/evals/full_web/01_miata_gt_auto_ground_truth.json/result.json `
  --ground-truth evals/ground_truth/01_miata_gt_auto_ground_truth.json
```

This command does not call Gemini or any external provider.
