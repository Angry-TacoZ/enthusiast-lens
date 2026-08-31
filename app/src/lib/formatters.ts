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
  'brakes_wheels_and_tires.rotor_diameters_in': 'Rotor diameters',
  'brakes_wheels_and_tires.braking_70_to_0_mph_ft': '70–0 mph braking',
  'audio.amplifier_power_w': 'Amplifier output',
  'driver_assistance_and_highway_automation.acc_full_stop_and_go': 'ACC stop & go',
  'driver_assistance_and_highway_automation.active_lane_centering': 'Active lane centering',
  'drivetrain_and_differentials.limited_slip_differential': 'Limited-slip differential',
  'engine_and_measured_performance.displacement_l': 'Displacement',
  'engine_and_measured_performance.torque_lb_ft': 'Torque',
  'engine_and_measured_performance.curb_weight_lb': 'Curb weight',
  'engine_and_measured_performance.pounds_per_horsepower': 'Pounds per horsepower',
  'engine_and_measured_performance.zero_to_60_mph': '0–60 mph',
  'engine_and_measured_performance.skidpad_g': 'Skidpad',
  'transmission.manual_shifting_from_selector': 'Manual shift from selector',
  'suspension_axles_and_chassis.suspension_layout': 'Suspension layout',
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
  if (typeof fact.value === 'object') {
    const value = fact.value as Record<string, unknown>
    if (fact.field_id === 'brakes_wheels_and_tires.rotor_diameters_in') {
      return `F ${value.front_diameter_in ?? '—'} / R ${value.rear_diameter_in ?? '—'} in`
    }
    if (fact.field_id === 'energy_storage.capacity') {
      return value.fuel_tank_gal !== null && value.fuel_tank_gal !== undefined
        ? `${value.fuel_tank_gal} gal tank`
        : `${value.battery_kwh ?? '—'} kWh battery`
    }
    if (fact.field_id === 'suspension_axles_and_chassis.suspension_layout') {
      return `F ${value.front ?? '—'} / R ${value.rear ?? '—'}`
    }
    if (fact.field_id === 'brakes_wheels_and_tires.default_tire') {
      return `${value.brand_model ?? '—'} · F ${value.front_size ?? '—'} / R ${value.rear_size ?? '—'}`
    }
    return JSON.stringify(fact.value)
  }
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
