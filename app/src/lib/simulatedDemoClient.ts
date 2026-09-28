import type { AnalysisRecord, FactResult, RunMode, VehicleOption } from '../types'

// Illustrative UI samples only. Never read/write evaluation artifacts or make requests.
export const demoStages = [
  'Configuration identified', 'Structured facts checked', 'Missing enthusiast facts identified',
  'Public-source research simulated', 'Evidence reconciled', 'Report prepared',
] as const

const samples: [string, unknown, string | null][] = [
  ['audio.amplifier_power_w', 300, 'W'], ['audio.subwoofer', true, null],
  ['brakes_wheels_and_tires.rotor_diameters_in', { front_diameter_in: 12, rear_diameter_in: 11 }, 'in'],
  ['brakes_wheels_and_tires.default_tire', 'Illustrative touring tire', null],
  ['brakes_wheels_and_tires.braking_70_to_0_mph_ft', null, 'ft'],
  ['driver_assistance_and_highway_automation.adaptive_cruise_control', true, null],
  ['driver_assistance_and_highway_automation.acc_full_stop_and_go', null, null],
  ['driver_assistance_and_highway_automation.active_lane_centering', false, null],
  ['drivetrain_and_differentials.layout', 'AWD', null],
  ['drivetrain_and_differentials.limited_slip_differential', null, null],
  ['engine_and_measured_performance.displacement_l', null, 'L'],
  ['engine_and_measured_performance.aspiration', null, null],
  ['engine_and_measured_performance.horsepower', 200, 'hp'],
  ['engine_and_measured_performance.torque_lb_ft', 220, 'lb-ft'],
  ['engine_and_measured_performance.curb_weight_lb', 3200, 'lb'],
  ['engine_and_measured_performance.pounds_per_horsepower', 16, 'lb/hp'],
  ['engine_and_measured_performance.zero_to_60_mph', null, 's'],
  ['engine_and_measured_performance.skidpad_g', null, 'g'],
  ['energy_storage.capacity', null, null], ['transmission.type', 'Automatic', null],
  ['transmission.gear_count', null, null], ['transmission.manual_shifting_from_selector', true, null],
  ['transmission.paddle_shifters', true, null],
  ['suspension_axles_and_chassis.suspension_layout', 'Illustrative independent suspension', null],
]

export async function simulateDemoRun(
  vehicle: VehicleOption, mode: RunMode, onProgress: (stage: number) => void,
  delayMs = 450,
): Promise<AnalysisRecord> {
  const started = Date.now()
  for (let stage = 0; stage < demoStages.length; stage++) {
    onProgress(stage)
    await new Promise(resolve => window.setTimeout(resolve, delayMs))
  }
  const facts: FactResult[] = samples.map(([field_id, value, unit]) => ({
    field_id, value, unit, state: value === null ? 'unknown' : 'known', confidence: null,
    origin: field_id.endsWith('pounds_per_horsepower') ? 'derived' : null,
    configuration_dependency_notes: 'Illustrative sample, not a specification for the selected vehicle.',
    conflict_information: null,
    provenance: value === null ? [] : [{
      publisher: 'Simulated demo evidence', source_url: null, source_type: 'demo_sample',
      configuration_match: null, origin: 'researched', confidence: null, retrieved_at: null,
      notes: 'Authored UI sample only. No public source was consulted and no model was invoked.', relationship: 'context',
    }],
  }))
  const [, year, name] = vehicle.label.match(/^(\d{4})(?:–\d{4})?\s+(.*)$/) ?? ['', '2020', vehicle.label]
  return {
    schema_version: 'simulated-demo-v1', system_version: 'simulated-demo-v1',
    fixture_id: `demo:${vehicle.id}`, vehicle_family_id: vehicle.id,
    vehicle: { year: Number(year), make: name.trim().split(' ')[0], model: name.trim().split(' ').slice(1).join(' '),
      trim: vehicle.detail, body_style: 'Demo configuration', transmission: 'Illustrative automatic',
      drivetrain: 'Illustrative AWD', market: 'Demo', vin: null, listing_id: null, listing_url: null,
      packages: [], build_date_or_range: null, hardware_generation: null, notes: 'Not an exact-VIN vehicle specification.' },
    run_mode: mode, model: 'No model invoked — local simulation',
    started_at: new Date(started).toISOString(), completed_at: new Date().toISOString(), status: 'succeeded', facts,
    warnings: ['Sample values are illustrative, not factual claims about this vehicle.'],
    configuration_notes: ['This result demonstrates the product workflow. It is not one of the preserved Core 24 model runs. Sample values do not describe the selected vehicle.'],
    model_call_count: null, search_query_count: null, grounded_source_count: null, total_tokens: null,
    estimated_cost_usd: null, latency_ms: Date.now() - started, retry_count: null, failures: [], trajectory_path: null,
  }
}
