import type { AnalysisRecord, FactResult, Provenance } from '../types'

const source = (
  publisher: string,
  sourceUrl: string,
  confidence: Provenance['confidence'] = 'high',
): Provenance => ({
  source_url: sourceUrl,
  publisher,
  source_type: 'reputable_automotive_publication',
  configuration_match: 'same_trim',
  origin: 'researched',
  confidence,
  retrieved_at: null,
  notes: 'Preserved from the tracked Full-Web evaluation artifact.',
  relationship: 'supports',
})

const fact = (
  fieldId: string,
  value: unknown,
  unit: string | null,
  options: Partial<FactResult> = {},
): FactResult => ({
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

const mazdaSource = source(
  'Mazda USA',
  'https://www.mazdausa.com/vehicles/mx-5-miata',
)

export const recordedRun: AnalysisRecord = {
  schema_version: '1.0',
  system_version: 'full-web-baseline-v4',
  fixture_id: '01_miata_gt_auto_ground_truth.json',
  vehicle_family_id: '01_miata',
  vehicle: {
    year: 2026,
    make: 'Mazda',
    model: 'MX-5 Miata',
    trim: 'Grand Touring',
    body_style: 'Soft-top roadster',
    transmission: '6-speed Sport automatic',
    drivetrain: 'RWD',
    market: 'US',
    vin: 'JM1NDAD70T0702556',
    listing_id: 'T0702556A',
    listing_url:
      'https://www.claycooley.com/vehicle/JM1NDAD70T0702556/Used--2026--Mazda--MX--5_Miata--Irving--TX/',
    packages: [],
    build_date_or_range: null,
    hardware_generation: null,
    notes:
      'Public dealer listing advertises the Grand Touring convertible with automatic transmission and RWD.',
  },
  run_mode: 'full_web',
  model: 'gemini-3.6-flash',
  started_at: '2026-08-30T20:32:53.047375Z',
  completed_at: '2026-08-30T20:35:24.881109Z',
  status: 'succeeded',
  facts: [
    fact('engine_and_measured_performance.horsepower', 181, 'hp', {
      provenance: [mazdaSource],
    }),
    fact('engine_and_measured_performance.torque', 151, 'lb-ft', {
      provenance: [mazdaSource],
    }),
    fact('engine_and_measured_performance.curb_weight', 2405, 'lbs', {
      provenance: [source('Kelley Blue Book', 'https://www.kbb.com/mazda/mx-5-miata/')],
      configuration_dependency_notes:
        'Curb weight applies to the automatic-transmission soft-top configuration.',
    }),
    fact('engine_and_measured_performance.zero_to_60_mph', '6.1–6.5', 's', {
      confidence: 'medium',
      provenance: [source('0–60 Specs', 'https://www.0-60specs.com/mazda/mx-5-miata-0-60-times/', 'medium')],
      configuration_dependency_notes:
        'Instrumented range is configuration-matched to the automatic soft-top.',
    }),
    fact('engine_and_measured_performance.power_to_weight_hp_per_us_ton', 150.52, 'hp/US ton', {
      confidence: null,
      origin: 'derived',
      configuration_dependency_notes:
        'Deterministically calculated from canonical horsepower and curb weight.',
    }),
    fact('transmission.mechanism', 'Torque-converter automatic', null, {
      provenance: [mazdaSource],
    }),
    fact('transmission.gear_count', 6, null, { provenance: [mazdaSource] }),
    fact('transmission.paddle_shifters', true, null, { provenance: [mazdaSource] }),
    fact('drivetrain_and_differentials.layout', 'Front-mid engine / RWD', null, {
      provenance: [mazdaSource],
    }),
    fact('drivetrain_and_differentials.rear_limited_slip_differential', false, null, {
      provenance: [mazdaSource],
      configuration_dependency_notes:
        'The limited-slip differential is restricted to manual-transmission configurations.',
    }),
    fact(
      'suspension_axles_and_chassis.front_suspension',
      'Independent double-wishbone',
      null,
      { provenance: [mazdaSource] },
    ),
    fact(
      'suspension_axles_and_chassis.rear_suspension',
      'Independent 5-link multi-link',
      null,
      { provenance: [mazdaSource] },
    ),
    fact('suspension_axles_and_chassis.bilstein_dampers', false, null, {
      provenance: [mazdaSource],
      configuration_dependency_notes:
        'Bilstein dampers are restricted to manual-transmission configurations.',
    }),
    fact('brakes_wheels_and_tires.front_rotor_diameter_in', 11, 'in', {
      provenance: [source('Cars.com', 'https://www.cars.com/research/mazda-mx_5_miata/')],
    }),
    fact('audio.system_brand', 'Bose', null, { provenance: [mazdaSource] }),
    fact('audio.speaker_count', 9, null, { provenance: [mazdaSource] }),
    fact('audio.amplifier_power_w', null, null, {
      state: 'unknown',
      confidence: null,
      provenance: [mazdaSource],
      configuration_dependency_notes:
        'The amplifier is documented, but rated wattage was not established.',
    }),
    fact('driver_assistance_and_highway_automation.adaptive_cruise_control', true, null, {
      provenance: [mazdaSource],
    }),
    fact('driver_assistance_and_highway_automation.lane_centering', false, null, {
      provenance: [mazdaSource],
    }),
    fact(
      'configuration_dependencies.manual_vs_automatic_performance_hardware',
      'Automatic deletes the manual model’s LSD, Bilstein dampers, front shock-tower brace, DSC-Track mode, and induction sound enhancer.',
      null,
      { provenance: [mazdaSource] },
    ),
  ],
  warnings: [],
  configuration_notes: [
    'Automatic-transmission models omit the rear limited-slip differential, Bilstein dampers, and DSC-Track mode found on manual configurations.',
    'The selected configuration is the soft-top Grand Touring with rear-wheel drive.',
  ],
  model_call_count: 8,
  search_query_count: 22,
  grounded_source_count: 60,
  total_tokens: 61971,
  estimated_cost_usd: 0.13619625,
  latency_ms: 151813,
  retry_count: 0,
  failures: [],
  trajectory_path:
    'artifacts/evals/full_web/01_miata_gt_auto_ground_truth.json/trajectory/research-410076db-4a93-4538-8b89-3cabcf04d20d.json',
}

export const vehicleOptions = [
  {
    id: 'miata-gt-auto',
    label: '2026 Mazda MX-5 Miata',
    detail: 'Grand Touring · Automatic · RWD',
    availability: 'recorded' as const,
  },
  {
    id: 'mini-acc-check',
    label: '2021 MINI Cooper S',
    detail: 'ACC claim verification · FWD',
    availability: 'input_only' as const,
  },
  {
    id: 'model-y-hw4',
    label: '2023 Tesla Model Y',
    detail: 'Long Range AWD · HW4 / AI4',
    availability: 'input_only' as const,
  },
]
