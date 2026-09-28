import { describe, expect, it, vi } from 'vitest'
import { simulateDemoRun, demoStages } from './simulatedDemoClient'
import { vehicleOptions } from '../data/vehicles'
import { recordedRun } from '../data/recordedRun'
import { loadRecordedRun } from './recordedClient'

describe('source-backed demo profiles', () => {
  it('provides all 24 canonical fields for each selectable vehicle without provider calls or benchmark mutation', async () => {
    const before = JSON.stringify(await loadRecordedRun('miata-gt-auto', 'full_web'))
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    const progress = vi.fn()
    const results = await Promise.all(vehicleOptions.map(vehicle => simulateDemoRun(vehicle, 'full_web', progress, 0)))

    for (const result of results) {
      expect(result.facts.map(fact => fact.field_id)).toEqual(recordedRun.facts.map(fact => fact.field_id))
      expect(new Set(result.facts.map(fact => fact.field_id)).size).toBe(24)
      expect(result.model_call_count).toBeNull()
      expect(result.search_query_count).toBeNull()
      expect(result.total_tokens).toBeNull()
      expect(result.estimated_cost_usd).toBeNull()
      expect(result.facts.filter(fact => fact.state === 'known').every(fact => fact.provenance.length > 0 && fact.provenance.every(source => source.source_url?.startsWith('https://')))).toBe(true)
      expect(result.facts.filter(fact => fact.state === 'unknown').every(fact => fact.value === null && fact.provenance.length === 0)).toBe(true)
    }
    expect(progress).toHaveBeenCalledTimes(vehicleOptions.length * demoStages.length)
    expect(fetchSpy).not.toHaveBeenCalled()
    expect(JSON.stringify(await loadRecordedRun('miata-gt-auto', 'full_web'))).toBe(before)
    fetchSpy.mockRestore()
  })

  it('uses configuration-specific powertrain values instead of generic samples', async () => {
    const byId = new Map(vehicleOptions.map(vehicle => [vehicle.id, vehicle]))
    const elantra = await simulateDemoRun(byId.get('elantra-n-line')!, 'full_web', vi.fn(), 0)
    const mustang = await simulateDemoRun(byId.get('mustang-ecoboost')!, 'hybrid', vi.fn(), 0)
    const charger = await simulateDemoRun(byId.get('charger-daytona')!, 'full_web', vi.fn(), 0)
    const tesla = await simulateDemoRun(byId.get('tesla-model-y')!, 'full_web', vi.fn(), 0)
    const wrx = await simulateDemoRun(byId.get('wrx-limited')!, 'hybrid', vi.fn(), 0)
    const fact = (result: typeof elantra, fieldId: string) => result.facts.find(item => item.field_id === fieldId)!

    expect(fact(elantra, 'engine_and_measured_performance.torque_lb_ft').value).toBe(195)
    expect(fact(elantra, 'engine_and_measured_performance.torque_lb_ft').value).not.toBe(220)
    expect(fact(mustang, 'engine_and_measured_performance.horsepower').value).toBe(330)
    expect(fact(mustang, 'engine_and_measured_performance.torque_lb_ft').value).toBe(350)
    expect(mustang.vehicle.packages).toContain('2.3L High Performance Package (67E)')
    expect(fact(charger, 'engine_and_measured_performance.horsepower').value).toBe(670)
    expect(fact(charger, 'engine_and_measured_performance.displacement_l').state).toBe('not_applicable')
    expect(fact(tesla, 'engine_and_measured_performance.displacement_l').state).toBe('not_applicable')
    expect(fact(tesla, 'transmission.gear_count').value).toBe(1)
    expect(fact(wrx, 'transmission.gear_count').state).toBe('unknown')
    expect(wrx.vehicle.transmission).toContain('CVT')
    expect(wrx.configuration_notes.join(' ')).toContain('not represented as an 8-gear mechanical transmission')
  })
})
