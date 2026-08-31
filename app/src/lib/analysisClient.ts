import { recordedRun } from '../data/recordedRun'
import type { AnalysisRecord, RunMode } from '../types'

export interface AnalysisClient {
  loadRecordedRun(vehicleId: string, mode: RunMode): Promise<AnalysisRecord | null>
}

/**
 * The UI's only analysis-data dependency. A shared API implementation can
 * replace this local client without changing report components.
 */
export const recordedRunClient: AnalysisClient = {
  async loadRecordedRun(vehicleId, mode) {
    await new Promise((resolve) => window.setTimeout(resolve, 550))
    if (vehicleId !== 'miata-gt-auto' || mode !== 'full_web') return null
    return structuredClone(recordedRun)
  },
}
