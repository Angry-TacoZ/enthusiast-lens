# Enthusiast Lens Ground-Truth Freeze Readiness

Generated: 2026-08-30T01:28:33-04:00

- Vehicle families: **11**
- Benchmark fixture files: **12**
- Frozen fixtures: **12**
- Draft fixtures: **0**
- JSON Schema validation errors: **0**

## Status

All benchmark fixtures are frozen. The paired MINI steering-wheel evidence is saved locally, the Tesla HW4 fixture is tied to an exact VIN, and the corrected Charger fixture is tied to exact VIN `2C3CDBDK2SR559586` with preserved OEM Track Package evidence. The benchmark lock was regenerated after this authorized pre-evaluation correction; all 12 runtime inputs are ready. The scoring aggregation rule remains frozen in `SCORING_POLICY.md`.

Run `python audit_ground_truth.py` from this directory before any comparative evaluation run.
