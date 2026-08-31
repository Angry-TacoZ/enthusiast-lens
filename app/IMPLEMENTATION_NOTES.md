# Standalone UI branch notes

## Scope

- Standalone judge/demo UI only.
- New files are contained under `app/`.
- No benchmark, runner, grader, model, Gemini, vPIC, API server, or root
  changelog files are changed.

## Data boundary

- `src/types.ts` mirrors the existing canonical result envelope for compile-time
  frontend checks; it does not define a new product schema.
- `src/data/recordedRun.ts` is a compact, labeled excerpt of the repository's
  tracked Full-Web run. It is presentation data, not ground truth.
- `src/lib/analysisClient.ts` is the single replacement seam. The real FastAPI
  adapter should implement that interface after the backend route and error
  contract are stable.

## Merge reconciliation

- Reconcile a meaningful UI entry into `CHANGELOG.md` only after the Hybrid
  branch has landed.
- Decide whether TypeScript types will be generated from FastAPI OpenAPI or
  contract-tested against a fixture before live API wiring.
- Share report components with the Chrome MV3 extension only after the
  standalone experience and API shape are stable.

## Visual interaction

- The welcome state includes a CSS/SVG line-art sports-car mark centered above
  the hero copy. Its trace, wheel, scan, glow, and speed-line motion all stop
  cleanly under `prefers-reduced-motion`.
