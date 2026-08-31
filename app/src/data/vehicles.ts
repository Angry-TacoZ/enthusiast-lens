import type { VehicleOption } from '../types'

/** The browser-visible family allowlist. The server owns the fixture mapping. */
export const vehicleOptions: VehicleOption[] = [
  { id: 'miata-gt-auto', label: '2026 Mazda MX-5 Miata', detail: 'Grand Touring · Automatic · RWD · Core 24', availability: 'available' },
  { id: 'mini-cooper-s', label: '2020–2021 MINI Cooper S 2-Door', detail: 'Cooper S · ACC scenario pair · Core 24', availability: 'available' },
  { id: 'gr86-base', label: '2022 Toyota GR86', detail: 'Base · Core 24', availability: 'available' },
  { id: 'mustang-ecoboost', label: '2020 Ford Mustang', detail: 'EcoBoost Premium · Core 24', availability: 'available' },
  { id: 'elantra-n-line', label: '2024 Hyundai Elantra', detail: 'N Line · Core 24', availability: 'available' },
  { id: 'cadillac-ats', label: '2018 Cadillac ATS', detail: 'Base · Core 24', availability: 'available' },
  { id: 'wrangler-4xe', label: '2025 Jeep Wrangler 4xe', detail: 'Rubicon · Core 24', availability: 'available' },
  { id: 'charger-daytona', label: '2025 Dodge Charger Daytona', detail: 'Scat Pack · Core 24', availability: 'available' },
  { id: 'kia-soul-turbo', label: '2022 Kia Soul', detail: 'Turbo · Core 24', availability: 'available' },
  { id: 'tesla-model-y', label: '2023 Tesla Model Y', detail: 'Long Range AWD · Core 24', availability: 'available' },
  { id: 'wrx-limited', label: '2026 Subaru WRX', detail: 'Limited · Core 24', availability: 'available' },
]
