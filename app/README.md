# Enthusiast Lens standalone app

Judge-facing React/Vite interface for the canonical Enthusiast Record. The UI
does not own analysis logic and does not read the frozen answer key.

## Current data boundary

`src/data/recordedRun.ts` is a small, explicitly labeled excerpt from the
tracked Full-Web evaluation artifact. It exists so the UI is usable while the
FastAPI endpoints are implemented in parallel. `src/lib/analysisClient.ts`
defines the replaceable client boundary; no backend route name is assumed.

## Commands

```powershell
npm.cmd install
npm.cmd run dev
npm.cmd run lint
npm.cmd run test
npm.cmd run build
```

The production build contains no API credentials. Provider keys remain on the
server side.
