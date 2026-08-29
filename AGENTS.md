# Enthusiast Lens Engineering Rules

## 1. Inspect before editing

Before changing code:

1. Inspect the relevant implementation.
2. Inspect related tests.
3. Inspect schemas/interfaces affected by the change.
4. Identify the likely blast radius.
5. Prefer the smallest change that satisfies the requirement.

Do not guess how an existing component works when the repository can be inspected.

## 2. Frozen benchmark is read-only

Everything under:

`evals/ground_truth/`

is the frozen V1 evaluation benchmark unless a human explicitly authorizes a benchmark revision.

Never:
- change ground-truth answers;
- rewrite or reformat benchmark JSON;
- rename benchmark fixtures;
- alter evidence;
- alter `benchmark_lock.json`;
- alter `SCORING_POLICY.md`;
- “fix” source data because an implementation disagrees with it.

Before comparative evaluation runs, verify the benchmark lock.

If implementation output conflicts with the benchmark, investigate the implementation first.

## 3. Evaluation is part of the build

A feature is not complete merely because it runs.

Meaningful behavior changes must be evaluated.

For experiments:

1. State the hypothesis before judging the result.
2. Use the same input cases for compared systems.
3. Use the same output schema and scoring rules.
4. Preserve raw results.
5. Record evidence supporting the decision.
6. Preserve useful failed or removed experiments.
7. Check for regressions after improvements.

Do not cherry-pick successful examples.

## 4. Baseline and candidate must remain comparable

The planned experiment is:

### Full-Web baseline
Vehicle/listing context → agent researches the complete enthusiast schema from web sources.

### Hybrid candidate
Vehicle/listing context → Car2DB structured facts → identify missing/weak/ambiguous fields → targeted web research → reconciliation.

Both systems must:
- receive equivalent benchmark vehicle context;
- emit the same canonical schema;
- be graded by the same deterministic grader;
- preserve provenance;
- record comparable runtime/resource metrics.

Do not quietly give one system extra ground-truth information or privileged context.

## 5. Deterministic work stays deterministic

Use normal code rather than an LLM for tasks that do not require judgment.

Examples:
- API requests
- schema validation
- normalization
- aliases
- unit conversion
- horsepower-to-weight calculations
- caching
- filtering/sorting
- benchmark loading
- range/tolerance comparisons
- score calculation
- report generation
- UI formatting

The agent should be used only where reasoning or evidence reconciliation is actually required.

## 6. One research/reconciliation agent for V1

Do not introduce a multi-agent architecture unless a measured experiment demonstrates a clear need.

The V1 agent may:
- interpret exact vehicle configuration;
- identify missing or inadequate enthusiast facts;
- formulate targeted research questions;
- research gaps;
- reconcile conflicting evidence;
- detect trim/transmission/drivetrain/package/build-date/market dependencies;
- evaluate source relevance;
- return structured provenance and confidence.

Keep orchestration as simple as possible.

## 7. `Unknown` is a valid result

Never fabricate a vehicle specification because the schema expects a field.

If reliable evidence is insufficient:

`Unknown`

is preferred over an unsupported assertion.

A knowable ground-truth fact returned as Unknown may reduce evaluation coverage, but it is preferable to hallucination.

## 8. Preserve provenance

Every externally researched factual value should retain enough provenance to determine:
- source URL;
- publisher/source type where available;
- whether the source matches the exact configuration;
- confidence or verification state where applicable.

Do not strip provenance during normalization.

## 9. Configuration identity matters

Do not assume year + model is sufficient.

Vehicle facts may depend on:
- trim;
- transmission;
- drivetrain;
- package;
- market;
- build date;
- hardware generation;
- software entitlement.

Avoid importing facts from nearby configurations.

This is a core product requirement, not an edge case.

## 10. Objective-only scored core

The V1 scored product schema is objective.

Do not introduce subjective scored fields such as:
- steering feel;
- fun factor;
- exhaust sound quality;
- perceived ride quality;
- subjective handling quality;
- interior quality;
- tuning potential;
- reliability reputation.

Objective hardware such as active exhaust valves, suspension type, differential type, audio hardware, and ADAS capability is allowed.

## 11. Security and trust boundaries

- Secrets belong in environment variables.
- Never commit API keys, tokens, credentials, or private data.
- Provide `.env.example` when configuration is introduced.
- Treat web/API responses as untrusted external input.
- Validate agent output before consuming it.
- Preserve human approval for any consequential external action.
- This project should not perform autonomous purchases or other consequential vehicle transactions.

## 12. Tests are required

When implementation begins, add deterministic tests for applicable behavior.

At minimum, the completed system should cover:
- schema validation;
- normalization;
- unit conversion;
- aliases;
- accepted ranges/tolerances;
- Unknown handling;
- benchmark lock validation;
- scoring;
- MINI family aggregation;
- malformed agent output;
- Car2DB adapter behavior;
- configuration dependency handling.

A change that breaks existing tests is not complete.

## 13. Verification before completion

Before declaring implementation work complete, run the relevant:
- tests;
- lint/type checks once configured;
- build once configured;
- benchmark audit where relevant;
- benchmark-lock verification where relevant.

Report actual command results.

Do not say something works merely because the code appears correct.

## 14. Observability

Agentic operations should be inspectable.

Preserve, where applicable:
- input context;
- agent instructions;
- research queries;
- tool calls;
- tool results;
- selected sources;
- retries;
- validation failures;
- final structured output;
- latency;
- model usage;
- estimated cost;
- cache usage.

Representative trajectories will be required for the hackathon submission.

## 15. Reproducibility

Prefer:
- pinned runtime versions;
- lockfiles;
- deterministic setup;
- documented environment variables;
- exact commands;
- locally saved benchmark inputs/evidence;
- machine-readable outputs.

Another person should be able to clone the repository and reproduce the important results.

## 16. Changelog discipline

`CHANGELOG.md` records meaningful project evolution, not every file edit.

Update it when there is a meaningful:
- architecture decision;
- scope decision;
- schema change;
- evaluation-method change;
- benchmark revision;
- experiment;
- important failed/removed approach;
- implementation finding that materially changes the chosen approach.

For experiments, include:
- what changed;
- why;
- evidence/result;
- keep/remove/learning.

Do not rewrite earlier changelog history unless correcting a factual mistake.

## 17. Scope discipline

The hackathon deadline matters.

V1 priorities are:
1. correct end-to-end workflow;
2. measurable Full-Web vs Hybrid comparison;
3. reproducibility;
4. evidence/trajectories;
5. simple usable interface.

Do not expand scope simply because an additional feature would be interesting.

The browser extension is an interface to the core pipeline, not the core architecture.

## 18. Model/resource discipline

Use the least expensive model/tool that is adequate for the task when model choice is under implementation control.

Do not use an LLM for deterministic processing.

Any model-routing strategy that becomes part of the submitted system must be testable and its effect measurable.

## 19. Do not contaminate evaluation

The agent/runtime being evaluated must never receive:
- ground-truth fixture answers;
- grader expectations;
- benchmark scoring values;
- hidden answer-key evidence intended only for evaluation.

Ground truth is for the deterministic grader, not the research agent.

Keep benchmark inputs and answer keys logically separated in code.

## 20. Completion gate for agent/evaluation work

Do not mark a meaningful agent/evaluation task complete unless the applicable items exist:

- defined input;
- defined structured output;
- validation;
- same-case comparison where relevant;
- raw evidence/results;
- failure review;
- reproducible command;
- uncertainty/Unknown behavior;
- no benchmark contamination;
- changelog update if the result changed a meaningful project decision.
