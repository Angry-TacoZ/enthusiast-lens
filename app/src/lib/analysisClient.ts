import type { AnalysisRecord, RunMode } from '../types'

export type AnalysisJobStatus = 'queued' | 'running' | 'succeeded' | 'partial' | 'failed'
export interface AnalysisJob { id: string; status: AnalysisJobStatus; result?: AnalysisRecord; error?: string }
export interface AnalysisClient {
  startAnalysis(vehicleId: string, mode: RunMode): Promise<AnalysisJob>
  getAnalysis(jobId: string): Promise<AnalysisJob>
}

const API_BASE_URL = (import.meta.env.VITE_ANALYSIS_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } })
  } catch {
    throw new Error('The local analysis server is not reachable. Start it and try again.')
  }
  const body = (await response.json().catch(() => null)) as { detail?: string; error?: string } | null
  if (!response.ok) throw new Error(body?.error ?? body?.detail ?? 'The analysis request could not be completed.')
  return body as T
}

export const analysisApiClient: AnalysisClient = {
  startAnalysis(vehicleId, mode) {
    return request<AnalysisJob>('/api/analysis-runs', { method: 'POST', body: JSON.stringify({ vehicle_id: vehicleId, mode }) })
  },
  getAnalysis(jobId) {
    return request<AnalysisJob>(`/api/analysis-runs/${encodeURIComponent(jobId)}`)
  },
}
