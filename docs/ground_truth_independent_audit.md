# Enthusiast Lens Ground-Truth Independent Audit

Audit timestamp: 2026-08-30T01:28:33-04:00

## Result

**PASS after corrections.**

- 11 original vehicle families
- 12 benchmark fixtures (MINI contributes paired true/false ACC subcases)
- 12 frozen fixtures
- 0 draft fixtures
- 0 JSON Schema validation errors
- 0 duplicate field IDs
- 0 scorable facts with unresolved/non-verified status
- 0 scorable facts lacking at least one supporting source
- required MINI steering-wheel evidence present
- Tesla HW4 case now grounded to an exact real 2023 Long Range AWD VIN
- Charger case corrected before evaluation to an exact real 2025 Scat Pack AWD VIN with OEM-documented Track Package configuration
- benchmark lock regenerated after the authorized Charger correction

## Corrections made during audit

1. Fixed the stale readiness report that still displayed old MINI draft counts after both MINI fixtures had already been frozen.
2. Corrected the 2021 MINI false-positive fixture to use the 2021 owner manual and separated the marketplace ACC claim from sources that actually support other listing facts.
3. Corrected the Mustang metadata so the B&O 12-speaker system is an explicit separate option (583), not implied to be included automatically with 201A.
4. Replaced migrated/dead historical Ford PDF source URLs with a surviving mirror of the original Ford Division 2020 order guide while retaining Ford's live HPP release where possible.
5. Grounded the Tesla HW4 benchmark to exact VIN `7SAYGDEE3PF885285` instead of relying only on a generic 2023 HW4 assertion.
6. Defined the primary metric as an 11-family macro-average so uneven fixture fact counts do not bias the comparison and MINI does not receive double weight.
7. Added a deterministic `audit_ground_truth.py` script so Codex/judges can re-run the structural audit.
8. Corrected the Charger fixture before Full-Web or Hybrid evaluation began: exact-VIN OEM-sticker research found the earlier non-Track assumption unsupported. The corrected fixture is tied to VIN `2C3CDBDK2SR559586`, revalidates all Track Package-dependent facts, and remains frozen.

## Important boundary

The audit verifies fixture structure, freeze status, source presence, internal consistency, evidence presence, and a targeted web spot-check of the unusual configuration claims. It is not a substitute for re-downloading and manually reading every external source on every future run. Source URLs can change over time, which is why critical listing evidence is also snapshotted locally where practical.
