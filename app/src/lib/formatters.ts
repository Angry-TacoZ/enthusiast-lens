import type { FactResult } from '../types'

const labelOverrides: Record<string, string> = {
  acc: 'ACC',
  awd: 'AWD',
  dct: 'DCT',
  rpm: 'RPM',
  lsd: 'LSD',
  mph: 'MPH',
}

const fieldLabelOverrides: Record<string, string> = {
  'engine_and_measured_performance.power_to_weight_hp_per_us_ton': 'Power-to-weight',
  'brakes_wheels_and_tires.front_rotor_diameter_in': 'Front rotor diameter',
  'audio.amplifier_power_w': 'Amplifier output',
  'drivetrain_and_differentials.rear_limited_slip_differential':
    'Rear limited-slip differential',
  'configuration_dependencies.manual_vs_automatic_performance_hardware':
    'Manual vs. automatic hardware',
}

export function formatFieldLabel(fieldId: string): string {
  if (fieldLabelOverrides[fieldId]) return fieldLabelOverrides[fieldId]
  const leaf = fieldId.split('.').at(-1) ?? fieldId
  return leaf
    .split('_')
    .map((word) => labelOverrides[word] ?? `${word.charAt(0).toUpperCase()}${word.slice(1)}`)
    .join(' ')
    .replace('Zero To 60 MPH', '0–60 MPH')
}

export function formatFactValue(fact: FactResult): string {
  if (fact.state === 'unknown') return 'Unknown'
  if (fact.state === 'not_available') return 'Not available'
  if (fact.state === 'not_applicable') return 'Not applicable'
  if (fact.state === 'conflicted') return 'Conflicting evidence'
  if (typeof fact.value === 'boolean') return fact.value ? 'Yes' : 'No'
  if (Array.isArray(fact.value)) return fact.value.join(', ')
  if (fact.value === null || fact.value === undefined) return 'Unknown'
  return `${String(fact.value)}${fact.unit ? ` ${fact.unit}` : ''}`
}

export function formatDuration(milliseconds: number | null): string {
  if (milliseconds === null) return '—'
  if (milliseconds < 1_000) return `${milliseconds} ms`
  if (milliseconds < 60_000) return `${(milliseconds / 1_000).toFixed(1)} s`
  const minutes = Math.floor(milliseconds / 60_000)
  const seconds = Math.round((milliseconds % 60_000) / 1_000)
  return `${minutes}m ${seconds}s`
}

export function categoryFromFieldId(fieldId: string): string {
  return fieldId.split('.')[0] ?? 'other'
}
