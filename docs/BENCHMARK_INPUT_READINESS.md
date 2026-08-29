# Benchmark Input Readiness

This inventory reports only input identity metadata already present in the frozen benchmark. It does not reproduce ground-truth facts and does not create runtime seed data from the answer key.

| Fixture | Vehicle family | Model year | Exact VIN available | Listing ID or URL available | Future direct vPIC decode |
| --- | --- | ---: | --- | --- | --- |
| `01_miata_gt_auto_ground_truth.json` | `01_miata` | 2026 | No | No | Blocked: exact VIN missing |
| `02a_mini_acc_true_positive_ground_truth.json` | `02_mini` | 2020 | Yes | Yes | Ready |
| `02b_mini_acc_false_positive_ground_truth.json` | `02_mini` | 2021 | Yes | Yes | Ready |
| `03_gr86_base_ground_truth.json` | `03_gr86` | 2022 | No | No | Blocked: exact VIN missing |
| `04_mustang_ecoboost_premium_ground_truth.json` | `04_mustang` | 2020 | No | No | Blocked: exact VIN missing |
| `05_elantra_n_line_ground_truth.json` | `05_elantra_n_line` | 2024 | No | No | Blocked: exact VIN missing |
| `06_cadillac_ats_base_ground_truth.json` | `06_cadillac_ats` | 2018 | No | No | Blocked: exact VIN missing |
| `07_jeep_wrangler_rubicon_4xe_ground_truth.json` | `07_wrangler_4xe` | 2025 | No | No | Blocked: exact VIN missing |
| `08_charger_daytona_ground_truth.json` | `08_charger_daytona` | 2025 | No | No | Blocked: exact VIN missing |
| `09_kia_soul_turbo_ground_truth.json` | `09_kia_soul` | 2022 | No | No | Blocked: exact VIN missing |
| `10_tesla_model_y_long_range_awd_ground_truth.json` | `10_tesla_model_y` | 2023 | Yes | Yes | Ready |
| `11_wrx_limited_cvt_ground_truth.json` | `11_subaru_wrx` | 2026 | No | No | Blocked: exact VIN missing |

## Summary

- 3 of 12 fixtures already have exact VINs and can use vPIC directly in a future evaluation.
- Those same 3 fixtures have an existing listing identifier or URL in frozen identity/evidence metadata.
- 9 fixtures lack an exact VIN and remain blocked for direct vPIC input until a public runtime input is supplied outside the frozen answer key.
- The paired MINI fixtures are separate inputs belonging to one vehicle family.
