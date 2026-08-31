# Hackathon Core 24 Frozen Scoring Policy

Version: `hackathon-core-24-comparison-rules-v1`  
Grader: `deterministic-core-24-grader-v1`

This corpus is independent of the historical 92-field V1 benchmark in
`evals/ground_truth/`. It was frozen before any paid Core 24 Full-Web or Hybrid
execution. Later system behavior may not be used to change answers or
tolerances.

Each fixture contains exactly 24 canonical fields. A known, applicable fact is
scorable. An applicable fact marked `unresolved` is excluded because exact
configuration evidence was unavailable before freeze. A fact marked
`not_applicable` is excluded by powertrain/transmission semantics and is never
treated as Unknown or error.

For scorable fields, `C` is a matching known output, `E` is a non-matching known
output, and `U` is missing or non-known output. `C + E + U = N`. CEFC is `C/N`,
attempted accuracy is `C/(C+E)`, required error rate is `E/N`, and Unknown rate
is `U/N`. Correct researched facts require provenance; deterministic
pounds-per-horsepower is provenance-exempt.

Headline CEFC is the unweighted macro-average across 11 vehicle families. The
two MINI fixtures are first averaged into one MINI family score, preventing the
paired diagnostic from receiving double weight.

All numeric tolerances, aliases, compound shapes, powertrain semantics, ADAS
definitions, and instrumented-test rules are authoritative in
`comparison_rules.json`. Compound fields receive one canonical outcome, but
every required component must match. A partial object is not a correct field.

Every scorable answer has non-vPIC provenance. vPIC may corroborate evaluated
Hybrid runtime behavior, but it is never the sole answer-key source here.
