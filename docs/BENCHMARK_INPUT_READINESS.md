# Benchmark Input Readiness

This inventory describes the frozen runtime-input corpus in `evals/inputs/benchmark_inputs.json`. It contains vehicle identity, advertised configuration, and public input-source metadata only. It does not reproduce expected enthusiast facts, grading tolerances, or answer-key provenance.

| Fixture | Vehicle family | Exact VIN | Listing/source preserved | vPIC verified | Configuration/package sufficient | Runtime ready | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `01_miata_gt_auto_ground_truth.json` | `01_miata` | `JM1NDAD70T0702556` | Clay Cooley Mazda, stock `T0702556A` | Yes | Yes | Yes | None |
| `02a_mini_acc_true_positive_ground_truth.json` | `02_mini` | `WMWXR5C00L2M13510` | CarGurus `451744696` | Yes | Yes | Yes | None |
| `02b_mini_acc_false_positive_ground_truth.json` | `02_mini` | `WMWXR5C02M2N13321` | CarGurus `435848455` | Yes | Yes | Yes | None |
| `03_gr86_base_ground_truth.json` | `03_gr86` | `JF1ZNBC19N8757552` | Cars.com listing index | Yes | Yes | Yes | None |
| `04_mustang_ecoboost_premium_ground_truth.json` | `04_mustang` | `1FA6P8TDXL5178353` | Bob Ruth Ford listing | Yes | Yes: HPP, Safe & Smart, Premium Plus/201A, and B&O advertised | Yes | None |
| `05_elantra_n_line_ground_truth.json` | `05_elantra_n_line` | `KMHLR4DF8RU776774` | CarGurus listing index | Yes | Yes | Yes | None |
| `06_cadillac_ats_base_ground_truth.json` | `06_cadillac_ats` | `1G6AA5RX7J0125600` | Auto Boutique Texas, stock `T25104` | Yes | Yes: dealer lists RWD/manual sedan; vPIC trim is `Standard` | Yes | None |
| `07_jeep_wrangler_rubicon_4xe_ground_truth.json` | `07_wrangler_4xe` | `1C4RJXR62SW584938` | Cars.com, stock `UM11105` | Yes | Yes | Yes | None |
| `08_charger_daytona_ground_truth.json` | `08_charger_daytona` | Unresolved | No exact accepted source | No | No | No | No public exact-VIN source found that reliably proves the vehicle is without the Track Package |
| `09_kia_soul_turbo_ground_truth.json` | `09_kia_soul` | `KNDJ53AF4N7819134` | TrueCar, stock `V768901A` | Yes | Yes: Turbo DCT advertised; vPIC trim is `GT Line Turbo` | Yes | None |
| `10_tesla_model_y_long_range_awd_ground_truth.json` | `10_tesla_model_y` | `7SAYGDEE3PF885285` | Urban Motors, stock `72372` | Yes | Yes: HW4/AI4 advertised | Yes | None |
| `11_wrx_limited_cvt_ground_truth.json` | `11_subaru_wrx` | `JF1VBAN66T8800249` | Subaru of Georgetown window sticker | Yes | Yes | Yes | None |

## Summary

- 11 of 12 fixtures have an exact VIN, preserved public input-source metadata, successful live NHTSA vPIC decoding, sufficient identity/configuration evidence, and are runtime-ready.
- 8 of the 9 previously missing VINs were resolved without changing the frozen answer key.
- The Charger remains unresolved because `without the Track Package` could not be proven for an exact public VIN. A nearby Scat Pack/AWD listing was not accepted.
- The paired MINI fixtures remain separate runtime inputs belonging to one vehicle family.
- Volatile public listing metadata is preserved in `evals/inputs/evidence/public_source_snapshots.json` without enthusiast conclusions.
