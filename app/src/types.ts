export type RunMode = 'full_web' | 'hybrid'
export type RunStatus = 'started' | 'succeeded' | 'partial' | 'failed'
export type FactState =
  | 'known'
  | 'unknown'
  | 'conflicted'
  | 'not_available'
  | 'not_applicable'
export type Origin = 'structured' | 'researched' | 'derived'
export type Confidence = 'high' | 'medium' | 'low'

export interface VehicleContext {
  year: number
  make: string
  model: string
  trim: string | null
  body_style: string | null
  transmission: string | null
  drivetrain: string | null
  market: string | null
  vin: string | null
  listing_id: string | null
  listing_url: string | null
  packages: string[]
  build_date_or_range: string | null
  hardware_generation: string | null
  notes: string | null
}

export interface Provenance {
  source_url: string | null
  publisher: string | null
  source_type: string
  configuration_match: string | null
  origin: Origin
  confidence: Confidence | null
  retrieved_at: string | null
  notes: string | null
  relationship: 'supports' | 'conflicts' | 'context'
}

export interface FactResult {
  field_id: string
  value: unknown
  unit: string | null
  state: FactState
  confidence: Confidence | null
  provenance: Provenance[]
  configuration_dependency_notes: string | null
  conflict_information: string | null
  origin: Origin | null
}

export interface AnalysisRecord {
  schema_version: string
  system_version: string
  fixture_id: string
  vehicle_family_id: string
  vehicle: VehicleContext
  run_mode: RunMode
  model: string
  started_at: string
  completed_at: string | null
  status: RunStatus
  facts: FactResult[]
  warnings: string[]
  configuration_notes: string[]
  model_call_count: number | null
  search_query_count: number | null
  grounded_source_count: number | null
  total_tokens: number | null
  estimated_cost_usd: number | null
  latency_ms: number | null
  retry_count: number | null
  failures: string[]
  trajectory_path: string | null
}

export interface VehicleOption {
  id: string
  label: string
  detail: string
  availability: 'available'
}
