import { describe, expect, it } from 'vitest'
import { recordedClient } from './recordedClient'

describe('recorded demo', () => {
  it('returns the preserved Miata result with provenance', async () => {
    const job = await recordedClient.startAnalysis('miata-gt-auto', 'full_web')
    expect(job.status).toBe('succeeded')
    expect(job.result?.facts).toHaveLength(24)
    expect(job.result?.facts.some(fact => fact.provenance.length > 0)).toBe(true)
    expect(job.result?.trajectory_path).toBeNull()
  })
  it('keeps the failed Hybrid GR86 attempt failed', async () => {
    const job = await recordedClient.startAnalysis('gr86-base', 'hybrid')
    expect(job.status).toBe('failed')
    expect(job.result).toBeUndefined()
  })
  it('does not fabricate results for vehicles without recordings', async () => {
    const job = await recordedClient.startAnalysis('charger-daytona', 'full_web')
    expect(job.status).toBe('failed')
    expect(job.result).toBeUndefined()
  })
})
