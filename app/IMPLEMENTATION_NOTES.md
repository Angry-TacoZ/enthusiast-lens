# Standalone UI branch notes

## Scope

- Standalone judge UI only.
- New files are contained under `app/`.
- No benchmark, runner, grader, model, Gemini, vPIC, API server, or root
  changelog files are changed.

## Data boundary

- `src/types.ts` mirrors the existing canonical result envelope for compile-time
  frontend checks; it does not define a new product schema.
- `src/data/recordedRun.ts` supplies a local Core 24 canonical record for
  offline operation. It is presentation data, not ground truth.
- `src/lib/analysisClient.ts` is the single replacement seam for a shared API
  client.

## Merge reconciliation

- Reconcile a meaningful UI entry into `CHANGELOG.md` when merging the UI
  branch; this branch intentionally leaves the shared changelog untouched.
- Preserve the Core 24 field-alignment test when wiring the shared API.
- Share report components with the Chrome MV3 extension after the shared API
  shape is stable.

## Visual interaction

- The welcome state includes a CSS/SVG line-art sports-car mark centered above
  the hero copy. Its trace, wheel, scan, glow, and speed-line motion all stop
  cleanly under `prefers-reduced-motion`.
