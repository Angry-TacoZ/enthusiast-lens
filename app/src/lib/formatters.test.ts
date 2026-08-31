import { describe, expect, it } from 'vitest'
import { formatDuration, formatFactValue, formatFieldLabel } from './formatters'
import type { FactResult } from '../types'

const baseFact: FactResult = {
  field_id: 'engine_and_measured_performance.horsepower',
  value: 181,
  unit: 'hp',
  state: 'known',
  confidence: 'high',
  provenance: [],
  configuration_dependency_notes: null,
  conflict_information: null,
  origin: 'researched',
}

describe('formatters', () => {
  it('turns canonical field ids into compact labels', () => {
    expect(formatFieldLabel('engine_and_measured_performance.zero_to_60_mph')).toBe('0–60 MPH')
  })

  it('preserves explicit unknown semantics instead of rendering a null value', () => {
    expect(formatFactValue({ ...baseFact, value: null, unit: null, state: 'unknown' })).toBe('Unknown')
  })

  it('formats booleans, units, and long durations for the report', () => {
    expect(formatFactValue(baseFact)).toBe('181 hp')
    expect(formatFactValue({ ...baseFact, value: false, unit: null })).toBe('No')
    expect(formatDuration(151_813)).toBe('2m 32s')
  })
})
