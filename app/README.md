# Enthusiast Lens standalone app

Judge-facing React/Vite interface for the canonical Enthusiast Record. The UI
does not own analysis logic and does not read the frozen answer key.

## Data boundary

`src/data/recordedRun.ts` supplies a local canonical Core 24 record for
offline UI operation. `src/lib/analysisClient.ts` is the sole data boundary;
a shared API client can replace it without changing the report components.

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
