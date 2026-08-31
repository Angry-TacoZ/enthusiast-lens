import type { AnalysisRecord, FactResult, Provenance } from '../types'

const source = (publisher: string, sourceUrl: string, confidence: Provenance['confidence'] = 'high'): Provenance => ({
  source_url: sourceUrl,
  publisher,
  source_type: 'manufacturer_specification',
  configuration_match: 'exact_configuration',
  origin: 'researched',
  confidence,
  retrieved_at: null,
  notes: 'Saved from the PR #10 Core 24 contract fixture; no provider run was executed.',
  relationship: 'supports',
})

const fact = (fieldId: string, value: unknown, unit: string | null, options: Partial<FactResult> = {}): FactResult => ({
  field_id: fieldId,
  value,
  unit,
  state: 'known',
  confidence: 'high',
  provenance: [],
  configuration_dependency_notes: null,
  conflict_information: null,
  origin: 'researched',
  ...options,
})

const mazdaSpecs = source('Mazda North American Operations', 'https://www.mazdausa.com/vehicles/mx-5-miata/compare-vehicle-specs-and-trims')
const mazdaNews = source('Mazda North American Operations', 'https://news.mazdausa.com/2026-01-27-2026-Mazda-MX-5-Miata-Pricing-and-Packaging')
const mazdaManual = source('Mazda North American Operations', 'https://www.mazdausa.com/static/manuals/2025/mx-5/contents/65460300.html')

export const recordedRun: AnalysisRecord = {
  schema_version: 'hackathon-core-24-v1',
  system_version: 'hackathon-core-24-contract-fixture',
  fixture_id: '01_miata_gt_auto_ground_truth.json',
  vehicle_family_id: '01_miata',
  vehicle: {
    year: 2026, make: 'Mazda', model: 'MX-5 Miata', trim: 'Grand Touring', body_style: 'Soft-top roadster',
    transmission: '6-speed Sport automatic', drivetrain: 'RWD', market: 'US', vin: 'JM1NDAD70T0702556',
    listing_id: null, listing_url: null, packages: [], build_date_or_range: null, hardware_generation: null,
    notes: 'PR #10 Core 24 contract fixture: automatic soft-top, not RF or manual.',
  },
  run_mode: 'full_web',
  model: 'No provider execution — saved fixture',
  started_at: '2026-08-31T20:00:00Z',
  completed_at: '2026-08-31T20:00:00Z',
  status: 'succeeded',
  facts: [
    fact('audio.amplifier_power_w', null, 'W', { state: 'unknown', confidence: null, provenance: [mazdaSpecs], configuration_dependency_notes: 'The Bose system is documented, but exact amplifier output was unresolved in the frozen Core 24 contract.' }),
    fact('audio.subwoofer', true, null, { provenance: [mazdaSpecs] }),
    fact('brakes_wheels_and_tires.rotor_diameters_in', { front_diameter_in: 11, rear_diameter_in: 11 }, 'in', { provenance: [mazdaSpecs] }),
    fact('brakes_wheels_and_tires.default_tire', null, null, { state: 'unknown', confidence: null, provenance: [], configuration_dependency_notes: 'Exact OE tire brand and model were unresolved before the Core 24 freeze.' }),
    fact('brakes_wheels_and_tires.braking_70_to_0_mph_ft', null, 'ft', { state: 'unknown', confidence: null, provenance: [], configuration_dependency_notes: 'No configuration-matched instrumented braking result was defensible before the Core 24 freeze.' }),
    fact('driver_assistance_and_highway_automation.adaptive_cruise_control', true, null, { provenance: [mazdaSpecs, mazdaNews] }),
    fact('driver_assistance_and_highway_automation.acc_full_stop_and_go', false, null, { provenance: [mazdaManual] }),
    fact('driver_assistance_and_highway_automation.active_lane_centering', false, null, { provenance: [mazdaSpecs] }),
    fact('drivetrain_and_differentials.layout', 'RWD', null, { provenance: [mazdaSpecs] }),
    fact('drivetrain_and_differentials.limited_slip_differential', false, null, { provenance: [mazdaSpecs, mazdaNews], configuration_dependency_notes: 'The limited-slip differential is manual-only on Grand Touring; this fixture is the automatic.' }),
    fact('engine_and_measured_performance.displacement_l', 2, 'L', { provenance: [mazdaSpecs] }),
    fact('engine_and_measured_performance.aspiration', 'Naturally aspirated', null, { provenance: [mazdaSpecs] }),
    fact('engine_and_measured_performance.horsepower', 181, 'hp', { provenance: [mazdaSpecs, mazdaNews] }),
    fact('engine_and_measured_performance.torque_lb_ft', 151, 'lb-ft', { provenance: [mazdaSpecs, mazdaNews] }),
    fact('engine_and_measured_performance.curb_weight_lb', 2405, 'lb', { provenance: [mazdaSpecs] }),
    fact('engine_and_measured_performance.pounds_per_horsepower', 13.29, 'lb/hp', { origin: 'derived', confidence: null, provenance: [mazdaSpecs], configuration_dependency_notes: 'Deterministically calculated as curb_weight_lb / horsepower, rounded to two decimals.' }),
    fact('engine_and_measured_performance.zero_to_60_mph', null, 's', { state: 'unknown', confidence: null, provenance: [], configuration_dependency_notes: 'No configuration-matched instrumented 0–60 result was defensible before the Core 24 freeze.' }),
    fact('engine_and_measured_performance.skidpad_g', null, 'g', { state: 'unknown', confidence: null, provenance: [], configuration_dependency_notes: 'No configuration-matched instrumented skidpad result was defensible before the Core 24 freeze.' }),
    fact('energy_storage.capacity', { fuel_tank_gal: 11.9, battery_kwh: null }, null, { provenance: [mazdaSpecs] }),
    fact('transmission.type', 'Torque-converter automatic', null, { provenance: [mazdaSpecs, mazdaManual] }),
    fact('transmission.gear_count', 6, null, { provenance: [mazdaSpecs] }),
    fact('transmission.manual_shifting_from_selector', true, null, { provenance: [mazdaSpecs] }),
    fact('transmission.paddle_shifters', true, null, { provenance: [mazdaSpecs] }),
    fact('suspension_axles_and_chassis.suspension_layout', { front: 'double wishbone', rear: 'multilink' }, null, { provenance: [mazdaSpecs] }),
  ],
  warnings: [],
  configuration_notes: [
    'Automatic Grand Touring is not interchangeable with the manual: it excludes the manual-only limited-slip differential.',
    'This saved fixture represents PR #10’s Core 24 contract; it does not represent a completed Gemini or vPIC execution.',
  ],
  model_call_count: null,
  search_query_count: null,
  grounded_source_count: 3,
  total_tokens: null,
  estimated_cost_usd: null,
  latency_ms: null,
  retry_count: null,
  failures: [],
  trajectory_path: null,
}

export const vehicleOptions = [
  { id: 'miata-gt-auto', label: '2026 Mazda MX-5 Miata', detail: 'Grand Touring · Automatic · RWD · Core 24', availability: 'recorded' as const },
  { id: 'mini-acc-check', label: '2021 MINI Cooper S', detail: 'ACC claim verification · FWD', availability: 'input_only' as const },
  { id: 'model-y-hw4', label: '2023 Tesla Model Y', detail: 'Long Range AWD · HW4 / AI4', availability: 'input_only' as const },
]
