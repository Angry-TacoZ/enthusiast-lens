import { recordedRun } from '../data/recordedRun'
import type { AnalysisRecord, RunMode } from '../types'

export interface AnalysisClient {
  loadRecordedRun(vehicleId: string, mode: RunMode): Promise<AnalysisRecord | null>
}

/**
 * Deliberately local until the backend publishes its validated API contract.
 * Keeping the adapter replaceable avoids hard-coding a speculative route.
 */
export const recordedRunClient: AnalysisClient = {
  async loadRecordedRun(vehicleId, mode) {
    await new Promise((resolve) => window.setTimeout(resolve, 550))
    if (vehicleId !== 'miata-gt-auto' || mode !== 'full_web') return null
    return structuredClone(recordedRun)
  },
}
