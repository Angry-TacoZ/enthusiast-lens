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
    expect(formatFieldLabel('engine_and_measured_performance.zero_to_60_mph')).toBe('0–60 mph')
  })

  it('preserves explicit unknown semantics instead of rendering a null value', () => {
    expect(formatFactValue({ ...baseFact, value: null, unit: null, state: 'unknown' })).toBe('Unknown')
  })

  it('formats booleans, units, and long durations for the report', () => {
    expect(formatFactValue(baseFact)).toBe('181 hp')
    expect(formatFactValue({ ...baseFact, value: false, unit: null })).toBe('No')
    expect(formatDuration(151_813)).toBe('2m 32s')
  })

  it('keeps Core 24 structured values readable without flattening their meaning', () => {
    expect(formatFactValue({ ...baseFact, field_id: 'brakes_wheels_and_tires.rotor_diameters_in', value: { front_diameter_in: 11, rear_diameter_in: 11 }, unit: 'in' })).toBe('F 11 / R 11 in')
    expect(formatFactValue({ ...baseFact, field_id: 'suspension_axles_and_chassis.suspension_layout', value: { front: 'double wishbone', rear: 'multilink' }, unit: null })).toBe('F double wishbone / R multilink')
  })
})
