import type { AnalysisRecord, RunMode } from '../types'
import type { AnalysisClient, AnalysisJob } from './analysisClient'

// Only committed, answer-key-free run results are loaded. No grader or answer key.
const runs = import.meta.glob<AnalysisRecord>(
  '../../../artifacts/evals/{full_web_core_24,hybrid_core_24}/*/result.json',
  { import: 'default' },
)
const fixtures: Record<string, string> = {
  'miata-gt-auto': '01_miata_gt_auto_ground_truth.json',
  'gr86-base': '03_gr86_base_ground_truth.json',
  'kia-soul-turbo': '09_kia_soul_turbo_ground_truth.json',
  'wrx-limited': '11_wrx_limited_cvt_ground_truth.json',
}

export function recordingAvailability(vehicleId: string, mode: RunMode) {
  if (!fixtures[vehicleId]) return 'Demo simulation available'
  return vehicleId === 'gr86-base' && mode === 'hybrid' ? 'Recorded run failed' : 'Recorded result available'
}

export async function loadRecordedRun(vehicleId: string, mode: RunMode): Promise<AnalysisRecord> {
  const folder = mode === 'hybrid' ? 'hybrid_core_24' : 'full_web_core_24'
  const load = runs[`../../../artifacts/evals/${folder}/${fixtures[vehicleId]}/result.json`]
  if (!load) throw new Error('No recorded run is available for this selection.')
  return load()
}

export const recordedClient: AnalysisClient = {
  async startAnalysis(vehicleId, mode) {
    const folder = mode === 'hybrid' ? 'hybrid_core_24' : 'full_web_core_24'
    const load = runs[`../../../artifacts/evals/${folder}/${fixtures[vehicleId]}/result.json`]
    if (!load) return { id: 'recorded', status: 'failed', error: 'No recorded run is available for this vehicle. Choose Miata, GR86, Soul Turbo, or WRX.' }
    const result = await load()
    if (result.status === 'failed') return { id: 'recorded', status: 'failed', error: 'This recorded attempt did not complete within the fixed research deadline. Its failure is preserved in the benchmark evidence.' }
    return { id: 'recorded', status: result.status as AnalysisJob['status'], result: { ...result, trajectory_path: null } }
  },
  async getAnalysis() {
    throw new Error('Recorded results do not require polling.')
  },
}
