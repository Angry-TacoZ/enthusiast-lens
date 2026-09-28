import type { AnalysisRecord, FactResult, Provenance, RunMode, VehicleOption } from '../types'

// Static, source-backed display samples only. This browser demo never reads evaluation answers,
// makes provider requests, or represents these reference facts as live research.
export const demoStages = [
  'Configuration identified', 'Structured facts checked', 'Missing enthusiast facts identified',
  'Public-source research simulated', 'Evidence reconciled', 'Report prepared',
] as const

type DemoSpec = { value: unknown; unit: string | null; source: string; note?: string; confidence?: Provenance['confidence'] }
type DemoProfile = {
  vehicle: AnalysisRecord['vehicle']
  facts: Partial<Record<string, DemoSpec>>
  notApplicable?: string[]
  notes: string[]
}

const sources: Record<string, Omit<Provenance, 'notes'>> = {
  mazda: { publisher: 'Mazda North American Operations', source_url: 'https://www.mazdausa.com/vehicles/mx-5-miata/compare-vehicle-specs-and-trims', source_type: 'manufacturer_specification', configuration_match: 'model_year_and_trim', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  mazdaNews: { publisher: 'Mazda North American Operations', source_url: 'https://news.mazdausa.com/2026-01-27-2026-Mazda-MX-5-Miata-Pricing-and-Packaging', source_type: 'manufacturer_specification', configuration_match: 'model_year_and_trim', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  mini: { publisher: 'BMW of North America / MINI USA', source_url: 'https://www.press.bmwgroup.com/usa/article/detail/T0297926EN_US/model-year-2020-mini-lineup-pricing-and-equipment-updates', source_type: 'manufacturer_specification', configuration_match: 'model_year_and_trim', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  miniSpecs: { publisher: 'BMW of North America / MINI USA', source_url: 'https://www.press.bmwgroup.com/usa/article/attachment/T0324990EN_US/471010', source_type: 'manufacturer_specification', configuration_match: 'Cooper_S_2_door_generation', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  miniEngine: { publisher: 'BMW of North America / MINI USA', source_url: 'https://www.press.bmwgroup.com/usa/article/detail/T0157784EN_US/introducing-the-new-mini-the-new-original?language=en_US', source_type: 'manufacturer_specification', configuration_match: 'engine_family', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  gr86: { publisher: 'Toyota USA Newsroom', source_url: 'https://pressroom.toyota.com/toyota-announces-pricing-on-all-new-2022-gr86/', source_type: 'manufacturer_specification', configuration_match: 'model_year_and_trim', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  mustang: { publisher: 'Ford Motor Company', source_url: 'https://media.ford.com/content/dam/fordmedia/North%20America/US/product/2020/mustang/2020-Mustang-Tech_Specs.pdf', source_type: 'manufacturer_specification', configuration_match: 'model_year_and_powertrain', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  mustangHpp: { publisher: 'Ford Motor Company', source_url: 'https://media.ford.com/content/fordmedia/fna/mx/es/news/2019/04/16/ford-desarrolla-el-mustang-2-3l-high-performance-package-2020.html', source_type: 'manufacturer_specification', configuration_match: 'model_year_package_and_powertrain', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  elantra: { publisher: 'Hyundai Motor America', source_url: 'https://www.hyundaiusa.com/us/en/vehicles/2025-elantra/n-line', source_type: 'manufacturer_specification', configuration_match: 'same_n_line_powertrain', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  elantra2024: { publisher: 'Hyundai Motor America', source_url: 'https://cdn.dealereprocess.org/cdn/brochures/hyundai/2024-elantra.pdf', source_type: 'manufacturer_brochure', configuration_match: 'model_year_and_trim', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  cadillac: { publisher: 'Cadillac', source_url: 'https://www.cadillac.com/content/dam/cadillac/na/us/english/index/downloads/vehiclebrochures/brochures/2018/on_star/2018%20Cadillac%20ATS%20Catalog_revMAY2018.pdf', source_type: 'manufacturer_specification', configuration_match: 'model_year_and_trim', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  jeep: { publisher: 'Jeep', source_url: 'https://www.jeep.com/2025/wrangler/faq.html', source_type: 'manufacturer_specification', configuration_match: 'model_year_and_powertrain', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  jeepTransmission: { publisher: 'Stellantis Media', source_url: 'https://www.media.stellantis.com/em-en/jeep/press/new-jeep-wrangler-4xe-the-best-of-4x4-goes-electric-to-go-anywhere', source_type: 'manufacturer_specification', configuration_match: '4xe_powertrain', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  dodge: { publisher: 'Dodge', source_url: 'https://www.dodge.com/am/en/next-gen-charger.html', source_type: 'manufacturer_specification', configuration_match: 'model_year_trim_and_powertrain', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  dodgeSticker: { publisher: 'Dodge / Stellantis', source_url: 'https://www.dodge.com/hostd/windowsticker/getWindowStickerPdf.do?vin=2C3CDBDK2SR559586', source_type: 'manufacturer_window_sticker', configuration_match: 'exact_vehicle', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  kia: { publisher: 'Kia America', source_url: 'https://www.kiamedia.com/us/en/media/specifications/20045/2022-kia-soul-specifications', source_type: 'manufacturer_specification', configuration_match: 'model_year_and_trim', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  kiaPress: { publisher: 'Kia America', source_url: 'https://www.kiamedia.com/us/en/models/soul/2022', source_type: 'manufacturer_specification', configuration_match: 'model_year_and_trim', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  tesla: { publisher: 'Tesla', source_url: 'https://www.tesla.com/modely', source_type: 'manufacturer_specification', configuration_match: 'drivetrain_configuration', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  teslaManual: { publisher: 'Tesla', source_url: 'https://www.tesla.com/ownersmanual/2020_2024_modely/en_us/GUID-E414862C-CFA1-4A0B-9548-BE21C32CAA58.html', source_type: 'manufacturer_owner_manual', configuration_match: 'model_year_range', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
  subaru: { publisher: 'Subaru of America', source_url: 'https://www.subaru.com/services/vehicles/pdf/trimComparison/2026/WRX?hideBuildMsrp=false', source_type: 'manufacturer_specification', configuration_match: 'model_year_and_trim', origin: 'researched', confidence: 'high', retrieved_at: null, relationship: 'supports' },
}

const profiles: Record<string, DemoProfile> = {
  'miata-gt-auto': {
    vehicle: { year: 2026, make: 'Mazda', model: 'MX-5 Miata', trim: 'Grand Touring', body_style: 'Soft-top roadster', transmission: '6-speed automatic', drivetrain: 'RWD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: [], build_date_or_range: null, hardware_generation: null, notes: 'Grand Touring automatic soft-top configuration.' },
    facts: {
      'drivetrain_and_differentials.layout': { value: 'RWD', unit: null, source: 'mazda' },
      'engine_and_measured_performance.displacement_l': { value: 2, unit: 'L', source: 'mazdaNews' },
      'engine_and_measured_performance.aspiration': { value: 'Naturally aspirated', unit: null, source: 'mazdaNews' },
      'engine_and_measured_performance.horsepower': { value: 181, unit: 'hp', source: 'mazdaNews' },
      'engine_and_measured_performance.torque_lb_ft': { value: 151, unit: 'lb-ft', source: 'mazdaNews' },
      'engine_and_measured_performance.curb_weight_lb': { value: 2405, unit: 'lb', source: 'mazda' },
      'engine_and_measured_performance.pounds_per_horsepower': { value: 13.29, unit: 'lb/hp', source: 'mazda', note: 'Calculated from the cited curb weight and horsepower; rounded to two decimals.' },
      'transmission.type': { value: '6-speed automatic', unit: null, source: 'mazdaNews' },
      'transmission.gear_count': { value: 6, unit: null, source: 'mazdaNews' },
      'transmission.paddle_shifters': { value: true, unit: null, source: 'mazdaNews' },
    },
    notes: ['Reference values describe the 2026 Grand Touring automatic soft-top, not the manual or RF configuration.'],
  },
  'mini-cooper-s': {
    vehicle: { year: 2020, make: 'MINI', model: 'Cooper S 2-Door', trim: 'Cooper S', body_style: '2-door hatchback', transmission: '7-speed STEPTRONIC Sport DCT', drivetrain: 'FWD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: [], build_date_or_range: '2020–2021 model years', hardware_generation: null, notes: 'The demo option represents a paired 2020/2021 ACC scenario, not one exact vehicle. Configuration-dependent assistance facts are left Unknown.' },
    facts: {
      'drivetrain_and_differentials.layout': { value: 'FWD', unit: null, source: 'miniSpecs' },
      'engine_and_measured_performance.displacement_l': { value: 2, unit: 'L', source: 'miniEngine' },
      'engine_and_measured_performance.aspiration': { value: 'Turbocharged', unit: null, source: 'miniEngine' },
      'engine_and_measured_performance.horsepower': { value: 189, unit: 'hp', source: 'miniEngine' },
      'transmission.type': { value: '7-speed dual-clutch automatic', unit: null, source: 'mini' },
      'transmission.gear_count': { value: 7, unit: null, source: 'mini' },
    },
    notes: ['This selector pairs two model years and two ACC configurations; the sample does not assert either vehicle’s ACC state.'],
  },
  'gr86-base': {
    vehicle: { year: 2022, make: 'Toyota', model: 'GR86', trim: 'Base', body_style: '2-door coupe', transmission: '6-speed automatic', drivetrain: 'RWD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: [], build_date_or_range: null, hardware_generation: null, notes: null },
    facts: {
      'drivetrain_and_differentials.layout': { value: 'RWD', unit: null, source: 'gr86' },
      'engine_and_measured_performance.displacement_l': { value: 2.4, unit: 'L', source: 'gr86' },
      'engine_and_measured_performance.aspiration': { value: 'Naturally aspirated', unit: null, source: 'gr86' },
      'engine_and_measured_performance.horsepower': { value: 228, unit: 'hp', source: 'gr86' },
      'engine_and_measured_performance.torque_lb_ft': { value: 184, unit: 'lb-ft', source: 'gr86' },
      'transmission.type': { value: '6-speed automatic', unit: null, source: 'gr86' },
      'transmission.gear_count': { value: 6, unit: null, source: 'gr86' },
    },
    notes: ['Engine output is shared across the 2022 GR86 grades; the cited source separately reports automatic-transmission performance.'],
  },
  'mustang-ecoboost': {
    vehicle: { year: 2020, make: 'Ford', model: 'Mustang', trim: 'EcoBoost Premium Fastback', body_style: 'Fastback', transmission: '10-speed SelectShift automatic', drivetrain: 'RWD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: ['2.3L High Performance Package (67E)', 'Ford Safe & Smart Package (77S)', 'EcoBoost Premium Plus Equipment Group 201A', 'B&O Sound System option 583'], build_date_or_range: null, hardware_generation: null, notes: 'The B&O option is separate from the Safe & Smart package.' },
    facts: {
      'drivetrain_and_differentials.layout': { value: 'RWD', unit: null, source: 'mustang' },
      'engine_and_measured_performance.displacement_l': { value: 2.3, unit: 'L', source: 'mustangHpp' },
      'engine_and_measured_performance.aspiration': { value: 'Turbocharged', unit: null, source: 'mustangHpp' },
      'engine_and_measured_performance.horsepower': { value: 330, unit: 'hp', source: 'mustangHpp' },
      'engine_and_measured_performance.torque_lb_ft': { value: 350, unit: 'lb-ft', source: 'mustangHpp' },
      'transmission.type': { value: '10-speed SelectShift automatic', unit: null, source: 'mustang' },
      'transmission.gear_count': { value: 10, unit: null, source: 'mustang' },
    },
    notes: ['Engine figures are for the 2.3L High Performance Package, not the standard EcoBoost calibration.'],
  },
  'elantra-n-line': {
    vehicle: { year: 2024, make: 'Hyundai', model: 'Elantra', trim: 'N Line', body_style: 'sedan', transmission: '7-speed dual-clutch transmission', drivetrain: 'FWD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: [], build_date_or_range: null, hardware_generation: null, notes: null },
    facts: {
      'drivetrain_and_differentials.layout': { value: 'FWD', unit: null, source: 'elantra2024' },
      'engine_and_measured_performance.displacement_l': { value: 1.6, unit: 'L', source: 'elantra2024' },
      'engine_and_measured_performance.aspiration': { value: 'Turbocharged', unit: null, source: 'elantra2024' },
      'engine_and_measured_performance.horsepower': { value: 201, unit: 'hp', source: 'elantra2024' },
      'engine_and_measured_performance.torque_lb_ft': { value: 195, unit: 'lb-ft', source: 'elantra2024', note: 'Not 220 lb-ft. Hyundai lists 195 lb-ft for the 2024 N Line 1.6T.' },
      'transmission.type': { value: '7-speed dual-clutch transmission', unit: null, source: 'elantra' },
      'transmission.gear_count': { value: 7, unit: null, source: 'elantra' },
    },
    notes: ['N Line values are distinct from the higher-output Elantra N. Hyundai’s U.S. specification page lists 195 lb-ft for the 1.6T N Line.'],
  },
  'cadillac-ats': {
    vehicle: { year: 2018, make: 'Cadillac', model: 'ATS', trim: 'Base / Standard', body_style: 'sedan', transmission: '6-speed manual', drivetrain: 'RWD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: [], build_date_or_range: null, hardware_generation: null, notes: '2.0L Turbo RWD configuration with optional 6-speed manual.' },
    facts: {
      'drivetrain_and_differentials.layout': { value: 'RWD', unit: null, source: 'cadillac' },
      'engine_and_measured_performance.displacement_l': { value: 2, unit: 'L', source: 'cadillac' },
      'engine_and_measured_performance.aspiration': { value: 'Turbocharged', unit: null, source: 'cadillac' },
      'engine_and_measured_performance.horsepower': { value: 272, unit: 'hp', source: 'cadillac' },
      'engine_and_measured_performance.torque_lb_ft': { value: 295, unit: 'lb-ft', source: 'cadillac' },
      'transmission.type': { value: '6-speed manual', unit: null, source: 'cadillac' },
      'transmission.gear_count': { value: 6, unit: null, source: 'cadillac' },
    },
    notes: ['Cadillac lists the 6-speed manual as an available transmission specifically for the 2.0L Turbo RWD ATS.'],
  },
  'wrangler-4xe': {
    vehicle: { year: 2025, make: 'Jeep', model: 'Wrangler 4xe', trim: 'Rubicon', body_style: '4-door SUV', transmission: '8-speed automatic', drivetrain: '4WD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: [], build_date_or_range: null, hardware_generation: null, notes: 'Plug-in hybrid Rubicon configuration.' },
    facts: {
      'drivetrain_and_differentials.layout': { value: '4WD', unit: null, source: 'jeep' },
      'engine_and_measured_performance.displacement_l': { value: 2, unit: 'L', source: 'jeep' },
      'engine_and_measured_performance.aspiration': { value: 'Turbocharged plug-in hybrid', unit: null, source: 'jeep' },
      'engine_and_measured_performance.horsepower': { value: 375, unit: 'hp', source: 'jeep' },
      'engine_and_measured_performance.torque_lb_ft': { value: 470, unit: 'lb-ft', source: 'jeep' },
      'transmission.type': { value: '8-speed automatic', unit: null, source: 'jeepTransmission' },
      'transmission.gear_count': { value: 8, unit: null, source: 'jeepTransmission' },
    },
    notes: ['The cited 375 hp and 470 lb-ft figures are the combined Wrangler 4xe system ratings.'],
  },
  'charger-daytona': {
    vehicle: { year: 2025, make: 'Dodge', model: 'Charger Daytona', trim: 'Scat Pack', body_style: '2-door liftback', transmission: 'single-speed electric drive', drivetrain: 'AWD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: ['Track Package'], build_date_or_range: null, hardware_generation: null, notes: 'The represented 2025 Scat Pack configuration includes the Track Package.' },
    facts: {
      'drivetrain_and_differentials.layout': { value: 'AWD', unit: null, source: 'dodge' },
      'engine_and_measured_performance.horsepower': { value: 670, unit: 'hp', source: 'dodge' },
      'engine_and_measured_performance.torque_lb_ft': { value: 627, unit: 'lb-ft', source: 'dodge', confidence: 'medium', note: 'Dodge describes this torque figure as an estimate.' },
      'transmission.type': { value: 'single-speed electric drive', unit: null, source: 'dodgeSticker' },
      'transmission.gear_count': { value: 1, unit: null, source: 'dodgeSticker' },
    },
    notApplicable: ['engine_and_measured_performance.displacement_l', 'engine_and_measured_performance.aspiration'],
    notes: ['The 670 hp figure is combined output from two motors. Torque is Dodge’s published estimate; battery capacity and curb weight are not supplied here.'],
  },
  'kia-soul-turbo': {
    vehicle: { year: 2022, make: 'Kia', model: 'Soul', trim: 'Turbo', body_style: '5-door hatchback/crossover', transmission: '7-speed dual-clutch transmission', drivetrain: 'FWD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: [], build_date_or_range: null, hardware_generation: null, notes: null },
    facts: {
      'drivetrain_and_differentials.layout': { value: 'FWD', unit: null, source: 'kia' },
      'engine_and_measured_performance.displacement_l': { value: 1.6, unit: 'L', source: 'kia' },
      'engine_and_measured_performance.aspiration': { value: 'Turbocharged', unit: null, source: 'kia' },
      'engine_and_measured_performance.horsepower': { value: 201, unit: 'hp', source: 'kiaPress' },
      'engine_and_measured_performance.torque_lb_ft': { value: 195, unit: 'lb-ft', source: 'kiaPress' },
      'transmission.type': { value: '7-speed dual-clutch transmission', unit: null, source: 'kia' },
      'transmission.gear_count': { value: 7, unit: null, source: 'kia' },
    },
    notes: ['The 2022 Turbo trim pairs the 1.6L turbo engine with Kia’s 7-speed DCT.'],
  },
  'tesla-model-y': {
    vehicle: { year: 2023, make: 'Tesla', model: 'Model Y', trim: 'Long Range AWD', body_style: '5-door crossover', transmission: 'single-speed electric drive', drivetrain: 'AWD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: ['Hardware 4 / AI4'], build_date_or_range: '2023 HW4 / AI4 production', hardware_generation: 'HW4 / AI4', notes: 'Software entitlement is not inferred from the hardware generation.' },
    facts: {
      'drivetrain_and_differentials.layout': { value: 'AWD', unit: null, source: 'tesla' },
      'transmission.type': { value: 'single-speed electric drive', unit: null, source: 'teslaManual' },
      'transmission.gear_count': { value: 1, unit: null, source: 'teslaManual' },
    },
    notApplicable: ['engine_and_measured_performance.displacement_l', 'engine_and_measured_performance.aspiration'],
    notes: ['Tesla does not publish a configuration-specific horsepower or torque rating on the cited public specification page; those fields remain Unknown.'],
  },
  'wrx-limited': {
    vehicle: { year: 2026, make: 'Subaru', model: 'WRX', trim: 'Limited', body_style: 'sedan', transmission: 'Subaru Performance Transmission (CVT)', drivetrain: 'AWD', market: 'US', vin: null, listing_id: null, listing_url: null, packages: [], build_date_or_range: null, hardware_generation: null, notes: 'Limited trim with optional Subaru Performance Transmission.' },
    facts: {
      'drivetrain_and_differentials.layout': { value: 'AWD', unit: null, source: 'subaru' },
      'engine_and_measured_performance.displacement_l': { value: 2.4, unit: 'L', source: 'subaru' },
      'engine_and_measured_performance.aspiration': { value: 'Turbocharged', unit: null, source: 'subaru' },
      'engine_and_measured_performance.horsepower': { value: 271, unit: 'hp', source: 'subaru' },
      'engine_and_measured_performance.torque_lb_ft': { value: 258, unit: 'lb-ft', source: 'subaru' },
      'transmission.type': { value: 'Subaru Performance Transmission (CVT)', unit: null, source: 'subaru' },
    },
    notes: ['The CVT includes an 8-speed manual mode, but it is not represented as an 8-gear mechanical transmission.'],
  },
}

const fieldIds = [
  'audio.amplifier_power_w', 'audio.subwoofer', 'brakes_wheels_and_tires.rotor_diameters_in',
  'brakes_wheels_and_tires.default_tire', 'brakes_wheels_and_tires.braking_70_to_0_mph_ft',
  'driver_assistance_and_highway_automation.adaptive_cruise_control',
  'driver_assistance_and_highway_automation.acc_full_stop_and_go',
  'driver_assistance_and_highway_automation.active_lane_centering',
  'drivetrain_and_differentials.layout', 'drivetrain_and_differentials.limited_slip_differential',
  'engine_and_measured_performance.displacement_l', 'engine_and_measured_performance.aspiration',
  'engine_and_measured_performance.horsepower', 'engine_and_measured_performance.torque_lb_ft',
  'engine_and_measured_performance.curb_weight_lb', 'engine_and_measured_performance.pounds_per_horsepower',
  'engine_and_measured_performance.zero_to_60_mph', 'engine_and_measured_performance.skidpad_g',
  'energy_storage.capacity', 'transmission.type', 'transmission.gear_count',
  'transmission.manual_shifting_from_selector', 'transmission.paddle_shifters',
  'suspension_axles_and_chassis.suspension_layout',
] as const

function toFact(profile: DemoProfile, fieldId: typeof fieldIds[number]): FactResult {
  const spec = profile.facts[fieldId]
  const notApplicable = !spec && profile.notApplicable?.includes(fieldId)
  const source = spec ? sources[spec.source] : undefined
  const provenance = spec && source ? [{ ...source, notes: spec.note ?? 'Manufacturer-published specification used as a static demo reference.' }] : []
  return {
    field_id: fieldId,
    value: spec?.value ?? null,
    unit: spec?.unit ?? null,
    state: spec ? 'known' : notApplicable ? 'not_applicable' : 'unknown',
    confidence: spec?.confidence ?? (spec ? 'high' : null),
    origin: spec ? (fieldId.endsWith('pounds_per_horsepower') ? 'derived' : 'researched') : null,
    provenance,
    configuration_dependency_notes: spec?.note ?? (notApplicable ? 'Not applicable: this is a battery-electric vehicle with no combustion engine.' : spec ? null : 'Not verified for this exact demo configuration; left Unknown rather than guessed.'),
    conflict_information: null,
  }
}

export async function simulateDemoRun(
  vehicle: VehicleOption, mode: RunMode, onProgress: (stage: number) => void,
  delayMs = 450,
): Promise<AnalysisRecord> {
  const started = Date.now()
  for (let stage = 0; stage < demoStages.length; stage++) {
    onProgress(stage)
    await new Promise(resolve => window.setTimeout(resolve, delayMs))
  }
  const profile = profiles[vehicle.id]
  if (!profile) throw new Error(`No demo data profile exists for vehicle selection: ${vehicle.id}`)
  const facts = fieldIds.map(fieldId => toFact(profile, fieldId))
  return {
    schema_version: 'simulated-demo-v1', system_version: 'simulated-demo-v1',
    fixture_id: `demo:${vehicle.id}`, vehicle_family_id: vehicle.id,
    vehicle: profile.vehicle,
    run_mode: mode, model: 'No model invoked — local simulation',
    started_at: new Date(started).toISOString(), completed_at: new Date().toISOString(), status: 'succeeded', facts,
    warnings: ['Static, source-backed demo sample only. No live provider analysis was performed.'],
    configuration_notes: [...profile.notes, 'Unverified facts remain Unknown; these demo references are not a recorded benchmark run.'],
    model_call_count: null, search_query_count: null, grounded_source_count: null, total_tokens: null,
    estimated_cost_usd: null, latency_ms: Date.now() - started, retry_count: null, failures: [], trajectory_path: null,
  }
}
