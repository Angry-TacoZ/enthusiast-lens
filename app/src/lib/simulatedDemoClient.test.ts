import { describe, expect, it, vi } from 'vitest'
import { simulateDemoRun, demoStages } from './simulatedDemoClient'
import { vehicleOptions } from '../data/vehicles'
import { recordedRun } from '../data/recordedRun'
import { loadRecordedRun } from './recordedClient'

describe('simulation boundary', () => {
  it('uses all 24 field IDs, honest missing data and no requests or benchmark mutation', async () => {
    const before = JSON.stringify(await loadRecordedRun('miata-gt-auto', 'full_web'))
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    const progress = vi.fn()
    const result = await simulateDemoRun(vehicleOptions[7], 'hybrid', progress, 0)
    expect(result.facts.map(fact => fact.field_id)).toEqual(recordedRun.facts.map(fact => fact.field_id))
    expect(progress.mock.calls.map(([stage]) => stage)).toEqual(demoStages.map((_, index) => index))
    expect(result.fixture_id).toBe('demo:charger-daytona')
    expect(result.model_call_count).toBeNull()
    expect(result.total_tokens).toBeNull()
    expect(result.estimated_cost_usd).toBeNull()
    expect(result.facts.every(fact => fact.provenance.every(source => source.source_url === null))).toBe(true)
    expect(fetchSpy).not.toHaveBeenCalled()
    expect(JSON.stringify(await loadRecordedRun('miata-gt-auto', 'full_web'))).toBe(before)
    fetchSpy.mockRestore()
  })
})
